import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from llama_index.core import Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from v2.server.api.documents import router as documents_router
from v2.server.api.documents import get_db_service, get_doc_dir, get_vector_service
from v2.server.models.embeddings import BGE
from v2.server.services.db import DatabaseService
from v2.server.services.vector import VectorStoreService

load_dotenv()

_db_svc = None
_vector_svc = None


async def _get_db_service() -> DatabaseService:
    return _db_svc


def _get_doc_dir() -> str:
    return os.getenv("DOC_DIR", "/tmp/acm-docs")


def _get_vector_service() -> VectorStoreService:
    return _vector_svc


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _db_svc, _vector_svc

    Settings.llm = None
    Settings.embed_model = HuggingFaceEmbedding(model_name=BGE.name)
    Settings.transformations = [SentenceSplitter(chunk_size=BGE.chunk_size, chunk_overlap=BGE.chunk_overlap)]

    db_url = os.getenv("DATABASE_URL")
    _db_svc = DatabaseService(db_url=db_url)
    await _db_svc.init_db()

    _vector_svc = VectorStoreService(db_url=db_url, embed_dim=BGE.dims)

    doc_dir = _get_doc_dir()
    os.makedirs(doc_dir, exist_ok=True)
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.dependency_overrides[get_db_service] = _get_db_service
app.dependency_overrides[get_doc_dir] = _get_doc_dir
app.dependency_overrides[get_vector_service] = _get_vector_service
app.include_router(documents_router, prefix="/api")
