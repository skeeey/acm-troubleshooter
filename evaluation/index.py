# coding: utf-8

import logging
import os
from dotenv import load_dotenv
from llama_index.core import Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from services.index import RAGService
from services.storage import StorageService
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
Settings.embed_model = HuggingFaceEmbedding(
    model_name=BGE.name, trust_remote_code=BGE.trust_remote_code
)
Settings.transformations = [
    SentenceSplitter(chunk_size=BGE.chunk_size, chunk_overlap=200)
]

# init services
storage_svc = StorageService(db_url=os.getenv("DATABASE_URL"))
rag_svc = RAGService(db_url=os.getenv("DATABASE_URL"), embed_dim=BGE.dims)

sources=['skeeey-foundation-docs-test-60ddbda', 'skeeey-acm-docs-2-12-64acf75']
cutoff=0.65

if __name__ == "__main__":
    issues = {}
    for issue in storage_svc.list_issue():
        if issue.issue in issues:
            ids = issues[issue.issue]
            ids.append(str(issue.id))
            continue

        issues[issue.issue] = [str(issue.id)]
    
    for issue in issues.keys():
        nodes = rag_svc.retrieve(query=issue, sources=sources, minimum_similarity_cutoff=cutoff)
        if len(nodes) == 0:
            print("----")
            print(issue)
            print("----")
    
    # for key in issues.keys():
    #     if len(issues[key]) > 1:
    #         print(f"DELETE FROM issue WHERE id IN ('{"', '".join(issues[key][1:])}');")
