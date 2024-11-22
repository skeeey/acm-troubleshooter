# coding: utf-8

import os
import dspy
import logging
from dotenv import load_dotenv
from llama_index.core import Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from models.diagnosis import Context, Request, Response
from services.index import RAGService
from services.diagnosis import DiagnosisService
from services.storage import StorageService
from tools.embeddings.huggingface import JINA

# load envs
load_dotenv()

# log settings
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_FORMAT = "%(levelname)s: [%(asctime)s, %(module)s, line:%(lineno)d] %(message)s"

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
logger = logging.getLogger(__name__)

Settings.llm = None
Settings.embed_model = HuggingFaceEmbedding(model_name=JINA.name, trust_remote_code=JINA.trust_remote_code)
Settings.transformations = [SentenceSplitter(chunk_size=JINA.chunk_size, chunk_overlap=200)]

lm = dspy.LM(model=os.getenv("LM_MODEL"), api_base=os.getenv("LM_API_BASE"), api_key=os.getenv("LM_API_KEY"))
dspy.configure(lm=lm)

class DiagnosisREST:
    def __init__(self, rag_svc):
        self.diagnosis_svc = DiagnosisService(rag_svc=rag_svc)
        self.storage_svc = StorageService()
    
    def create_issue(self, req: Request) -> Response:
        issue = self.storage_svc.create_issue(req.issue)
        step = self.storage_svc.create_diagnosis_step(issue_id=issue.id)
        result = self.diagnosis_svc.diagnose(issue=req.issue)
        step.reasoning = result["reasoning"]
        step.plan = result["plan"]
        step.hub_commands = result["hub_commands"]
        step.spoke_commands = result["spoke_commands"]
        step = self.storage_svc.update_diagnosis_step(step=step)
        return Response(
            issue_id=issue.id,
            step_id=step.id,
            plan=step.plan,
            reasoning=step.reasoning,
            hub_commands=step.hub_commands,
            spoke_commands=step.spoke_commands,
        )

    def diagnose_issue(self, req: Request) -> Response:
        issue = self.storage_svc.get_issue(req.issue_id)
        print(issue)

        last_step = self.storage_svc.get_diagnosis_step(req.last_step_id)
        last_step.results = req.results
        self.storage_svc.update_diagnosis_step(step=last_step)


        step = self.storage_svc.create_diagnosis_step(issue_id=issue.id)
        result = self.diagnosis_svc.diagnose(issue=issue.issue, plan=last_step.plan, results=last_step.results)

        step.plan = result["plan"]
        step.reasoning = result["reasoning"]
        step.hub_commands = result["hub_commands"]
        step.spoke_commands = result["spoke_commands"]
        step = self.storage_svc.update_diagnosis_step(step=step)
        return Response(
            issue_id=req.issue_id,
            step_id=step.id,
            reasoning=step.reasoning,
            plan=step.plan,
            hub_commands=step.hub_commands,
            spoke_commands=step.spoke_commands,
        )

if __name__ == "__main__":
    db_host=os.getenv("DATABASE_HOST")
    db_pw=os.getenv("DATABASE_PASSWORD")
    rag_svc = RAGService(db_host=db_host, db_pw=db_pw, embed_dim=JINA.dims)
    
    rest = DiagnosisREST(rag_svc=rag_svc)
    
    context = Context(
        llm="",
        doc_type=["runbooks"],
        doc_version=["2.12"]
    )

    # step-1
    resp = rest.create_issue(Request(
        context=context,
        issue="my cluster local-cluster is unknown",
    ))
    print(resp)

    # step-2
    resp = rest.diagnose_issue(Request(
        context=context,
        issue_id=resp.issue_id,
        last_step_id=resp.step_id,
        results=["the ManagedClusterConditionAvailable is Unknown", "the ManagedClusterImportSucceeded is True"] 
    ))
    print(resp)

    # step-3
    resp = rest.diagnose_issue(Request(
        context=context,
        issue_id=resp.issue_id,
        last_step_id=resp.step_id,
        results=["the klusterlet is found"] 
    ))
    print(resp)

    # ....    


    # rag_svc.index_docs(os.getenv("PRODUCT_DOCS_DIR"), os.getenv("RUNBOOKS_DIR"))
    
    # runbooks = rag_svc.list_runbooks()
    # for rb in runbooks:
    #     print(rb)
    # print(len(runbooks))

    # docs = []
    # docs.extend(load_runbooks("/Users/wliu1/Workspace/foundation-docs/guide/ConfigureKlusterletCABundle.md"))
    # docs.extend(load_runbooks("/Users/wliu1/Workspace/foundation-docs/guide/ImportManagedClusterManually.md"))
    # docs.extend(load_runbooks("/Users/wliu1/Workspace/foundation-docs/guide/MetricsNotFound.md"))
    # rag_svc.refresh_runbooks(docs)

    # rag_svc.delete_runbooks("85acf42a9a7a1b656c7a1e98ff61bdf0")
    # rag_svc.retrieve(query=, kinds=["runbooks"])
