# coding: utf-8

"""
The server of ACM troubleshooter service
"""

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
from models.contexts import LLMConfig, RetrievalConfig, Context
from models.chat import Request, Response, EvaluationRequest
from models.docs import RunBookSetRequest, RunBookSetResponse, RunBookSetVersion
from services.llm import LLMService
from services.index import RAGService
from services.storage import StorageService
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
Settings.context_window = 10240 # maximum input size to the LLM
Settings.embed_model = HuggingFaceEmbedding(model_name=BGE.name)
Settings.transformations = [SentenceSplitter(chunk_size=BGE.chunk_size, chunk_overlap=200)]
# TODO use the latest doc sources
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

@app.post("/chat")
async def chat(req: Request) -> Response:
    issue_id = req.issue_id

    if is_empty(issue_id): # a new issue, create it and give an init response
        if is_empty(req.query):
            raise HTTPException(status_code=422, detail="the user inputs are required")

        ctx = req.context
        if ctx is None:
            ctx = Context(
                llm_config=LLMConfig(model=llm_model, api_base=llm_api_base, api_key=llm_api_key),
                retrieval_config=RetrievalConfig(doc_sources=doc_sources),
            )

        issue = storage_svc.create_issue(name=req.query)
        storage_svc.create_context(
            issue_id=issue.id,
            llm_cfg=ctx.llm_config.model_dump_json(),
            retrieval_cfg=ctx.retrieval_config.model_dump_json(),
        )

        llm_resp = llm_svc.response(mcfg=ctx.llm_config, rcfg=ctx.retrieval_config, query=req.query, history_resps=[])

        db_resp = storage_svc.create_resp(
            issue_id=issue.id,
            user_query=req.query,
            asst_resp=llm_resp["response"],
            reasoning=llm_resp["reasoning"],
            referenced_docs = llm_resp["relevant_doc_names"],
        )
        return Response(issue_id=str(db_resp.issue_id), resp_id=str(db_resp.id),
                        resp=db_resp.asst_resp, reasoning=db_resp.reasoning)

    # an existed issue, continue to resolve the issue with user's new inputs
    if is_empty(req.query):
        raise HTTPException(status_code=422, detail="the user inputs are required")

    ctx = storage_svc.find_context(uuid.UUID(issue_id))
    if ctx is None:
        raise HTTPException(status_code=404, detail="the issue context not found")

    issue = storage_svc.get_issue(uuid.UUID(issue_id))
    if issue is None:
        raise HTTPException(status_code=404, detail="the issue not found")

    llm_resp = llm_svc.response(
        mcfg=LLMConfig.model_validate_json(ctx.llm_config),
        rcfg=RetrievalConfig.model_validate_json(ctx.retrieval_config),
        query=req.query,
        history_resps=storage_svc.list_resp(uuid.UUID(issue_id)),
    )

    db_resp = storage_svc.create_resp(
        issue_id=issue_id,
        user_query=req.query,
        asst_resp=llm_resp["response"],
        reasoning=llm_resp["reasoning"],
        referenced_docs = llm_resp["relevant_doc_names"],
    )
    return Response(issue_id=str(db_resp.issue_id), resp_id=str(db_resp.id),
                    resp=db_resp.asst_resp, reasoning=db_resp.reasoning)

@app.put("/evaluation")
async def evaluate(req: EvaluationRequest):
    issue = storage_svc.get_issue(uuid.UUID(req.issue_id))
    if issue is None:
        raise HTTPException(status_code=404, detail="the issue not found")

    resp = storage_svc.get_resp(uuid.UUID(req.resp_id))
    if resp is None:
        raise HTTPException(status_code=404, detail="the responses not found")

    storage_svc.evaluate(issue.id, resp.id, req.score, req.feedback)

@app.get("/runbooksets")
async def list_runbook_sets():
    rs_list = []
    for rs in storage_svc.list_runbook_set():
        rs_list.append(
            RunBookSetResponse(id=str(rs.id), repo=rs.repo, branch=rs.branch)
        )
    return rs_list

@app.get("/runbooksets/{runbook_set_id}")
async def get_runbook_set(runbook_set_id: str):
    rs = storage_svc.get_runbook_set(uuid.UUID(runbook_set_id))
    if rs is None:
        raise HTTPException(status_code=404, detail="the runbook set not found")

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

@app.delete("/runbooksets/{runbook_set_id}")
async def delete_runbook_sets(runbook_set_id: str):
    rs = storage_svc.get_runbook_set(uuid.UUID(runbook_set_id))
    if rs is None:
        raise HTTPException(status_code=404, detail="the runbook set not found")

    dist = f"{parse_repo(rs.repo)}-{rs.branch}"
    repo_dir = os.path.join(cwd, dist)
    if os.path.exists(repo_dir):
        shutil.rmtree(repo_dir)

    for rsv in storage_svc.list_runbook_set_versions(rs.id):
        rag_svc.delete_docs(source=f"{dist}-{rsv.version}")

    storage_svc.delete_runbook_set(rs)
