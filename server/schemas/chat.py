# coding: utf-8

"""
The request/response of chat
"""

from pydantic import BaseModel

class Request(BaseModel):
    user_id: str
    issue_id: str | None = None
    query: str | None = None

class Response(BaseModel):
    issue_id: str
    resp_id: str
    resp: str
    reasoning: str
    references: str
