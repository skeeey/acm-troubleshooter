# coding: utf-8

"""
The embedding models
"""

from pydantic import BaseModel

class EmbeddingModel(BaseModel):
    name: str
    dims: int
    max_seq_len: int
    chunk_size: int
    trust_remote_code: bool

BGE = EmbeddingModel(
    name="BAAI/bge-m3",
    dims=1024,
    max_seq_len=8192,
    chunk_size=2048,
    trust_remote_code=False,
)
