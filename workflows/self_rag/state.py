# coding: utf-8

from typing_extensions import TypedDict

class GraphState(TypedDict):
    # docs
    doc_sources: list[str]
    relevant_docs: list[str]
    relevant_doc_names: list[str]
    
    # from user
    issue: str
    feedback: str

    # from llm
    response: str
    reasoning: str
    # TODO get the commands from response
    # hub_commands: list[str]
    # spoke_commands: list[str]

    # flags
    retrieval_times: int
    terminated: bool

def copy_state(state: GraphState) -> GraphState:
    return GraphState(
        doc_sources=state["doc_sources"],
        relevant_docs=state["relevant_docs"],
        relevant_doc_names=state["relevant_doc_names"],
        issue=state["issue"],
        feedback=state["feedback"],
        response=state["response"],
        reasoning=state["reasoning"],
        retrieval_times=state["retrieval_times"],
        terminated=state["terminated"],
    )

def new_state(doc_sources: list[str], issue: str, response: str, feedback: str) -> GraphState:
    return GraphState(
        doc_sources=doc_sources,
        relevant_docs=[],
        relevant_doc_names=[],
        issue=issue,
        feedback=feedback,
        response=response,
        reasoning="",
        retrieval_times=0,
        terminated=False,
    )
