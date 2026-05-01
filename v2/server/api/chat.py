import json
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from v2.server.models.db import MessageRole
from v2.server.schemas.chat import ChatRequest, ChatResponse, StreamEvent
from v2.server.services.db import DatabaseService
from v2.server.services.rag import RAGService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


def get_db_service():
    raise NotImplementedError("must be overridden via app.dependency_overrides")


def get_rag_service():
    raise NotImplementedError("must be overridden via app.dependency_overrides")


async def _get_or_create_session(db_svc: DatabaseService, req: ChatRequest):
    if req.session_id:
        session = await db_svc.get_session(uuid.UUID(req.session_id))
        if session is None:
            raise HTTPException(status_code=404, detail="session not found")
        return session

    return await db_svc.create_session(
        user_id=uuid.UUID(req.user_id),
        name=req.query[:100],
    )


async def _load_history(db_svc: DatabaseService, session_id: uuid.UUID) -> list[dict]:
    messages = await db_svc.list_messages(session_id)
    return [{"role": msg.role.value, "content": msg.content} for msg in messages]


@router.post("/")
async def chat(
    req: ChatRequest,
    db_svc: DatabaseService = Depends(get_db_service),
    rag_svc: RAGService = Depends(get_rag_service),
) -> ChatResponse:
    if not req.query or not req.query.strip():
        raise HTTPException(status_code=422, detail="query is required")

    doc_sources = await db_svc.list_indexed_doc_sources()
    session = await _get_or_create_session(db_svc, req)
    history = await _load_history(db_svc, session.id)

    await db_svc.create_message(
        session_id=session.id,
        role=MessageRole.USER,
        content=req.query,
    )

    try:
        result = await rag_svc.run(
            query=req.query,
            history=history,
            doc_sources=doc_sources,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"failed to get response from rag: {e}",
        ) from e

    assistant_msg = await db_svc.create_message(
        session_id=session.id,
        role=MessageRole.ASSISTANT,
        content=result.content,
    )

    if result.references:
        await db_svc.create_message_references(
            message_id=assistant_msg.id,
            doc_links=result.references,
        )

    return ChatResponse(
        session_id=str(session.id),
        message_id=str(assistant_msg.id),
        content=result.content,
        references=result.references,
    )


@router.post("/stream")
async def chat_stream(
    req: ChatRequest,
    db_svc: DatabaseService = Depends(get_db_service),
    rag_svc: RAGService = Depends(get_rag_service),
):
    if not req.query or not req.query.strip():
        raise HTTPException(status_code=422, detail="query is required")

    doc_sources = await db_svc.list_indexed_doc_sources()
    session = await _get_or_create_session(db_svc, req)
    history = await _load_history(db_svc, session.id)

    await db_svc.create_message(
        session_id=session.id,
        role=MessageRole.USER,
        content=req.query,
    )

    async def event_generator():
        full_content = ""
        references = []

        yield _sse(StreamEvent(
            event="start",
            session_id=str(session.id),
        ))

        try:
            async for chunk in rag_svc.stream(
                query=req.query,
                history=history,
                doc_sources=doc_sources,
            ):
                if chunk.content:
                    full_content += chunk.content
                    yield _sse(StreamEvent(event="delta", content=chunk.content))
                if chunk.references:
                    references = chunk.references
        except Exception as e:
            logger.exception("streaming error")
            yield _sse(StreamEvent(event="error", content=str(e)))
            return

        assistant_msg = await db_svc.create_message(
            session_id=session.id,
            role=MessageRole.ASSISTANT,
            content=full_content,
        )

        if references:
            await db_svc.create_message_references(
                message_id=assistant_msg.id,
                doc_links=references,
            )
            yield _sse(StreamEvent(event="references", references=references))

        yield _sse(StreamEvent(
            event="done",
            session_id=str(session.id),
            message_id=str(assistant_msg.id),
        ))

    return StreamingResponse(event_generator(), media_type="text/event-stream")


def _sse(event: StreamEvent) -> str:
    return f"data: {event.model_dump_json()}\n\n"
