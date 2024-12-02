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
    issue: str | None = None
    last_step_id: str| None = None
    results: str | None = None
    score: int = 0

class Response(BaseModel):
    issue_id: str
    step_id: str
    plan: str
    reasoning: str
    hub_commands: list[str] | None = None
    spoke_commands: list[str] | None = None

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

def add_result(step, result):
    step.plan = result["plan"]
    step.reasoning = result["reasoning"]
    step.hub_commands = result["hub_commands"]
    step.spoke_commands = result["spoke_commands"]
    return step

def resp(issue, step, result):
    return Response(
        issue_id=str(issue.id),
        step_id=str(step.id),
        plan=step.plan,
        reasoning=result["reasoning"],
        hub_commands=step.hub_commands,
        spoke_commands=step.spoke_commands,
    )
