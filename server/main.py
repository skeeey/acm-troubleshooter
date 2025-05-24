# coding: utf-8

"""
The server of ACM troubleshooter service
"""

import logging
import os
import dspy
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from llama_index.core import Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from server.api.users import router as users_router
from server.api.chat import router as chat_router
from server.api.evaluation import router as evaluation_router
from server.api.documents import router as documents_router
from server.api.slack import router as slack_router
from server.models.embeddings import BGE

os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "true"

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

# LLM settings
lm = dspy.LM(model=os.getenv("LM_MODEL"), api_base=os.getenv("LM_API_BASE"), api_key=os.getenv("LM_API_KEY"))
dspy.configure(lm=lm)

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

app.include_router(users_router, prefix="/api", tags=["users"])
app.include_router(chat_router, prefix="/api", tags=["chat"])
app.include_router(evaluation_router, prefix="/api", tags=["evaluation"])
app.include_router(documents_router, prefix="/api", tags=["documents"])

if os.getenv("SLACK_BOT_TOKEN") is not None:
    app.include_router(slack_router, prefix="/api", tags=["slack"])
