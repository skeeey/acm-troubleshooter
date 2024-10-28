# coding: utf-8

import os
import logging
import time
import chromadb
from llama_index.core import StorageContext
from llama_index.core import Settings
from llama_index.core import VectorStoreIndex
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from .loader import load_local_data, query_jira_issues, load_jira_data

logging.basicConfig(level=logging.INFO, format="%(levelname)s: [%(asctime)s, %(module)s, line:%(lineno)d] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Set embedding model to https://huggingface.co/BAAI/bge-small-en-v1.5
    Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

    # Load Data
    local_data_dir = os.getenv("LOCAL_DATA_DIR")
    jira_token = os.getenv("JIRA_TOKEN")
    jira_query = os.getenv("JIRA_QUERY")

    docs = []
    if local_data_dir:
        docs.extend(load_local_data(local_data_dir))
    
    if jira_token and jira_query:
        docs.extend(load_jira_data(query_jira_issues(api_token=jira_token, query=jira_query)))

    if len(docs) == 0:
        raise ValueError("no documents are provided")

    # Build index
    logger.info("build index ...")
    db = chromadb.PersistentClient(path=os.getenv("INDEX_DIR"))
    chroma_collection = db.get_or_create_collection("acm")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    start_time = time.time()
    index = VectorStoreIndex.from_documents(
        docs,
        storage_context=StorageContext.from_defaults(vector_store=vector_store),
        # need more test, refer to
        # https://www.llamaindex.ai/blog/evaluating-the-ideal-chunk-size-for-a-rag-system-using-llamaindex-6207e5d3fec5
        # transformations=[SentenceSplitter(chunk_size=512, chunk_overlap=10)],
        show_progress=True,
    )
    logger.info("index is built, time used %.3fs", (time.time() - start_time))
