# coding: utf-8

import os
import time
import dspy
import logging
from dotenv import load_dotenv
from llama_index.core import Settings 
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from signatures.retriever import grade_relevant_nodes
from services.index import RAGService
from services.storage import StorageService
from tools.embeddings.huggingface import BGE
from evaluation.issues import items

# load envs
load_dotenv()

# log settings
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_FORMAT = "%(levelname)s: [%(asctime)s, %(module)s, line:%(lineno)d] %(message)s"

logging.basicConfig(level=logging.ERROR, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
logger = logging.getLogger(__name__)

# llm settings
lm = dspy.LM(model=os.getenv("LM_MODEL"), api_base=os.getenv("LM_API_BASE"), api_key=os.getenv("LM_API_KEY"))
dspy.configure(lm=lm)

# rag settings
Settings.llm = None
Settings.embed_model = HuggingFaceEmbedding(model_name=BGE.name)
Settings.transformations = [SentenceSplitter(chunk_size=BGE.chunk_size, chunk_overlap=200)]

# cutoff=0.5
# top_k=3

# init services
storage_svc = StorageService(db_url=os.getenv("DATABASE_URL"))
rag_svc = RAGService(db_url=os.getenv("DATABASE_URL"), embed_dim=BGE.dims)
sources=os.getenv("DOC_SOURCES").split(",")

def list_issues():
    issues = {}
    for issue in storage_svc.list_issue():
        if issue.issue in issues:
            ids = issues[issue.issue]
            ids.append(str(issue.id))
            continue

        issues[issue.issue] = [str(issue.id)]
    return issues.keys()

# Evaluate retrieve, use the following indicators:
# - Relevancy
# - TODO Faithfulness (hallucinations, add expected results or use an advanced LLM)
# - Response Time
def evaluate_retrieve():
    for issue in items:
        start_time = time.time()
        nodes = rag_svc.retrieve(query=issue, sources=sources)
        r_elapsed_time = time.time() - start_time

        start_time = time.time()
        relevant_nodes = grade_relevant_nodes(nodes, issue)
        g_elapsed_time = time.time() - start_time
        
        print("==============")
        print("issue:", issue)
        print("retrieved time used %.3fs" % r_elapsed_time)
        print("grade time used %.3fs" % g_elapsed_time)
        print("retrieved nodes:", len(nodes))
        for node in nodes:
            print("%.3f, %s" % (node.score, node.metadata["filename"]))
        print("relevant nodes:", len(relevant_nodes))
        for node in relevant_nodes:
            print("%.3f, %s" % (node.score, node.metadata["filename"]))

if __name__ == "__main__":
    evaluate_retrieve()
