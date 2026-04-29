import uuid

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import SQLModel, select

from v2.server.models.db import Document, DocumentState


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
