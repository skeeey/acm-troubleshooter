# coding: utf-8

"""
The request/response of user
"""

from pydantic import BaseModel

class Request(BaseModel):
    name: str

class Response(BaseModel):
    id: str
    name: str
