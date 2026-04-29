import asyncio
import uuid
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI

from v2.server.api.documents import router, get_db_service, get_doc_dir, get_vector_service
from v2.server.models.db import DocumentState
from v2.server.services.db import DatabaseService

DB_URL = "sqlite+aiosqlite://"


@pytest_asyncio.fixture
async def test_app(tmp_path):
    db_svc = DatabaseService(db_url=DB_URL)
    await db_svc.init_db()
    doc_dir = str(tmp_path / "docs")

    import os
    os.makedirs(doc_dir, exist_ok=True)

    mock_vector_svc = MagicMock()
    mock_vector_svc.list_file_hashes.return_value = {}
    mock_vector_svc.index_docs.return_value = None
    mock_vector_svc.delete_docs_by_source.return_value = None
    mock_vector_svc.delete_docs_by_file.return_value = None

    app = FastAPI()
    app.include_router(router, prefix="/api")
    app.dependency_overrides[get_db_service] = lambda: db_svc
    app.dependency_overrides[get_doc_dir] = lambda: doc_dir
    app.dependency_overrides[get_vector_service] = lambda: mock_vector_svc

    return app, db_svc


@pytest_asyncio.fixture
async def client(test_app):
    app, _ = test_app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_list_documents_empty(client):
    resp = await client.get("/api/documents/")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_create_document(client, origin_repo):
    resp = await client.post("/api/documents/", json={
        "repo": str(origin_repo),
        "branch": "main",
        "desc": "test docs",
    })
    assert resp.status_code == 202
    data = resp.json()
    assert data["repo"] == str(origin_repo)
    assert data["branch"] == "main"
    assert data["desc"] == "test docs"
    assert data["state"] == "indexing"
    assert data["latest_commit"] is not None
    assert "Location" in resp.headers


@pytest.mark.asyncio
async def test_create_document_duplicate(client, origin_repo):
    await client.post("/api/documents/", json={
        "repo": str(origin_repo),
        "branch": "main",
        "desc": "first",
    })
    resp = await client.post("/api/documents/", json={
        "repo": str(origin_repo),
        "branch": "main",
        "desc": "duplicate",
    })
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_get_document(client, origin_repo):
    create_resp = await client.post("/api/documents/", json={
        "repo": str(origin_repo),
        "branch": "main",
        "desc": "test",
    })
    doc_id = create_resp.json()["id"]

    resp = await client.get(f"/api/documents/{doc_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == doc_id


@pytest.mark.asyncio
async def test_get_document_not_found(client):
    resp = await client.get("/api/documents/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_document(client, origin_repo):
    create_resp = await client.post("/api/documents/", json={
        "repo": str(origin_repo),
        "branch": "main",
        "desc": "test",
    })
    doc_id = create_resp.json()["id"]

    resp = await client.delete(f"/api/documents/{doc_id}")
    assert resp.status_code == 204

    resp = await client.get(f"/api/documents/{doc_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_document_no_new_commit(client, test_app, origin_repo):
    _, db_svc = test_app
    create_resp = await client.post("/api/documents/", json={
        "repo": str(origin_repo),
        "branch": "main",
        "desc": "test",
    })
    doc_id = create_resp.json()["id"]
    original_commit = create_resp.json()["latest_commit"]

    await asyncio.sleep(0)

    doc = await db_svc.get_document(uuid.UUID(doc_id))
    doc.state = DocumentState.INDEXED
    await db_svc.update_document(doc)

    resp = await client.put(f"/api/documents/{doc_id}")
    assert resp.status_code == 200
    assert resp.json()["latest_commit"] == original_commit


@pytest.mark.asyncio
async def test_update_document_new_commit(client, test_app, origin_repo):
    from git import Repo as GitRepo

    _, db_svc = test_app
    create_resp = await client.post("/api/documents/", json={
        "repo": str(origin_repo),
        "branch": "main",
        "desc": "test",
    })
    doc_id = create_resp.json()["id"]
    original_commit = create_resp.json()["latest_commit"]

    await asyncio.sleep(0)

    doc = await db_svc.get_document(uuid.UUID(doc_id))
    doc.state = DocumentState.INDEXED
    await db_svc.update_document(doc)

    origin = GitRepo(origin_repo)
    new_file = origin_repo / "new.md"
    new_file.write_text("# New")
    origin.index.add(["new.md"])
    origin.index.commit("add new file")

    resp = await client.put(f"/api/documents/{doc_id}")
    assert resp.status_code == 202
    assert resp.json()["latest_commit"] != original_commit
    assert resp.json()["state"] == "indexing"
    assert "Location" in resp.headers
