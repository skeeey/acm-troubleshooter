# coding: utf-8

from typing_extensions import TypedDict

class GraphState(TypedDict):
    issue: str
    
    plan: str
    results: list[str]

    relevant_docs: list[str]

    reasoning: str
    hub_commands: list[str]
    spoke_commands: list[str]
    
    retrieval_times: int

def new_state(state: GraphState) -> GraphState:
    return GraphState(
        issue=state["issue"],
        plan=state["plan"],
        results=state["results"],
        relevant_docs=state["relevant_docs"],
        reasoning=state["reasoning"],
        hub_commands=state["hub_commands"],
        spoke_commands=state["spoke_commands"],
        retrieval_times=state["retrieval_times"]
    )

def init_state(issue: str, plan="", results=[]) -> GraphState:
    return GraphState(
        issue=issue,
        plan=plan,
        results=results,
        relevant_docs=[],
        reasoning="",
        hub_commands="",
        spoke_commands="",
        retrieval_times=0
    )