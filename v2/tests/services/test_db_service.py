import uuid

import pytest

from v2.server.models.db import DocumentState


@pytest.mark.asyncio
async def test_create_document(db_svc):
    doc = await db_svc.create_document(repo="https://github.com/org/repo", branch="main", desc="test")
    assert doc.id is not None
    assert doc.repo == "https://github.com/org/repo"
    assert doc.branch == "main"
    assert doc.desc == "test"
    assert doc.state == DocumentState.INDEXING
    assert doc.latest_commit is None


@pytest.mark.asyncio
async def test_get_document(db_svc):
    doc = await db_svc.create_document(repo="https://github.com/org/repo", branch="main", desc="test")
    fetched = await db_svc.get_document(doc.id)
    assert fetched is not None
    assert fetched.id == doc.id
    assert fetched.repo == doc.repo


@pytest.mark.asyncio
async def test_get_document_not_found(db_svc):
    result = await db_svc.get_document(uuid.uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_find_document(db_svc):
    await db_svc.create_document(repo="https://github.com/org/repo", branch="release-2.0", desc="test")
    found = await db_svc.find_document(repo="https://github.com/org/repo", branch="release-2.0")
    assert found is not None
    assert found.branch == "release-2.0"


@pytest.mark.asyncio
async def test_find_document_not_found(db_svc):
    result = await db_svc.find_document(repo="https://github.com/org/nonexistent", branch="main")
    assert result is None


@pytest.mark.asyncio
async def test_list_documents(db_svc):
    await db_svc.create_document(repo="https://github.com/org/repo1", branch="main", desc="first")
    await db_svc.create_document(repo="https://github.com/org/repo2", branch="main", desc="second")
    docs = await db_svc.list_documents()
    assert len(docs) == 2


@pytest.mark.asyncio
async def test_update_document(db_svc):
    doc = await db_svc.create_document(repo="https://github.com/org/repo", branch="main", desc="test")
    doc.state = DocumentState.INDEXED
    doc.latest_commit = "abc1234"
    updated = await db_svc.update_document(doc)
    assert updated.state == DocumentState.INDEXED
    assert updated.latest_commit == "abc1234"


@pytest.mark.asyncio
async def test_delete_document(db_svc):
    doc = await db_svc.create_document(repo="https://github.com/org/repo", branch="main", desc="test")
    await db_svc.delete_document(doc)
    result = await db_svc.get_document(doc.id)
    assert result is None
