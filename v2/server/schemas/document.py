from pydantic import BaseModel


class CreateDocumentRequest(BaseModel):
    repo: str
    branch: str = "main"
    desc: str


class DocumentResponse(BaseModel):
    id: str
    repo: str
    branch: str
    desc: str
    latest_commit: str | None
    state: str
    error: str | None
