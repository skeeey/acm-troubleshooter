# coding: utf-8

from pydantic import BaseModel

class LLMConfig(BaseModel):
    api_base: str | None = None
    api_key: str | None = None
    model: str | None = None

class RetrievalConfig(BaseModel):
    doc_sources: list[str] | None = None

class Context(BaseModel):
    llm_config: LLMConfig | None = None
    retrieval_config: RetrievalConfig | None = None

class Request(BaseModel):
    context: Context | None = None
    issue_id: str | None = None
    last_resp_id: str | None = None
    user_inputs: str | None = None

class Response(BaseModel):
    issue_id: str
    resp_id: str
    asst_resp: str
    reasoning: str
    hub_commands: list[str] | None = None
    spoke_commands: list[str] | None = None

class EvaluationRequest(BaseModel):
    score: int = 0
    feedback: str | None = None

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
