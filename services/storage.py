# coding: utf-8

import uuid
from datetime import datetime, timezone
from sqlmodel import create_engine, Column, Field, JSON, SQLModel, Session

class Issue(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    issue: str
    lm_url: str | None = None
    doc_kinds: list[str] | None = Field(default=None, sa_column=Column(JSON))
    doc_versions: list[str] | None = Field(default=None, sa_column=Column(JSON))
    create_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)

class DiagnosisStep(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    plan: str | None = None
    reasoning: str | None = None
    user_suggestion: str | None = None
    referenced_docs: list[str] | None = Field(default=None, sa_column=Column(JSON))
    results: str | None = None
    hub_commands: list[str] | None = Field(default=None, sa_column=Column(JSON))
    spoke_commands: list[str] | None = Field(default=None, sa_column=Column(JSON))
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
    step_id: uuid.UUID = Field(nullable=False, foreign_key="diagnosisstep.id", ondelete="CASCADE")
    
class StorageService:
    def __init__(self, db_url: str):
        engine = create_engine(url=db_url, echo=False)
        SQLModel.metadata.create_all(engine)
        self.engine = engine

    def create_issue(self, issue: str, lm_url: str, doc_kinds: list[str], doc_versions: list[str]) -> Issue:
        issue = Issue(issue=issue, lm_url=lm_url, doc_kinds=doc_kinds, doc_versions=doc_versions)
        with Session(self.engine) as session:
            session.add(issue)
            session.commit()
            session.refresh(issue)
            return issue
    
    def get_issue(self, id: uuid.UUID) -> Issue:
        with Session(self.engine) as session:
            return session.get(Issue, id)
    
    def create_diagnosis_step(self, issue_id: uuid.UUID) -> DiagnosisStep:
        step = DiagnosisStep(issue_id=issue_id)
        with Session(self.engine) as session:
            session.add(step)
            session.commit()
            session.refresh(step)
            return step

    def update_diagnosis_step(self, updated: DiagnosisStep):
        with Session(self.engine) as session:
            session.add(updated)
            session.commit()
            session.refresh(updated)
    
    def get_diagnosis_step(self, id: uuid.UUID) -> DiagnosisStep:
        with Session(self.engine) as session:
            return session.get(DiagnosisStep, id)
    
    def evaluate_issue(self, issue_id: uuid.UUID, step_id: uuid.UUID, score: int, feedback: str = None):
        evaluation = Evaluation(score=score, feedback=feedback, issue_id=issue_id, step_id=step_id)
        with Session(self.engine) as session:
            session.add(evaluation)
            session.commit()
