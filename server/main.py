# coding: utf-8

import dspy
import logging
import os
import uuid
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from llama_index.core import Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from pydantic import BaseModel
from services.diagnosis import DiagnosisService
from services.index import RAGService
from services.storage import StorageService
from tools.common import is_empty
from tools.embeddings.huggingface import JINA

class Context(BaseModel):
    lm_url: str | None = None
    doc_kinds: list[str] | None = None
    doc_versions: list[str] | None = None

class Request(BaseModel):
    context: Context | None = None
    issue: str | None = None
    last_step_id: str| None = None
    results: str | None = None
    score: int = 0

class Response(BaseModel):
    issue_id: str
    step_id: str
    plan: str
    reasoning: str
    hub_commands: list[str] | None = None
    spoke_commands: list[str] | None = None

# load envs
load_dotenv()

# log settings
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_FORMAT = "%(levelname)s: [%(asctime)s, %(module)s, line:%(lineno)d] %(message)s"

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
logger = logging.getLogger(__name__)

# rag settings
Settings.llm = None
Settings.embed_model = HuggingFaceEmbedding(model_name=JINA.name, trust_remote_code=JINA.trust_remote_code)
Settings.transformations = [SentenceSplitter(chunk_size=JINA.chunk_size, chunk_overlap=200)]

# llm settings
lm = dspy.LM(model=os.getenv("LM_MODEL"), api_base=os.getenv("LM_API_BASE"), api_key=os.getenv("LM_API_KEY"))
dspy.configure(lm=lm)

# init services
storage_svc = StorageService(db_url=os.getenv("DATABASE_URL"))
rag_svc = RAGService(db_url=os.getenv("DATABASE_URL"), embed_dim=JINA.dims)
diagnosis_svc = DiagnosisService(rag_svc=rag_svc)

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

@app.get("/")
async def root():
    return "ACM Troubleshooter Services"

@app.put("/issues")
async def create_issue(req: Request):
    if is_empty(req.issue):
        return HTTPException(status_code=422, detail="the 'issue' in request is required")
    
    ctx = req.context
    if ctx is None:
        ctx = Context()
    
    issue = storage_svc.create_issue(req.issue, ctx.lm_url, ctx.doc_kinds, ctx.doc_versions)
    logger.info("issue (%s) is created", issue.id)
    step = storage_svc.create_diagnosis_step(issue_id=issue.id)
    result = diagnosis_svc.diagnose(issue=req.issue)
    storage_svc.update_diagnosis_step(add_result(step, result))
    logger.info("step (%s) for issue (%s) is created", step.id, issue.id)
    return resp(issue, step)

@app.post("/issues/{issue_id}")
async def diagnose_issue(issue_id: str, req: Request):
    if is_empty(req.last_step_id):
        return HTTPException(status_code=422, detail="the 'last_step_id' in request is required")

    issue = storage_svc.get_issue(uuid.UUID(issue_id))
    if issue is None:
        return HTTPException(status_code=404, detail=f"the issue ({issue_id}) not found")
    
    last_step = storage_svc.get_diagnosis_step(uuid.UUID(req.last_step_id))
    if last_step is None:
        return HTTPException(status_code=404, detail=f"the step ({req.last_step_id}) not found")
    
    if not is_empty(req.results):
        print(req.results)
        last_step.results = req.results
        storage_svc.update_diagnosis_step(last_step)

    new_step = storage_svc.create_diagnosis_step(issue_id=issue.id)
    result = diagnosis_svc.diagnose(issue=issue.issue, plan=last_step.plan, results=last_step.results)
    storage_svc.update_diagnosis_step(add_result(new_step, result))
    logger.info("step (%s) for issue (%s) is created", new_step.id, issue.id)
    return resp(issue, new_step)

@app.put("/issues/{issue_id}/evaluation/{step_id}")
async def evaluate_issue(issue_id: str, step_id: str, req: Request):
    print(issue_id, step_id, req)
    issue = storage_svc.get_issue(uuid.UUID(issue_id))
    if issue is None:
        return HTTPException(status_code=404, detail=f"the issue ({issue_id}) not found")
    
    last_step = storage_svc.get_diagnosis_step(uuid.UUID(step_id))
    if last_step is None:
        return HTTPException(status_code=404, detail=f"the step ({step_id}) not found")
    
    storage_svc.evaluate_issue(uuid.UUID(issue_id), uuid.UUID(step_id), req.score)
    logger.info("the step (%s) for issue (%s) is evaluated", step_id, issue_id)
    return {"message": f"the step ${step_id} for issue ${issue_id} is evaluated"}

@app.get("/runbooks")
async def list_runbooks():
    return

@app.post("/runbooks")
async def refresh_runbooks():
    return

@app.delete("/runbooks/{runbook_id}")
async def delete_runbooks():
    return

def add_result(step, result):
    step.plan = result["plan"]
    step.reasoning = result["reasoning"]
    step.hub_commands = result["hub_commands"]
    step.spoke_commands = result["spoke_commands"]
    return step

def resp(issue, step):
    return Response(
        issue_id=str(issue.id),
        step_id=str(step.id),
        plan=step.plan,
        reasoning=step.reasoning,
        hub_commands=step.hub_commands,
        spoke_commands=step.spoke_commands,
    )
