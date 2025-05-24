# coding: utf-8

"""
The request/response of evaluation
"""

from pydantic import BaseModel

class Request(BaseModel):
    issue_id: str
    resp_id: str
    score: int = 0
    feedback: str | None = None
