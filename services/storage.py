# coding: utf-8

import uuid
from models.persistence import Issue, DiagnosisStep
    
class StorageService:
    def __init__(self):
        self.issues = {}
        self.steps = {}
    
    def create_issue(self, issue: str) -> Issue:
        issue_id = str(uuid.uuid4())
        self.issues[issue_id] = Issue(id=issue_id, issue=issue)
        return self.issues[issue_id]
    
    def get_issue(self, id: str) -> Issue:
        return self.issues[id]
    
    def create_diagnosis_step(self, issue_id: str) -> DiagnosisStep:
        step_id = str(uuid.uuid4())
        self.steps[step_id] = DiagnosisStep(id=step_id, issue_id=issue_id, step=1)
        return self.steps[step_id]

    def update_diagnosis_step(self, step: DiagnosisStep) -> DiagnosisStep:
        self.steps[step.id] = step
        return self.steps[step.id]
    
    def get_diagnosis_step(self, id: str) -> DiagnosisStep:
        return self.steps[id]
    
    def evaluate_issue(self):
        # TODO
        return
