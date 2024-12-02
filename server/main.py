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
from services.diagnosis import DiagnosisService
from services.index import RAGService
from services.storage import StorageService
from server.models import (
    LLMConfig, RetrievalConfig,
    Context, Request, RunBookSetRequest, RunBookSetResponse, RunBookSetVersion,
    add_result, resp)
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
Settings.embed_model = HuggingFaceEmbedding(model_name=BGE.name, trust_remote_code=BGE.trust_remote_code)
Settings.transformations = [SentenceSplitter(chunk_size=BGE.chunk_size, chunk_overlap=200)]

# init services
storage_svc = StorageService(db_url=os.getenv("DATABASE_URL"))
rag_svc = RAGService(db_url=os.getenv("DATABASE_URL"), embed_dim=BGE.dims)
diagnosis_svc = DiagnosisService(rag_svc=rag_svc)

# load configurations
cwd = os.getenv("DOC_DIR")

# start api server
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# endpoints
@app.get("/")
async def root():
    return "ACM Troubleshooter Services"

@app.put("/issues")
async def create_issue(req: Request):
    if is_empty(req.issue):
        raise HTTPException(status_code=422, detail="the issue is required")
    
    ctx = req.context
    if ctx is None:
        ctx = Context(
            llm_config=LLMConfig(
                model=os.getenv("LM_MODEL"),
                api_base=os.getenv("LM_API_BASE"),
                api_key=os.getenv("LM_API_KEY")),
            retrieval_config=RetrievalConfig(
                doc_sources=os.getenv("DOC_SOURCES").split(",")
            ))
    
    issue = storage_svc.create_issue(req.issue)
    storage_svc.create_context(
        issue_id=issue.id,
        llm_cfg=ctx.llm_config.model_dump_json(),
        retrieval_cfg=ctx.retrieval_config.model_dump_json())
    step = storage_svc.create_diagnosis_step(issue_id=issue.id)

    result = diagnosis_svc.diagnose(mcfg=ctx.llm_config, rcfg=ctx.retrieval_config, issue=req.issue)

    storage_svc.update_diagnosis_step(add_result(step, result))
    return resp(issue, step, result)

@app.post("/issues/{issue_id}")
async def diagnose_issue(issue_id: str, req: Request):
    if is_empty(req.last_step_id):
        raise HTTPException(status_code=422, detail="the last_step_id is required")

    ctx = storage_svc.find_context(uuid.UUID(issue_id))
    if ctx is None:
        raise HTTPException(status_code=404, detail="the issue context not found")
    
    issue = storage_svc.get_issue(uuid.UUID(issue_id))
    if issue is None:
        raise HTTPException(status_code=404, detail="the issue not found")
    
    last_step = storage_svc.get_diagnosis_step(uuid.UUID(req.last_step_id))
    if last_step is None:
        raise HTTPException(status_code=404, detail="the step not found")
    
    if not is_empty(req.results):
        last_step.results = req.results
        storage_svc.update_diagnosis_step(last_step)

    new_step = storage_svc.create_diagnosis_step(issue_id=issue.id)

    result = diagnosis_svc.diagnose(
        mcfg=LLMConfig.model_validate_json(ctx.llm_config),
        rcfg=RetrievalConfig.model_validate_json(ctx.retrieval_config),
        issue=issue.issue, plan=last_step.plan, results=last_step.results)

    storage_svc.update_diagnosis_step(add_result(new_step, result))
    return resp(issue, new_step, result)

@app.put("/issues/{issue_id}/evaluation/{step_id}")
async def evaluate_issue(issue_id: str, step_id: str, req: Request):
    issue = storage_svc.get_issue(uuid.UUID(issue_id))
    if issue is None:
        raise HTTPException(status_code=404, detail="the issue not found")
    
    last_step = storage_svc.get_diagnosis_step(uuid.UUID(step_id))
    if last_step is None:
        raise HTTPException(status_code=404, detail="the step not found")
    
    storage_svc.evaluate_issue(uuid.UUID(issue_id), uuid.UUID(step_id), req.score)

@app.get("/runbooksets")
async def list_runbook_sets():
    rs_list = []
    for rs in storage_svc.list_runbook_set():
        rs_list.append(RunBookSetResponse(id=str(rs.id), repo=rs.repo, branch=rs.branch))
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

    return RunBookSetResponse(id=str(rs.id), repo=rs.repo, branch=rs.branch, versions=versions)

@app.put("/runbooksets")
async def create_runbook_set(req: RunBookSetRequest, bg_tasks: BackgroundTasks):
    rs = storage_svc.find_runbook_set(repo=req.repo, branch=req.branch)
    if rs is not None:
        raise HTTPException(status_code=409, detail="the runbook set already exists")
    
    dist = f"{parse_repo(req.repo)}-{req.branch}"
    repo_dir = os.path.join(cwd, dist)

    clone_result = clone(repo=req.repo, cwd=cwd, dist=dist, branch=req.branch)
    if clone_result.return_code != 0:
        raise HTTPException(status_code=500, detail=clone_result.stderr)
    
    fetch_result = fetch_head_commit(cwd=repo_dir)
    if fetch_result.return_code != 0:
        raise HTTPException(status_code=500, detail=fetch_result.stderr)
    
    version = fetch_result.stdout
    
    new_rs = storage_svc.create_runbook_set(repo=req.repo, branch=req.branch)
    
    bg_tasks.add_task(index, new_rs.id, repo_dir, version, rag_svc, storage_svc)
    return RedirectResponse(status_code=303, url=f"/runbooksets/{str(new_rs.id)}")

@app.post("/runbooksets/{id}")
async def update_runbook_sets(id: str, bg_tasks: BackgroundTasks):
    rs = storage_svc.get_runbook_set(uuid.UUID(id))
    if rs is None:
        raise HTTPException(status_code=404, detail=f"the runbook set not found")
    
    repo_dir = os.path.join(cwd, f"{parse_repo(rs.repo)}-{rs.branch}")

    if not os.path.exists(repo_dir):
        raise HTTPException(status_code=500, detail="the runbook set repo dir not found")

    pull_result = pull(cwd=repo_dir)
    if pull_result.return_code != 0:
        raise HTTPException(status_code=500, detail=pull_result.stderr)

    fetch_result = fetch_head_commit(cwd=repo_dir)
    if fetch_result.return_code != 0:
        raise HTTPException(status_code=500, detail=fetch_result.stderr)
    
    version = fetch_result.stdout
    rsv = storage_svc.find_runbook_set_version(version=version)
    if rsv is not None:
        #TODO checking state
        return RedirectResponse(status_code=303, url=f"/runbooksets/{str(rs.id)}")
    
    bg_tasks.add_task(index, rs.id, repo_dir, version, rag_svc, storage_svc)
    return RedirectResponse(status_code=303, url=f"/runbooksets/{str(rs.id)}")

@app.delete("/runbooksets/{id}")
async def delete_runbook_sets(id: str):
    rs = storage_svc.get_runbook_set(uuid.UUID(id))
    if rs is None:
        raise HTTPException(status_code=404, detail=f"the runbook set not found")
    
    dist=f"{parse_repo(rs.repo)}-{rs.branch}"
    repo_dir = os.path.join(cwd, dist)
    if os.path.exists(repo_dir):
        shutil.rmtree(repo_dir)
    
    for rsv in storage_svc.list_runbook_set_versions(rs.id):
        rag_svc.delete_docs(source=f"{dist}-{rsv.version}")

    storage_svc.delete_runbook_set(rs)
