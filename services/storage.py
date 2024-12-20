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
    name: str
    create_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)

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

    def create_issue(self, name: str) -> Issue:
        name = Issue(name=name)
        with Session(self.engine) as session:
            session.add(name)
            session.commit()
            session.refresh(name)
            return name
    
    def get_issue(self, id: uuid.UUID) -> Issue:
        with Session(self.engine) as session:
            return session.get(Issue, id)
    
    def list_issue(self) -> list[Issue]:
        with Session(self.engine) as session:
            return session.exec(statement=select(Issue), execution_options={"prebuffer_rows": True})

    def create_resp(self, issue_id:str, user_query: str, asst_resp: str, reasoning: str, referenced_docs: list[str]):
        resp = Response(user_query=user_query, asst_resp=asst_resp,
                        reasoning=reasoning, referenced_docs=referenced_docs,
                        issue_id=issue_id)
        with Session(self.engine) as session:
            session.add(resp)
            session.commit()
            session.refresh(resp)
            return resp
    
    def get_resp(self, id: uuid.UUID) -> Response:
        with Session(self.engine) as session:
            return session.get(Response, id)
    
    def list_resp(self, issue_id: uuid.UUID) -> list[Response]:
        with Session(self.engine) as session:
            statement = select(Response).where(Response.issue_id == issue_id).order_by(Response.create_at)
            return session.exec(statement=statement, execution_options={"prebuffer_rows": True})

    def evaluate(self, issue_id: uuid.UUID, resp_id: uuid.UUID, score: int, feedback: str = None):
        evaluation = Evaluation(score=score, feedback=feedback, issue_id=issue_id, resp_id=resp_id)
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
    
    def list_runbook_set(self) -> list[RunbookSet]:
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
