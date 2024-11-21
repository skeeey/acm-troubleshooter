# coding: utf-8

from langgraph.graph import END
from workflows.diagnosis.state import StepExecute

def should_end(state: StepExecute):
    if state["termination"] is True:
        return END
    else:
        return "execute"