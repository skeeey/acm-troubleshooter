import json
import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI

from v2.server.api.chat import router, get_db_service, get_rag_service
from v2.server.models.db import User
from v2.server.services.db import DatabaseService
from v2.server.services.rag import RAGResult, RAGService

DB_URL = "sqlite+aiosqlite://"


class MockRAGService(RAGService):
    async def run(self, query, history, doc_sources) -> RAGResult:
        return RAGResult(
            content=f"Answer to: {query}",
            references=["https://example.com/doc1.md"],
        )

    async def stream(self, query, history, doc_sources) -> AsyncGenerator[RAGResult, None]:
        for word in ["Answer ", "to: ", query]:
            yield RAGResult(content=word)
        yield RAGResult(content="", references=["https://example.com/doc1.md"])


@pytest_asyncio.fixture
async def test_app():
    db_svc = DatabaseService(db_url=DB_URL)
    await db_svc.init_db()

    app = FastAPI()
    app.include_router(router, prefix="/api")
    app.dependency_overrides[get_db_service] = lambda: db_svc
    app.dependency_overrides[get_rag_service] = lambda: MockRAGService()

    return app, db_svc


@pytest_asyncio.fixture
async def client(test_app):
    app, _ = test_app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def seeded_app(test_app):
    """Seed with a user so chat endpoints work."""
    app, db_svc = test_app
    from sqlalchemy.ext.asyncio import AsyncSession
    async with AsyncSession(db_svc.engine) as session:
        user = User(name="testuser")
        session.add(user)
        await session.commit()
        await session.refresh(user)

    return app, db_svc, user


@pytest_asyncio.fixture
async def seeded_client(seeded_app):
    app, _, _ = seeded_app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_chat_empty_query(seeded_client):
    resp = await seeded_client.post("/api/chat/", json={
        "user_id": str(uuid.uuid4()),
        "query": "",
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_chat_creates_session(seeded_client, seeded_app):
    _, _, user = seeded_app
    resp = await seeded_client.post("/api/chat/", json={
        "user_id": str(user.id),
        "query": "How to install ACM?",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["content"] == "Answer to: How to install ACM?"
    assert data["session_id"]
    assert data["message_id"]
    assert data["references"] == ["https://example.com/doc1.md"]


@pytest.mark.asyncio
async def test_chat_session_continuity(seeded_client, seeded_app):
    _, db_svc, user = seeded_app

    resp1 = await seeded_client.post("/api/chat/", json={
        "user_id": str(user.id),
        "query": "How to install ACM?",
    })
    session_id = resp1.json()["session_id"]

    resp2 = await seeded_client.post("/api/chat/", json={
        "user_id": str(user.id),
        "session_id": session_id,
        "query": "What about upgrades?",
    })
    assert resp2.status_code == 200
    assert resp2.json()["session_id"] == session_id

    messages = await db_svc.list_messages(uuid.UUID(session_id))
    assert len(messages) == 4  # user1, assistant1, user2, assistant2


@pytest.mark.asyncio
async def test_chat_session_not_found(seeded_client, seeded_app):
    _, _, user = seeded_app
    resp = await seeded_client.post("/api/chat/", json={
        "user_id": str(user.id),
        "session_id": str(uuid.uuid4()),
        "query": "test",
    })
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_chat_stream(seeded_client, seeded_app):
    _, _, user = seeded_app
    resp = await seeded_client.post("/api/chat/stream", json={
        "user_id": str(user.id),
        "query": "How to install ACM?",
    })
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")

    events = []
    for line in resp.text.strip().split("\n\n"):
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))

    assert events[0]["event"] == "start"
    assert events[0]["session_id"] is not None

    deltas = [e for e in events if e["event"] == "delta"]
    assert len(deltas) > 0
    full_content = "".join(e["content"] for e in deltas)
    assert "How to install ACM?" in full_content

    ref_events = [e for e in events if e["event"] == "references"]
    assert len(ref_events) == 1
    assert ref_events[0]["references"] == ["https://example.com/doc1.md"]

    assert events[-1]["event"] == "done"
    assert events[-1]["message_id"] is not None


@pytest.mark.asyncio
async def test_chat_stream_empty_query(seeded_client):
    resp = await seeded_client.post("/api/chat/stream", json={
        "user_id": str(uuid.uuid4()),
        "query": "  ",
    })
    assert resp.status_code == 422
