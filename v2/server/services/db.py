import uuid

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import SQLModel, select

from v2.server.models.db import (
    ChatSession,
    Document,
    DocumentState,
    Evaluation,
    Message,
    MessageReference,
    MessageRole,
)


class DatabaseService:
    def __init__(self, db_url: str):
        self.engine = create_async_engine(db_url)

    async def init_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    async def create_document(self, repo: str, branch: str, desc: str) -> Document:
        async with AsyncSession(self.engine) as session:
            doc = Document(repo=repo, branch=branch, desc=desc, state=DocumentState.INDEXING)
            session.add(doc)
            await session.commit()
            await session.refresh(doc)
            return doc

    async def get_document(self, uid: uuid.UUID) -> Document | None:
        async with AsyncSession(self.engine) as session:
            return await session.get(Document, uid)

    async def find_document(self, repo: str, branch: str) -> Document | None:
        async with AsyncSession(self.engine) as session:
            stmt = select(Document).where(Document.repo == repo, Document.branch == branch)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def list_documents(self) -> list[Document]:
        async with AsyncSession(self.engine) as session:
            result = await session.execute(select(Document))
            return list(result.scalars().all())

    async def update_document(self, doc: Document) -> Document:
        async with AsyncSession(self.engine) as session:
            doc = await session.merge(doc)
            await session.commit()
            await session.refresh(doc)
            return doc

    async def delete_document(self, doc: Document) -> None:
        async with AsyncSession(self.engine) as session:
            doc = await session.merge(doc)
            await session.delete(doc)
            await session.commit()

    # ---- Chat Session ----

    async def create_session(self, user_id: uuid.UUID, name: str) -> ChatSession:
        async with AsyncSession(self.engine) as session:
            chat_session = ChatSession(user_id=user_id, name=name)
            session.add(chat_session)
            await session.commit()
            await session.refresh(chat_session)
            return chat_session

    async def get_session(self, session_id: uuid.UUID) -> ChatSession | None:
        async with AsyncSession(self.engine) as session:
            return await session.get(ChatSession, session_id)

    # ---- Messages ----

    async def create_message(
        self,
        session_id: uuid.UUID,
        role: MessageRole,
        content: str,
    ) -> Message:
        async with AsyncSession(self.engine) as session:
            msg = Message(session_id=session_id, role=role, content=content)
            session.add(msg)
            await session.commit()
            await session.refresh(msg)
            return msg

    async def get_message(self, message_id: uuid.UUID) -> Message | None:
        async with AsyncSession(self.engine) as session:
            return await session.get(Message, message_id)

    async def list_messages(self, session_id: uuid.UUID) -> list[Message]:
        async with AsyncSession(self.engine) as session:
            stmt = (
                select(Message)
                .where(Message.session_id == session_id)
                .order_by(Message.create_at)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def create_message_references(
        self,
        message_id: uuid.UUID,
        doc_links: list[str],
    ) -> list[MessageReference]:
        async with AsyncSession(self.engine) as session:
            refs = [
                MessageReference(message_id=message_id, doc_link=link)
                for link in doc_links
            ]
            session.add_all(refs)
            await session.commit()
            for ref in refs:
                await session.refresh(ref)
            return refs

    # ---- Evaluation ----

    async def create_evaluation(
        self,
        session_id: uuid.UUID,
        message_id: uuid.UUID,
        score: int,
        feedback: str | None = None,
    ) -> Evaluation:
        async with AsyncSession(self.engine) as session:
            evaluation = Evaluation(
                session_id=session_id,
                message_id=message_id,
                score=score,
                feedback=feedback,
            )
            session.add(evaluation)
            await session.commit()
            await session.refresh(evaluation)
            return evaluation

    # ---- Documents ----

    async def list_indexed_doc_sources(self) -> list[str]:
        async with AsyncSession(self.engine) as session:
            stmt = select(Document).where(Document.state == DocumentState.INDEXED)
            result = await session.execute(stmt)
            docs = result.scalars().all()
            return [f"{doc.repo}/{doc.branch}" for doc in docs]
