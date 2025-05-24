# coding: utf-8

"""
Documents API
"""

import os
import uuid
import shutil
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import RedirectResponse
from server.dependencies.services import get_db_service, get_vector_store_service
from server.schemas.document import Request, Response, Commit, QueryRequest, Doc, QueryResponse
from server.services.db import DatabaseService
from server.services.vector import VectorStoreService
from server.task.index import index_documents
from server.tools.git import parse_repo, clone, pull, fetch_head_commit

router = APIRouter(prefix="/documents", tags=["documents"])

@router.get("/")
async def list_documents(db_svc: DatabaseService = Depends(get_db_service)):
    doc_list = []
    for doc in db_svc.list_documents():
        doc_list.append(Response(id=str(doc.id), repo=doc.repo, branch=doc.branch, desc=doc.desc))
    return doc_list

@router.get("/{doc_id}")
async def get_document(doc_id: str, db_svc: DatabaseService = Depends(get_db_service)):
    doc = db_svc.get_document(uuid.UUID(doc_id))
    if doc is None:
        raise HTTPException(status_code=404, detail="the runbook set not found")
    commits = []
    commits = db_svc.list_document_commits(doc.id)
    for commit in commits:
        commits.append(Commit(commit=commit.commit, state=commit.state))
    return Response(id=str(doc.id), repo=doc.repo, branch=doc.branch, desc=doc.desc, commits=commits)

@router.post("/")
async def create_or_update_document(req: Request, bg_tasks: BackgroundTasks,
    db_svc: DatabaseService = Depends(get_db_service),
    vector_store_svc: VectorStoreService = Depends(get_vector_store_service)):
    cwd = os.getenv("DOC_DIR")
    dist = f"{parse_repo(req.repo)}-{req.branch}"
    repo_dir = os.path.join(cwd, dist)

    doc = db_svc.find_document(repo=req.repo, branch=req.branch)
    if doc is not None:
        if not os.path.exists(repo_dir):
            raise HTTPException(
                status_code=500, detail="the runbook set repo dir not found"
            )

        # update the repo
        pull_result = pull(cwd=repo_dir)
        if pull_result.return_code != 0:
            raise HTTPException(status_code=500, detail=pull_result.stderr)

        # fetch the head commit
        fetch_result = fetch_head_commit(cwd=repo_dir)
        if fetch_result.return_code != 0:
            raise HTTPException(status_code=500, detail=fetch_result.stderr)

        commit = fetch_result.stdout
        doc_commit = db_svc.find_document_commit(commit=commit)
        if doc_commit is not None:
            # TODO if doc status is failed, try to reindex
            return RedirectResponse(status_code=303, url=f"/runbooksets/{str(doc.id)}")

        bg_tasks.add_task(
            index_documents,
            doc.id,
            req.repo,
            req.branch,
            commit,
            repo_dir,
            vector_store_svc,
            db_svc,
            )
        return RedirectResponse(status_code=303, url=f"/runbooksets/{str(doc.id)}")

    # clone the repo
    clone_result = clone(repo=req.repo, cwd=cwd, dist=dist, branch=req.branch)
    if clone_result.return_code != 0:
        raise HTTPException(status_code=500, detail=clone_result.stderr)

    # fetch the head commit
    fetch_result = fetch_head_commit(cwd=repo_dir)
    if fetch_result.return_code != 0:
        raise HTTPException(status_code=500, detail=fetch_result.stderr)

    commit = fetch_result.stdout

    new_rs = db_svc.create_document(repo=req.repo, branch=req.branch, desc=req.desc)

    bg_tasks.add_task(
        index_documents,
        new_rs.id,
        req.repo,
        req.branch,
        commit,
        repo_dir,
        vector_store_svc,
        db_svc,
        )
    return RedirectResponse(status_code=303, url=f"/runbooksets/{str(new_rs.id)}")

@router.delete("/{doc_id}")
async def delete_document(doc_id: str,
    db_svc: DatabaseService = Depends(get_db_service),
    vector_store_svc: VectorStoreService = Depends(get_vector_store_service)):
    doc = db_svc.get_document(uuid.UUID(doc_id))
    if doc is None:
        raise HTTPException(status_code=404, detail="the runbook set not found")

    cwd = os.getenv("DOC_DIR")
    dist = f"{parse_repo(doc.repo)}-{doc.branch}"
    repo_dir = os.path.join(cwd, dist)
    if os.path.exists(repo_dir):
        shutil.rmtree(repo_dir)

    for commit in db_svc.list_document_commits(doc.id):
        vector_store_svc.delete_docs(source=f"{dist}-{commit.commit}")

    db_svc.delete_document(doc)

# TODO post-then-get (async)
@router.post("/retrieve")
async def retrieve_document(req: QueryRequest,
    db_svc: DatabaseService = Depends(get_db_service),
    vector_store_svc: VectorStoreService = Depends(get_vector_store_service)):
    docs = db_svc.list_document_views()
    if len(docs) == 0:
        raise HTTPException(status_code=500, detail="there are no docs")
    
    # TODO filter the docs
    sources = []
    for doc in docs:
        sources.append(doc.source)

    docs = []
    nodes = vector_store_svc.retrieve(query=req.query, sources=sources)
    for n in nodes:
        docs.append(Doc(similarity=n.score, text=n.text, link=n.metadata["filelink"]))

    if len(docs) == 0:
        raise HTTPException(status_code=404, detail="no relevant docs")

    return QueryResponse(docs=docs)

