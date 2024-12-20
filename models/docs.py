# coding: utf-8

"""
The models of doc
"""

from pydantic import BaseModel

class RunBookSetVersion(BaseModel):
    version: str
    state: str

class RunBookSetRequest(BaseModel):
    repo: str
    branch: str = "main"

class RunBookSetResponse(BaseModel):
    id: str
    repo: str
    branch: str
    versions: list[RunBookSetVersion] | None = None
