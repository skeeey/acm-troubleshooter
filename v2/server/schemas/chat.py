from pydantic import BaseModel


class ChatRequest(BaseModel):
    session_id: str | None = None
    user_id: str
    query: str


class ChatResponse(BaseModel):
    session_id: str
    message_id: str
    content: str
    references: list[str]


class StreamEvent(BaseModel):
    event: str
    session_id: str | None = None
    message_id: str | None = None
    content: str | None = None
    references: list[str] | None = None
