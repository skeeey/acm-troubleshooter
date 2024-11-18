import os
import chromadb
import dspy
from dotenv import load_dotenv
from dspy.retrieve.llama_index_rm import LlamaIndexRM
from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.chat_engine import CondensePlusContextChatEngine
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.groq import Groq
from llama_index.vector_stores.chroma import ChromaVectorStore

load_dotenv()

lm = dspy.LM('llama-3.1-70b-versatile', api_base='https://api.groq.com/openai/v1', api_key=os.getenv("GROQ_API_KEY"))
# lm = dspy.LM('ollama_chat/qwen2.5:32b', api_base='http://localhost:11434', api_key='')
dspy.configure(lm=lm)

class Planner(dspy.Signature):
    """Generate a troubleshooting plan for issues with Red Hat Advanced Cluster Management for Kubernetes (ACM or RHACM).
    """

    documents = dspy.InputField(desc="The relevant documents")
    issue: str = dspy.InputField()

    plan: str = dspy.OutputField(desc="The troubleshooting plan for the given issue")

class RAG(dspy.Module):
    def __init__(self, retrieve: dspy.Retrieve):
        super().__init__()
        self.retrieve = retrieve
        self.generate_plan = dspy.ChainOfThought(Planner)
    
    def forward(self, issue):
        documents = self.retrieve(issue)
        prediction = self.generate_plan(documents=documents, issue=issue)
        return dspy.Prediction(documents=documents, plan=prediction.plan)

if __name__ == "__main__":
    Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

    db = chromadb.PersistentClient(path="/Users/wliu1/Downloads/chromadb-acm-runbooks")
    chroma_collection = db.get_or_create_collection("acm")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    index = VectorStoreIndex.from_vector_store(vector_store)

    retriever = index.as_retriever()
    # nodes = retriever.retrieve("the local-cluster is unknown")
    # print(nodes.node)

    rag = RAG(retrieve=LlamaIndexRM(retriever=retriever, k=10))
    rag_response = rag(issue="the local-cluster is unknown")
    print(rag_response.plan)
