# coding: utf-8

import cmd
import chromadb
import logging
import os
from dotenv import load_dotenv
from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.chat_engine import CondensePlusContextChatEngine
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.groq import Groq
from llama_index.vector_stores.chroma import ChromaVectorStore
from prompts.templates import CHATBOT_PROMPT

# log settings
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_FORMAT = "%(levelname)s: [%(asctime)s, %(module)s, line:%(lineno)d] %(message)s"

load_dotenv()

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
logger = logging.getLogger(__name__)

class ChatEngine:
    def __init__(self, index_dir, llm, verbose=True):
        db = chromadb.PersistentClient(path=index_dir)
        chroma_collection = db.get_or_create_collection("acm")
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        index = VectorStoreIndex.from_vector_store(vector_store)
        self.chat_engine = CondensePlusContextChatEngine.from_defaults(
           retriever=VectorIndexRetriever(index=index, similarity_top_k=10),
           memory=ChatMemoryBuffer.from_defaults(token_limit=40960),
           llm=llm,
           context_prompt=CHATBOT_PROMPT,
           verbose=verbose)

    def chat(self, question):
        response = self.chat_engine.chat(question)
        return response

class ChatBot(cmd.Cmd):
    intro = (
        "Welcome to the chat shell. \n"
        "Using `m <Your message>` to send a message. \n"
        "Type help or ? to list commands.\n"
    )
    prompt = "(Chat🦙) "

    def __init__(self, engine:ChatEngine):
        super().__init__()
        self.engine = engine

    def do_m(self, message):
        """Send a question to the current conversation and get back the AI's response: m <Your message>"""
        resp = self.engine.chat(message.strip())
        print(f"\n\n{resp}")

    def do_bye(self, _):
        """Quits the chat."""
        print("Bye")
        raise SystemExit

if __name__ == "__main__":
    llm = Groq(model="llama-3.1-70b-versatile", api_key=os.getenv("GROQ_API_KEY"))

    Settings.llm = llm
    Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

    chat_engine = ChatEngine(
        index_dir=os.getenv("INDEX_DIR"),
        llm=llm,
        verbose=False,
    )
    ChatBot(chat_engine).cmdloop()
