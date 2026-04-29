import enum
import uuid
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    create_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)

class ChatSession(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    create_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    user_id: uuid.UUID = Field(nullable=False, foreign_key="user.id", ondelete="CASCADE")

class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"

class Message(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    role: MessageRole
    content: str
    reasoning: str | None = None
    token_count: int | None = None
    create_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    session_id: uuid.UUID = Field(nullable=False, foreign_key="chatsession.id", ondelete="CASCADE")

class MessageReference(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    doc_link: str
    message_id: uuid.UUID = Field(nullable=False, foreign_key="message.id", ondelete="CASCADE")

class Evaluation(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    score: int
    feedback: str | None = None
    create_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    session_id: uuid.UUID = Field(nullable=False, foreign_key="chatsession.id", ondelete="CASCADE")
    message_id: uuid.UUID = Field(nullable=False, foreign_key="message.id", ondelete="CASCADE")

class DocumentState(str, enum.Enum):
    IDLE = "idle"
    INDEXING = "indexing"
    INDEXED = "indexed"
    FAILED = "failed"

class Document(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    repo: str
    branch: str
    desc: str
    latest_commit: str | None = None
    state: DocumentState = DocumentState.IDLE
    error: str | None = None
    create_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    update_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
    )
