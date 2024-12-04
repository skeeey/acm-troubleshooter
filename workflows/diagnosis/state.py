# coding: utf-8

from typing_extensions import TypedDict

class GraphState(TypedDict):
    sources: list[str]
    issue: str
    plan: str
    user_inputs: str
    relevant_docs: list[str]
    reasoning: str
    hub_commands: list[str]
    spoke_commands: list[str]
    retrieval_times: int
    terminated: bool

def new_state(state: GraphState) -> GraphState:
    return GraphState(
        sources=state["sources"],
        issue=state["issue"],
        plan=state["plan"],
        user_inputs=state["user_inputs"],
        relevant_docs=state["relevant_docs"],
        reasoning=state["reasoning"],
        hub_commands=state["hub_commands"],
        spoke_commands=state["spoke_commands"],
        retrieval_times=state["retrieval_times"],
        terminated=state["terminated"],
    )

def init_state(issue: str, sources: list[str], plan="", user_inputs="") -> GraphState:
    return GraphState(
        sources=sources,
        issue=issue,
        plan=plan,
        user_inputs=user_inputs,
        relevant_docs=[],
        reasoning="",
        hub_commands=[],
        spoke_commands=[],
        retrieval_times=0,
        terminated=False,
    )