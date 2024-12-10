# coding: utf-8

import logging
import os
import shutil
import uuid
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from llama_index.core import Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from services.llm import LLMService
from services.index import RAGService
from services.storage import StorageService
from server.models import (
    LLMConfig,
    RetrievalConfig,
    Context,
    Request,
    Response,
    EvaluationRequest,
    RunBookSetRequest,
    RunBookSetResponse,
    RunBookSetVersion,
)
from tasks.runbooks import index
from tools.common import is_empty
from tools.git import parse_repo, clone, pull, fetch_head_commit
from tools.embeddings.huggingface import BGE

# load envs
load_dotenv()

# log settings
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_FORMAT = "%(levelname)s: [%(asctime)s, %(module)s, line:%(lineno)d] %(message)s"

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
logger = logging.getLogger(__name__)

# rag settings
Settings.llm = None
Settings.embed_model = HuggingFaceEmbedding(model_name=BGE.name)
Settings.transformations = [SentenceSplitter(chunk_size=BGE.chunk_size, chunk_overlap=200)]
doc_sources = os.getenv("DOC_SOURCES").split(",")

# default llm settings
llm_model=os.getenv("LM_MODEL")
llm_api_base=os.getenv("LM_API_BASE")
llm_api_key=os.getenv("LM_API_KEY")

# init services
storage_svc = StorageService(db_url=os.getenv("DATABASE_URL"))
rag_svc = RAGService(db_url=os.getenv("DATABASE_URL"), embed_dim=BGE.dims)
llm_svc = LLMService(rag_svc=rag_svc)

# load configurations
cwd = os.getenv("DOC_DIR")

# start api server
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:8000",
        "http://127.0.0.1",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/issues")
async def resolve(req: Request) -> Response:
    issue_id = req.issue_id

    # a new issue, create it and give an init response
    if is_empty(issue_id):
        if is_empty(req.user_inputs):
            raise HTTPException(status_code=422, detail="the issue is required")

        ctx = req.context
        if ctx is None:
            ctx = Context(
                llm_config=LLMConfig(model=llm_model, api_base=llm_api_base,api_key=llm_api_key),
                retrieval_config=RetrievalConfig(doc_sources=doc_sources),
            )

        issue = storage_svc.create_issue(req.user_inputs)
        storage_svc.create_context(
            issue_id=issue.id,
            llm_cfg=ctx.llm_config.model_dump_json(),
            retrieval_cfg=ctx.retrieval_config.model_dump_json(),
        )
        db_resp = storage_svc.create_resp(issue_id=issue.id)

        llm_resp = llm_svc.response(
            mcfg=ctx.llm_config,
            rcfg=ctx.retrieval_config,
            issue=req.user_inputs,
        )
        db_resp.asst_resp = llm_resp["response"]
        db_resp.reasoning = llm_resp["reasoning"]
        db_resp.referenced_docs = llm_resp["relevant_doc_names"]
        
        storage_svc.update_resp(db_resp)
        
        return Response(issue_id=str(issue.id), resp_id=str(db_resp.id),
                        asst_resp=db_resp.asst_resp, reasoning=db_resp.reasoning,)

    # an existed issue, continue to resolve the issue with user's new inputs
    if is_empty(req.last_resp_id):
        raise HTTPException(status_code=422, detail="the last_asst_resp_id is required")
    
    if is_empty(req.user_inputs):
        raise HTTPException(status_code=422, detail="the user resp is required")

    ctx = storage_svc.find_context(uuid.UUID(issue_id))
    if ctx is None:
        raise HTTPException(status_code=404, detail="the issue context not found")

    issue = storage_svc.get_issue(uuid.UUID(issue_id))
    if issue is None:
        raise HTTPException(status_code=404, detail="the issue not found")

    last_resp = storage_svc.get_resp(uuid.UUID(req.last_resp_id))
    if last_resp is None:
        raise HTTPException(status_code=404, detail="the last asst resp not found")

    last_resp.user_resp = req.user_inputs
    storage_svc.update_resp(last_resp)

    db_resp = storage_svc.create_resp(issue_id=issue.id)

    llm_resp = llm_svc.response(
        mcfg=LLMConfig.model_validate_json(ctx.llm_config),
        rcfg=RetrievalConfig.model_validate_json(ctx.retrieval_config),
        issue=issue.issue,
        last_asst_resp=last_resp.asst_resp,
        feedback=req.user_inputs,
    )

    db_resp.asst_resp = llm_resp["response"]
    db_resp.reasoning = llm_resp["reasoning"]
    db_resp.referenced_docs = llm_resp["relevant_doc_names"]
    
    storage_svc.update_resp(db_resp)
    
    return Response(issue_id=str(issue.id), resp_id=str(db_resp.id),
                    asst_resp=db_resp.asst_resp, reasoning=db_resp.reasoning)

