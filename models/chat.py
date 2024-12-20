# coding: utf-8

"""
The models of chat
"""

from pydantic import BaseModel
from models.contexts import Context

class Request(BaseModel):
    context: Context | None = None
    issue_id: str | None = None
    query: str | None = None

class Response(BaseModel):
    issue_id: str
    resp_id: str
    resp: str
    reasoning: str

class EvaluationRequest(BaseModel):
    issue_id: str
    resp_id: str
    score: int = 0
    feedback: str | None = None

class Record(BaseModel):
    role: str
    message: str
