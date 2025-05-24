from llama_index.core.schema import NodeWithScore
from pydantic import BaseModel

class RelevantNode(BaseModel):
    node: NodeWithScore
    score: int = 0
