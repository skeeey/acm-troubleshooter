from pydantic import BaseModel

class Issue(BaseModel):
    id: str
    issue: str

class DiagnosisStep(BaseModel):
    id: str
    issue_id: str
    # step: int
    plan: str = ""
    reasoning: str = ""
    referenced_docs: list[str] = []
    results: list[str] = []
    hub_commands: list[str] = []
    spoke_commands: list[str] = []


class Evaluation(BaseModel):
    id: str
    issue_id: str
    score: int
    feedback: str
