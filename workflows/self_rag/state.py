# coding: utf-8

from typing_extensions import TypedDict
from models.chat import Record

class GraphState(TypedDict):
    # docs
    doc_sources: list[str]
    relevant_docs: list[str]
    relevant_doc_names: list[str]

    # history records (input)
    history_records: list[Record] 
    
    # from user (input)
    query: str

    # from llm (output)
    response: str
    reasoning: str

    # flags
    retrieval_times: int
    terminated: bool

def copy_state(state: GraphState) -> GraphState:
    return GraphState(
        doc_sources=state["doc_sources"],
        relevant_docs=state["relevant_docs"],
        relevant_doc_names=state["relevant_doc_names"],
        history_records=state["history_records"],
        query=state["query"],
        response=state["response"],
        reasoning=state["reasoning"],
        retrieval_times=state["retrieval_times"],
        terminated=state["terminated"],
    )

def new_state(doc_sources: list[str], query: str, history_records: list[Record]) -> GraphState:
    return GraphState(
        doc_sources=doc_sources,
        relevant_docs=[],
        relevant_doc_names=[],
        history_records=history_records,
        query=query,
        response="",
        reasoning="",
        retrieval_times=0,
        terminated=False,
    )
