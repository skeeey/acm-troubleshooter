# coding: utf-8

from pydantic import BaseModel

class EmbeddingModel(BaseModel):
    name: str
    dims: int
    max_seq_len: int
    chunk_size: int
    trust_remote_code: bool

# see https://huggingface.co/spaces/mteb/leaderboard

# embedding acm docs
# index time: 523.934s
# question: my cluster local-cluster is unknown
# retrieve time: 12.151s
# retrieved items: 9
# retrieved highest score: 0.716 ~ 0.687
GTE = EmbeddingModel(
    name="Alibaba-NLP/gte-large-en-v1.5",
    dims=1024,
    max_seq_len=8192,
    chunk_size=1024,
    trust_remote_code=True,
)

# embedding acm docs
# index time: 376.757s
# question: my cluster local-cluster is unknown
# retrieve time: 12.803s
# retrieved items: 10
# retrieved score: 0.771 ~ 0.707
JINA = EmbeddingModel(
    name="jinaai/jina-embeddings-v3",
    dims=1024,
    max_seq_len=1024,
    chunk_size=920,
    trust_remote_code=True,
)

BGE = EmbeddingModel(
    name="BAAI/bge-m3",
    dims=1024,
    max_seq_len=8192,
    chunk_size=1024,
    trust_remote_code=False,
)
