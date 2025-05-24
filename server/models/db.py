import uuid
from pydantic import BaseModel
from datetime import datetime, timezone
from sqlmodel import Column, JSON, SQLModel, Field

class User(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    create_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)

# one issue means one chat session
# TODO rename the table name from issue to chat_session
class Issue(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    create_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    user_id: uuid.UUID = Field(nullable=False, foreign_key="user.id", ondelete="CASCADE")

class Response(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_query: str | None = None
    asst_resp: str | None = None
    reasoning: str | None = None
    referenced_docs: list[str] | None = Field(default=None, sa_column=Column(JSON))
    create_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    update_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
    )
    issue_id: uuid.UUID = Field(nullable=False, foreign_key="issue.id", ondelete="CASCADE")

class Evaluation(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    score: int
    feedback: str | None = None
    create_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    issue_id: uuid.UUID = Field(nullable=False, foreign_key="issue.id", ondelete="CASCADE")
    resp_id: uuid.UUID = Field(nullable=False, foreign_key="response.id", ondelete="CASCADE")

class Document(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    repo: str
    branch: str
    desc: str
    create_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)

class DocumentCommit(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    commit: str
    state: str
    create_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    document_id: uuid.UUID = Field(nullable=False, foreign_key="document.id", ondelete="CASCADE")

class IssueRecordView(BaseModel):
    issue_id: uuid.UUID
    issue_name: str
    issue_create_at: datetime
    response_id: uuid.UUID | None
    response_create_at: datetime | None
    evaluation_score: int | None
    evaluation_feedback: str | None

class DocumentView(BaseModel):
    source: str
    desc: str
