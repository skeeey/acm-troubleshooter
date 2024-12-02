# coding: utf-8

import uuid
from datetime import datetime, timezone
from sqlmodel import Column, JSON, SQLModel, Session, Field, create_engine, select

class Context(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    retrieval_config: str | None = Field(default=None, sa_column=Column(JSON))
    llm_config: str | None = Field(default=None, sa_column=Column(JSON))
    issue_id: uuid.UUID = Field(nullable=False, unique=True, foreign_key="issue.id", ondelete="CASCADE")

class Issue(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    issue: str
    create_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)

class Diagnosis(SQLModel, table=True):
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
    step_id: uuid.UUID = Field(nullable=False, foreign_key="diagnosis.id", ondelete="CASCADE")

class RunbookSet(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    repo: str
    branch: str
    create_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)

class RunbookSetVersion(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    version: str
    state: str
    create_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    runbook_set_id: uuid.UUID = Field(nullable=False, foreign_key="runbookset.id", ondelete="CASCADE")
    
class StorageService:
    def __init__(self, db_url: str):
        engine = create_engine(url=db_url, echo=False)
        SQLModel.metadata.create_all(engine)
        self.engine = engine

    def create_context(self, issue_id: uuid.UUID, retrieval_cfg: str, llm_cfg: str):
        ctx = Context(retrieval_config=retrieval_cfg, llm_config=llm_cfg, issue_id=issue_id)
        with Session(self.engine) as session:
            session.add(ctx)
            session.commit()
    
    def find_context(self, issue_id: uuid.UUID) -> Context:
        with Session(self.engine) as session:
            statement = select(Context).where(Context.issue_id == issue_id)
            results = session.exec(statement)
            return results.first()

    def create_issue(self, issue: str) -> Issue:
        issue = Issue(issue=issue)
        with Session(self.engine) as session:
            session.add(issue)
            session.commit()
            session.refresh(issue)
            return issue
    
    def get_issue(self, id: uuid.UUID) -> Issue:
        with Session(self.engine) as session:
            return session.get(Issue, id)
    
    def create_diagnosis_step(self, issue_id: uuid.UUID) -> Diagnosis:
        step = Diagnosis(issue_id=issue_id)
        with Session(self.engine) as session:
            session.add(step)
            session.commit()
            session.refresh(step)
            return step

    def update_diagnosis_step(self, updated: Diagnosis):
        with Session(self.engine) as session:
            session.add(updated)
            session.commit()
            session.refresh(updated)
    
    def get_diagnosis_step(self, id: uuid.UUID) -> Diagnosis:
        with Session(self.engine) as session:
            return session.get(Diagnosis, id)
    
    def evaluate_issue(self, issue_id: uuid.UUID, step_id: uuid.UUID, score: int, feedback: str = None):
        evaluation = Evaluation(score=score, feedback=feedback, issue_id=issue_id, step_id=step_id)
        with Session(self.engine) as session:
            session.add(evaluation)
            session.commit()
    
    def create_runbook_set(self, repo: str, branch: str) -> RunbookSet:
        runbook_set = RunbookSet(repo=repo, branch=branch)
        with Session(self.engine) as session:
            session.add(runbook_set)
            session.commit()
            session.refresh(runbook_set)
            return runbook_set
        
    def delete_runbook_set(self, runbook_set: RunbookSet):
        with Session(self.engine) as session:
            session.delete(runbook_set)
            session.commit()
    
    def get_runbook_set(self, id: uuid.UUID) -> RunbookSet:
        with Session(self.engine) as session:
            return session.get(RunbookSet, id)
    
    def list_runbook_set(self) -> RunbookSet:
        with Session(self.engine) as session:
            return session.exec(statement=select(RunbookSet), execution_options={"prebuffer_rows": True})
    
    def find_runbook_set(self, repo: str, branch: str) -> RunbookSet:
         with Session(self.engine) as session:
            statement = select(RunbookSet).where(RunbookSet.repo == repo, RunbookSet.branch == branch)
            results = session.exec(statement)
            return results.first()

    def add_runbook_set_version(self, runbook_set_id: uuid.UUID, version: str) -> RunbookSetVersion:
        rsv = RunbookSetVersion(version=version, state="indexing", runbook_set_id=runbook_set_id)
        with Session(self.engine) as session:
            session.add(rsv)
            session.commit()
            session.refresh(rsv)
            return rsv
    
    def update_runbook_set_version(self, rsv: RunbookSetVersion):
        with Session(self.engine) as session:
            session.add(rsv)
            session.commit()
    
    def find_runbook_set_version(self, version: str) -> RunbookSetVersion:
         with Session(self.engine) as session:
            statement = select(RunbookSetVersion).where(RunbookSetVersion.version == version)
            results = session.exec(statement)
            return results.first()
    
    def list_runbook_set_versions(self, rs_id: uuid.UUID) -> list[RunbookSetVersion]:
         with Session(self.engine) as session:
            statement = select(RunbookSetVersion).where(RunbookSetVersion.runbook_set_id == rs_id).order_by(RunbookSetVersion.create_at)
            results = session.exec(statement=statement, execution_options={"prebuffer_rows": True})
            return results