@app.put("/issues/{issue_id}/evaluation/{resp_id}")
async def evaluate(issue_id: str, resp_id: str, req: EvaluationRequest):
    issue = storage_svc.get_issue(uuid.UUID(issue_id))
    if issue is None:
        raise HTTPException(status_code=404, detail="the issue not found")

    resp = storage_svc.get_resp(uuid.UUID(resp_id))
    if resp is None:
        raise HTTPException(status_code=404, detail="the step not found")

    storage_svc.evaluate(uuid.UUID(issue_id), uuid.UUID(resp_id), req.score, req.feedback)

@app.get("/runbooksets")
async def list_runbook_sets():
    rs_list = []
    for rs in storage_svc.list_runbook_set():
        rs_list.append(
            RunBookSetResponse(id=str(rs.id), repo=rs.repo, branch=rs.branch)
        )
    return rs_list

@app.get("/runbooksets/{id}")
async def get_runbook_set(id: str):
    rs = storage_svc.get_runbook_set(uuid.UUID(id))
    if rs is None:
        raise HTTPException(status_code=404, detail=f"the runbook set not found")

    versions = []
    rsvs = storage_svc.list_runbook_set_versions(rs.id)
    for rsv in rsvs:
        versions.append(RunBookSetVersion(version=rsv.version, state=rsv.state))

    return RunBookSetResponse(
        id=str(rs.id), repo=rs.repo, branch=rs.branch, versions=versions
    )

@app.post("/runbooksets")
async def create_or_update_runbook_set(req: RunBookSetRequest, bg_tasks: BackgroundTasks):
    dist = f"{parse_repo(req.repo)}-{req.branch}"
    repo_dir = os.path.join(cwd, dist)

    rs = storage_svc.find_runbook_set(repo=req.repo, branch=req.branch)
    if rs is not None:
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
        
        version = fetch_result.stdout
        rsv = storage_svc.find_runbook_set_version(version=version)
        if rsv is not None:
            # TODO if rsv status is failed, try to reindex 
            return RedirectResponse(status_code=303, url=f"/runbooksets/{str(rs.id)}")
        
        bg_tasks.add_task(index, rs.id, repo_dir, version, rag_svc, storage_svc)
        return RedirectResponse(status_code=303, url=f"/runbooksets/{str(rs.id)}")

    # clone the repo
    clone_result = clone(repo=req.repo, cwd=cwd, dist=dist, branch=req.branch)
    if clone_result.return_code != 0:
        raise HTTPException(status_code=500, detail=clone_result.stderr)

    # fetch the head commit
    fetch_result = fetch_head_commit(cwd=repo_dir)
    if fetch_result.return_code != 0:
        raise HTTPException(status_code=500, detail=fetch_result.stderr)

    version = fetch_result.stdout

    new_rs = storage_svc.create_runbook_set(repo=req.repo, branch=req.branch)

    bg_tasks.add_task(index, new_rs.id, repo_dir, version, rag_svc, storage_svc)
    return RedirectResponse(status_code=303, url=f"/runbooksets/{str(new_rs.id)}")

@app.delete("/runbooksets/{id}")
async def delete_runbook_sets(id: str):
    rs = storage_svc.get_runbook_set(uuid.UUID(id))
    if rs is None:
        raise HTTPException(status_code=404, detail=f"the runbook set not found")

    dist = f"{parse_repo(rs.repo)}-{rs.branch}"
    repo_dir = os.path.join(cwd, dist)
    if os.path.exists(repo_dir):
        shutil.rmtree(repo_dir)

    for rsv in storage_svc.list_runbook_set_versions(rs.id):
        rag_svc.delete_docs(source=f"{dist}-{rsv.version}")

    storage_svc.delete_runbook_set(rs)
