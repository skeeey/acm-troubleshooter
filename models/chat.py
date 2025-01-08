# coding: utf-8

"""
The models of chat
"""

from pydantic import BaseModel
from models.contexts import Context

class UserRequest(BaseModel):
    name: str

class UserResponse(BaseModel):
    id: str
    name: str

class Request(BaseModel):
    user_id: str
    context: Context | None = None
    issue_id: str | None = None
    query: str | None = None

class Response(BaseModel):
    issue_id: str
    resp_id: str
    resp: str
    reasoning: str
    references: str

class EvaluationRequest(BaseModel):
    issue_id: str
    resp_id: str
    score: int = 0
    feedback: str | None = None

class Record(BaseModel):
    role: str
    message: str
