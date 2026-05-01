from pydantic import BaseModel


class EvaluationRequest(BaseModel):
    session_id: str
    message_id: str
    score: int = 0
    feedback: str | None = None


class EvaluationResponse(BaseModel):
    id: str
    session_id: str
    message_id: str
    score: int
    feedback: str | None
