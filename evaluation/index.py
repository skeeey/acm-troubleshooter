# coding: utf-8

"""
Evaluate the retrieve and rerank
"""

import os
import time
import mlflow
import dspy
import logging
from dotenv import load_dotenv
from llama_index.core import Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from signatures.retriever import convert_question, grade_relevant_nodes
from services.index import RAGService
from services.storage import StorageService
from tools.embeddings.huggingface import BGE
from tools.common import is_empty
from evaluation.cases import irrelevant_cases, cluster_cases, addon_cases, question_cases

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

mlflow.dspy.autolog()
mlflow.set_experiment("DSPy")

# rag settings
Settings.llm = None
Settings.context_window = 10240 # maximum input size to the LLM
Settings.embed_model = HuggingFaceEmbedding(model_name=BGE.name)
Settings.transformations = [SentenceSplitter(chunk_size=BGE.chunk_size, chunk_overlap=200)]

# init services
storage_svc = StorageService(db_url=os.getenv("DATABASE_URL"))
rag_svc = RAGService(db_url=os.getenv("DATABASE_URL"), embed_dim=BGE.dims)
sources=os.getenv("DOC_SOURCES").split(",")

def list_issues():
    issues = {}
    for issue in storage_svc.list_issue():
        if issue.name in issues:
            ids = issues[issue.name]
            ids.append(str(issue.id))
            continue

        issues[issue.name] = [str(issue.id)]
    return issues.keys()

# Evaluate retrieve, use the following indicators:
# - Relevancy
# - TODO Faithfulness (hallucinations, add expected results or use an advanced LLM)
# - Response Time
def evaluate_retrieve(issue, with_converter=False, with_grade=False):
    retrieve(issue, with_grade)
    if with_converter:
        new_issue = convert_question("", issue)
        retrieve(new_issue, with_grade)

def retrieve(query, with_grade=False):
    print("==============")
    print("issue:", query)
    if is_empty(query):
        return

    start_time = time.time()
    nodes = rag_svc.retrieve(query=query, sources=sources)
    r_elapsed_time = time.time() - start_time
    print(f"retrieved time used {r_elapsed_time:.3f}")
    print(f"retrieved nodes:{len(nodes)}")
    for n in nodes:
        print(f"{n.score:.3f}, {n.metadata["filename"]}")

    if not with_grade:
        return

    start_time = time.time()
    relevant_nodes = grade_relevant_nodes(nodes, query)
    g_elapsed_time = time.time() - start_time
    print(f"grade time used {g_elapsed_time:.3f}")
    print("relevant nodes:", len(relevant_nodes))
    for rn in relevant_nodes:
        print(f"{rn.score}, {rn.node.score:.3f}, {rn.node.metadata["filename"]}")

if __name__ == "__main__":
    for case in irrelevant_cases:
        evaluate_retrieve(case)

    for case in cluster_cases:
        evaluate_retrieve(case)

    for case in addon_cases:
        evaluate_retrieve(case)

    for case in question_cases:
        evaluate_retrieve(case, True)
