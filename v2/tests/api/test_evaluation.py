import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI

from v2.server.api.evaluation import router, get_db_service
from v2.server.models.db import MessageRole, User
from v2.server.services.db import DatabaseService

DB_URL = "sqlite+aiosqlite://"


@pytest_asyncio.fixture
async def test_app():
    db_svc = DatabaseService(db_url=DB_URL)
    await db_svc.init_db()

    app = FastAPI()
    app.include_router(router, prefix="/api")
    app.dependency_overrides[get_db_service] = lambda: db_svc

    return app, db_svc


@pytest_asyncio.fixture
async def seeded_app(test_app):
    app, db_svc = test_app
    from sqlalchemy.ext.asyncio import AsyncSession
    async with AsyncSession(db_svc.engine) as session:
        user = User(name="testuser")
        session.add(user)
        await session.commit()
        await session.refresh(user)

    chat_session = await db_svc.create_session(user_id=user.id, name="test session")
    msg = await db_svc.create_message(
        session_id=chat_session.id,
        role=MessageRole.ASSISTANT,
        content="test answer",
    )
    return app, db_svc, chat_session, msg


@pytest_asyncio.fixture
async def client(seeded_app):
    app, _, _, _ = seeded_app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_evaluate(client, seeded_app):
    _, _, chat_session, msg = seeded_app
    resp = await client.put("/api/evaluation/", json={
        "session_id": str(chat_session.id),
        "message_id": str(msg.id),
        "score": 8,
        "feedback": "helpful answer",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["score"] == 8
    assert data["feedback"] == "helpful answer"
    assert data["session_id"] == str(chat_session.id)
    assert data["message_id"] == str(msg.id)


@pytest.mark.asyncio
async def test_evaluate_without_feedback(client, seeded_app):
    _, _, chat_session, msg = seeded_app
    resp = await client.put("/api/evaluation/", json={
        "session_id": str(chat_session.id),
        "message_id": str(msg.id),
        "score": 5,
    })
    assert resp.status_code == 200
    assert resp.json()["feedback"] is None


@pytest.mark.asyncio
async def test_evaluate_session_not_found(client, seeded_app):
    _, _, _, msg = seeded_app
    resp = await client.put("/api/evaluation/", json={
        "session_id": str(uuid.uuid4()),
        "message_id": str(msg.id),
        "score": 5,
    })
    assert resp.status_code == 404
    assert "session" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_evaluate_message_not_found(client, seeded_app):
    _, _, chat_session, _ = seeded_app
    resp = await client.put("/api/evaluation/", json={
        "session_id": str(chat_session.id),
        "message_id": str(uuid.uuid4()),
        "score": 5,
    })
    assert resp.status_code == 404
    assert "message" in resp.json()["detail"]
