# coding: utf-8

"""
Evaluate the retrieve and rerank
"""

import os
import time
# import mlflow
import dspy
import logging
from dotenv import load_dotenv
from llama_index.core import Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from server.models.embeddings import BGE
from server.services.vector import VectorStoreService
from server.services.db import DatabaseService
from server.tools.common import is_empty
from server.tools.llm import convert_question, grade_relevant_nodes
from evaluation.queries import queries

os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "true"

# load envs
load_dotenv()

# log settings
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_FORMAT = "%(levelname)s: [%(asctime)s, %(module)s, line:%(lineno)d] %(message)s"

logging.basicConfig(level=logging.ERROR, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
logger = logging.getLogger(__name__)

# rag settings
Settings.llm = None
Settings.context_window = 10240 # maximum input size to the LLM
Settings.embed_model = HuggingFaceEmbedding(model_name=BGE.name)
Settings.transformations = [SentenceSplitter(chunk_size=BGE.chunk_size, chunk_overlap=200)]

# LLM settings
lm = dspy.LM(model=os.getenv("LM_MODEL"), api_base=os.getenv("LM_API_BASE"), api_key=os.getenv("LM_API_KEY"))
dspy.configure(lm=lm)

# mlflow.dspy.autolog()
# mlflow.set_experiment("DSPy")

# init services
db_svc = DatabaseService(db_url=os.getenv("DATABASE_URL"))
rag_svc = VectorStoreService(db_url=os.getenv("DATABASE_URL"), embed_dim=BGE.dims)

# Evaluate retrieve, use the following indicators:
# - Relevancy
# - TODO Faithfulness (hallucinations, add expected results or use an advanced LLM)
# - Response Time
def evaluate_retrieve(query, with_grade=True, with_converter=False):
    if with_converter:
        query = convert_question({}, query)
    retrieve(query, with_grade)

def retrieve(query, with_grade):
    print("==============")
    print("query:", query)
    if is_empty(query):
        return

    start_time = time.time()
    sources = []
    for doc in db_svc.list_document_views(doc_state="indexed", only_latest=True):
        sources.append(doc.source)

    nodes = rag_svc.retrieve(query=query, sources=sources)
    r_elapsed_time = time.time() - start_time
    print(f"retrieved time used {r_elapsed_time:.3f}s")
    print(f"retrieved nodes:{len(nodes)}")
    for n in nodes:
        print(f"{n.score:.3f}, {n.metadata["filename"]}")

    if not with_grade:
        return

    start_time = time.time()
    relevant_nodes = grade_relevant_nodes(nodes, query)
    g_elapsed_time = time.time() - start_time
    print(f"grade time used {g_elapsed_time:.3f}s")
    print("relevant nodes:", len(relevant_nodes))
    for rn in relevant_nodes:
        print(f"{rn.score}, {rn.node.score:.3f}, {rn.node.metadata["filename"]}")

if __name__ == "__main__":
    for q in queries[0:1]:
        evaluate_retrieve(q)
