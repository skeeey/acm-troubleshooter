# coding: utf-8

"""
The request/response of document
"""

from pydantic import BaseModel

class Commit(BaseModel):
    commit: str
    state: str

class Request(BaseModel):
    repo: str
    branch: str = "main"
    desc: str

class Response(BaseModel):
    id: str
    repo: str
    branch: str
    desc: str
    commits: list[Commit] | None = None

class QueryRequest(BaseModel):
    query: str
    sources: list[str] | None = None
    top_k: int | None = 10 # similarity top_k
    top_n: int | None = 3 # rerank top_n
    cutoff: float | None = 0.5 # similarity top_k

class Doc(BaseModel):
    similarity: float
    link: str
    text: str

class QueryResponse(BaseModel):
    docs: list[Doc]
