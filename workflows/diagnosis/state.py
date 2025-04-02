# coding: utf-8

from typing import TypedDict

class StepExecute(TypedDict):
    issue: str
    plan: str
    result: str
    termination: bool

def new_status(issue="", plan="", result="", termination=False):
    return {
        "issue": issue,
        "plan": plan,
        "result": result,
        "termination": termination,
    }