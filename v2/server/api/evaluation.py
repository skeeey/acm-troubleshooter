import uuid

from fastapi import APIRouter, Depends, HTTPException

from v2.server.schemas.evaluation import EvaluationRequest, EvaluationResponse
from v2.server.services.db import DatabaseService

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


def get_db_service():
    raise NotImplementedError("must be overridden via app.dependency_overrides")


@router.put("/")
async def evaluate(
    req: EvaluationRequest,
    db_svc: DatabaseService = Depends(get_db_service),
) -> EvaluationResponse:
    session = await db_svc.get_session(uuid.UUID(req.session_id))
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")

    msg = await db_svc.get_message(uuid.UUID(req.message_id))
    if msg is None:
        raise HTTPException(status_code=404, detail="message not found")

    evaluation = await db_svc.create_evaluation(
        session_id=session.id,
        message_id=msg.id,
        score=req.score,
        feedback=req.feedback,
    )

    return EvaluationResponse(
        id=str(evaluation.id),
        session_id=str(evaluation.session_id),
        message_id=str(evaluation.message_id),
        score=evaluation.score,
        feedback=evaluation.feedback,
    )
