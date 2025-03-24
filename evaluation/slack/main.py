import os
import json
from dotenv import load_dotenv
from ollama import Client
from pathlib import Path
from dataclasses import dataclass
from typing import List
from llama_index.core import Settings
from llama_index.core import Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from embeddings.huggingface import BGE
from models.contexts import LLMConfig, RetrievalConfig
from services.llm import LLMService
from services.index import RAGService

# load envs
load_dotenv()

doc_sources = os.getenv("DOC_SOURCES").split(",")

@dataclass
class Message:
    user: str
    msg: str

@dataclass
class Conversation:
    conversation: List[Message]

# rag settings
Settings.llm = None
Settings.context_window = 10240 # maximum input size to the LLM
Settings.embed_model = HuggingFaceEmbedding(model_name=BGE.name)
Settings.transformations = [SentenceSplitter(chunk_size=BGE.chunk_size, chunk_overlap=200)]

rag_svc = RAGService(db_url=os.getenv("DATABASE_URL"), embed_dim=BGE.dims)
llm_svc = LLMService(rag_svc=rag_svc)

prompt_template = """
Represent the following Slack conversation snippet in JSON with the format: {{"conversation":[{{"user":"<user_name>", msg:"<user_message>"}}]}}.
For example: 
{{"conversation":[{{"user":"Bob", msg:"hello"}},{{"user":"Alice", msg:"hello"}}]}}

{conversation}
"""

def to_obj(file):
    with open(file, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return Conversation(conversation=[Message(**item) for item in data['conversation']])

def ollama_call(user_prompt):
    return Client(host="http://localhost:11434").chat(
        model="qwen2.5:32b",
        messages=[
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": user_prompt},
        ])

def replay(issue):
    return llm_svc.response(
            mcfg=LLMConfig(model="", api_base="http://localhost:11434", api_key=""),
            rcfg=RetrievalConfig(doc_sources=doc_sources),
            query=issue,
            history_resps=[]
        )

def read(path):
    with open(path, 'r', encoding='utf-8') as file:
        return file.read()

def write(path, content):
    with open(path, 'w', encoding='utf-8') as file:
        file.write(content)

if __name__ == "__main__":
    conversations_dir = Path(os.path.join(Path.cwd(), "evaluation", "slack", "conversations"))
    print(to_obj(Path(conversations_dir, "c5.txt.json")))

    # txt_files = list(conversations_dir.glob('*.txt'))
    # for txt_file in txt_files:
    #     json_file = txt_file.with_suffix('.txt.json')
    #     if not json_file.exists():
    #         print(txt_file)
    #         write(
    #             json_file,
    #             ollama_call(prompt_template.format(conversation=read(txt_file))).message.content,
    #         )
