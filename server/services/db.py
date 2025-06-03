# coding: utf-8

# pylint: disable=missing-class-docstring

"""
The service to store the chat records
"""

import logging
import uuid
from sqlmodel import SQLModel, Session, create_engine, select, text, desc as order_desc
from server.models.db import User, Issue, Response, Evaluation, Document, DocumentCommit, IssueRecordView, DocumentView
from server.tools.common import to_doc_source
from collections import defaultdict
from server.tools.git import parse_repo

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self, db_url: str):
        engine = create_engine(url=db_url, echo=False)
        SQLModel.metadata.create_all(engine)
        self.engine = engine
        logger.info("Database service is initialized")

    def create_user(self, name: str) -> User:
        user = User(name=name)
        with Session(self.engine) as session:
            session.add(user)
            session.commit()
            session.refresh(user)
            return user

    def find_user(self, name: str) -> User:
        with Session(self.engine) as session:
            statement = select(User).where(User.name == name)
            results = session.exec(statement)
            return results.first()

    def create_issue(self, user_id: uuid.UUID, name: str) -> Issue:
        name = Issue(name=name, user_id=user_id)
        with Session(self.engine) as session:
            session.add(name)
            session.commit()
            session.refresh(name)
            return name

    def get_issue(self, uid: uuid.UUID) -> Issue:
        with Session(self.engine) as session:
            return session.get(Issue, uid)

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

    def get_resp(self, uid: uuid.UUID) -> Response:
        with Session(self.engine) as session:
            return session.get(Response, uid)

    def list_resp(self, issue_id: uuid.UUID) -> list[Response]:
        with Session(self.engine) as session:
            statement = select(Response).where(Response.issue_id == issue_id).order_by(Response.create_at)
            return session.exec(statement=statement, execution_options={"prebuffer_rows": True})

    def evaluate(self, issue_id: uuid.UUID, resp_id: uuid.UUID, score: int, feedback: str = None):
        evaluation = Evaluation(score=score, feedback=feedback, issue_id=issue_id, resp_id=resp_id)
        with Session(self.engine) as session:
            session.add(evaluation)
            session.commit()

    def get_issues_records(self) -> list[IssueRecordView]:
        with Session(self.engine) as session:
            query = text("""
                SELECT issue.id AS issue_id, issue.name AS issue_name, issue.create_at AS issue_create_at,
                   response.id AS response_id, response.create_at AS response_create_at,
                   evaluation.score AS evaluation_score, evaluation.feedback AS evaluation_feedback
                FROM issue
                LEFT JOIN response ON issue.id = response.issue_id
                LEFT JOIN evaluation ON response.id = evaluation.resp_id;
            """)

            result = session.exec(query)

            issue_records = []
            for row in result:
                issue_records.append(IssueRecordView(
                    issue_id=row.issue_id,
                    issue_name=row.issue_name,
                    issue_create_at=row.issue_create_at,
                    response_id=row.response_id,
                    response_create_at=row.response_create_at,
                    evaluation_score=row.evaluation_score,
                    evaluation_feedback=row.evaluation_feedback,
                ))
            return issue_records

    def create_document(self, repo: str, branch: str, desc: str) -> Document:
        doc = Document(repo=repo, branch=branch, desc=desc)
        with Session(self.engine) as session:
            session.add(doc)
            session.commit()
            session.refresh(doc)
            return doc

    def delete_document(self, doc: Document):
        with Session(self.engine) as session:
            session.delete(doc)
            session.commit()

    def get_document(self, uid: uuid.UUID) -> Document:
        with Session(self.engine) as session:
            return session.get(Document, uid)

    def list_documents(self) -> list[Document]:
        with Session(self.engine) as session:
            return session.exec(statement=select(Document), execution_options={"prebuffer_rows": True})

    def find_document(self, repo: str, branch: str) -> Document:
        with Session(self.engine) as session:
            statement = select(Document).where(Document.repo == repo, Document.branch == branch)
            results = session.exec(statement)
            return results.first()

    def add_document_commit(self, doc_id: uuid.UUID, commit: str) -> DocumentCommit:
        doc_commit = DocumentCommit(commit=commit, state="indexing", document_id=doc_id)
        with Session(self.engine) as session:
            session.add(doc_commit)
            session.commit()
            session.refresh(doc_commit)
            return doc_commit

    def update_document_commit(self, doc_commit: DocumentCommit):
        with Session(self.engine) as session:
            session.add(doc_commit)
            session.commit()

    def find_document_commit(self, commit: str) -> DocumentCommit:
        with Session(self.engine) as session:
            statement = select(DocumentCommit).where(DocumentCommit.commit == commit)
            results = session.exec(statement)
            return results.first()

    def list_document_commits(self, doc_id: uuid.UUID) -> list[DocumentCommit]:
        with Session(self.engine) as session:
            statement = select(DocumentCommit).\
                where(DocumentCommit.document_id == doc_id).\
                order_by(DocumentCommit.create_at)
            results = session.exec(statement=statement, execution_options={"prebuffer_rows": True})
            return results

    def list_document_views(self, doc_state: str = None, only_latest: bool = False) -> list[DocumentView]:
        with Session(self.engine) as session:
            stmt = (
                select(Document.id, Document.repo, Document.branch, Document.desc, DocumentCommit.commit, DocumentCommit.state)
                .join(DocumentCommit, Document.id == DocumentCommit.document_id)
            )
            if doc_state is not None:
                stmt = stmt.where(DocumentCommit.state == doc_state)
            stmt = stmt.order_by(Document.repo, Document.branch, order_desc(DocumentCommit.create_at))

            results = session.exec(stmt).all()

            grouped = defaultdict(list)
            final_list = []

            for id, repo, branch, desc, commit, state in results:
                grouped[(repo, branch)].append({
                    "id": str(id),
                    "source": to_doc_source(repo, branch, commit),
                    "latest": False,
                    "state": state,
                    "desc": desc,
                })

            for key in grouped:
                commits = grouped[key]
                if commits:
                    commits[0]["latest"] = True
                if only_latest:
                    final_list.extend([commits[0]])
                    continue
                final_list.extend(commits)

            return [DocumentView(**item) for item in final_list]
