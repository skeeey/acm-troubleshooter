import asyncio
import os
import shutil
import uuid

from fastapi import APIRouter, Depends, HTTPException, Response

from v2.server.models.db import DocumentState
from v2.server.schemas.document import CreateDocumentRequest, DocumentResponse
from v2.server.services.db import DatabaseService
from v2.server.services.vector import VectorStoreService
from v2.server.tasks.index import index_documents
from v2.server.tools.git import clone_repo, pull_repo, get_head_commit, parse_repo_name

router = APIRouter(prefix="/documents", tags=["documents"])


def get_db_service():
    raise NotImplementedError("must be overridden via app.dependency_overrides")


def get_doc_dir() -> str:
    raise NotImplementedError("must be overridden via app.dependency_overrides")


def get_vector_service():
    raise NotImplementedError("must be overridden via app.dependency_overrides")


def _to_response(doc) -> DocumentResponse:
    return DocumentResponse(
        id=str(doc.id),
        repo=doc.repo,
        branch=doc.branch,
        desc=doc.desc,
        latest_commit=doc.latest_commit,
        state=doc.state.value,
        error=doc.error,
    )


def _repo_dir(doc_dir: str, repo: str, branch: str) -> str:
    return os.path.join(doc_dir, f"{parse_repo_name(repo)}-{branch}")


@router.get("/")
async def list_documents(db_svc: DatabaseService = Depends(get_db_service)):
    return [_to_response(doc) for doc in await db_svc.list_documents()]


@router.get("/{doc_id}")
async def get_document(doc_id: str, db_svc: DatabaseService = Depends(get_db_service)):
    doc = await db_svc.get_document(uuid.UUID(doc_id))
    if doc is None:
        raise HTTPException(status_code=404, detail="document not found")
    return _to_response(doc)


@router.post("/", status_code=202)
async def create_document(
    req: CreateDocumentRequest,
    response: Response,
    db_svc: DatabaseService = Depends(get_db_service),
    doc_dir: str = Depends(get_doc_dir),
    vector_svc: VectorStoreService = Depends(get_vector_service),
):
    existing = await db_svc.find_document(repo=req.repo, branch=req.branch)
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="document already exists, use PUT to re-index",
        )

    repo_path = _repo_dir(doc_dir, req.repo, req.branch)

    try:
        await asyncio.to_thread(clone_repo, req.repo, repo_path, req.branch)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"failed to clone repo: {e}")

    commit = await asyncio.to_thread(get_head_commit, repo_path)
    doc = await db_svc.create_document(repo=req.repo, branch=req.branch, desc=req.desc)
    doc.latest_commit = commit
    doc = await db_svc.update_document(doc)

    response.headers["Location"] = f"/api/documents/{doc.id}"

    asyncio.create_task(index_documents(
        doc_id=doc.id,
        repo_dir=repo_path,
        repo_url=req.repo,
        branch=req.branch,
        vector_svc=vector_svc,
        db_svc=db_svc,
    ))

    return _to_response(doc)


@router.put("/{doc_id}")
async def update_document(
    doc_id: str,
    response: Response,
    db_svc: DatabaseService = Depends(get_db_service),
    doc_dir: str = Depends(get_doc_dir),
    vector_svc: VectorStoreService = Depends(get_vector_service),
):
    doc = await db_svc.get_document(uuid.UUID(doc_id))
    if doc is None:
        raise HTTPException(status_code=404, detail="document not found")

    if doc.state == DocumentState.INDEXING:
        raise HTTPException(status_code=409, detail="document is already indexing")

    repo_path = _repo_dir(doc_dir, doc.repo, doc.branch)
    if not os.path.exists(repo_path):
        raise HTTPException(status_code=500, detail="repo directory not found")

    try:
        await asyncio.to_thread(pull_repo, repo_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"failed to pull repo: {e}")

    commit = await asyncio.to_thread(get_head_commit, repo_path)
    if commit == doc.latest_commit:
        response.status_code = 200
        return _to_response(doc)

    doc.latest_commit = commit
    doc.state = DocumentState.INDEXING
    doc.error = None
    doc = await db_svc.update_document(doc)

    response.status_code = 202
    response.headers["Location"] = f"/api/documents/{doc.id}"

    asyncio.create_task(index_documents(
        doc_id=doc.id,
        repo_dir=repo_path,
        repo_url=doc.repo,
        branch=doc.branch,
        vector_svc=vector_svc,
        db_svc=db_svc,
    ))

    return _to_response(doc)


@router.delete("/{doc_id}", status_code=204)
async def delete_document(
    doc_id: str,
    db_svc: DatabaseService = Depends(get_db_service),
    doc_dir: str = Depends(get_doc_dir),
    vector_svc: VectorStoreService = Depends(get_vector_service),
):
    doc = await db_svc.get_document(uuid.UUID(doc_id))
    if doc is None:
        raise HTTPException(status_code=404, detail="document not found")

    repo_path = _repo_dir(doc_dir, doc.repo, doc.branch)
    if os.path.exists(repo_path):
        shutil.rmtree(repo_path)

    source = f"{doc.repo}/{doc.branch}"
    await asyncio.to_thread(vector_svc.delete_docs_by_source, source)

    await db_svc.delete_document(doc)
