from pydantic import BaseModel

class Context(BaseModel):
    llm: str = ""
    doc_type: list[str] = ["runbooks"]
    doc_version: list[str] = ["2.12"]

class Request(BaseModel):
    issue_id: str = ""
    last_step_id: str = ""
    issue: str = ""
    results: list[str] = []
    context: Context = None

class Response(BaseModel):
    issue_id: str
    step_id: str
    plan: str
    reasoning: str
    hub_commands: list[str]
    spoke_commands: list[str]