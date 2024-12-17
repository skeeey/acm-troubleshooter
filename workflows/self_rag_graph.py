# coding: utf-8

from langgraph.graph import END, StateGraph, START
from services.index import RAGService
from workflows.self_rag.state import GraphState
from workflows.self_rag.nodes import retrieve_func, answer_func
from workflows.self_rag.edges import dispatch

def build_self_rag_graph(rag_svc: RAGService):
    workflow = StateGraph(GraphState)

    workflow.add_node("retrieve", retrieve_func(rag_svc=rag_svc))
    workflow.add_node("answer", answer_func())

    # Build graph
    workflow.add_edge(START, "retrieve")
    workflow.add_conditional_edges(
        "retrieve",
        dispatch,
        {
            "continue": "answer",
            "terminated": END,
        },
    )
    workflow.add_edge("answer", END)

    # Compile
    return workflow.compile()
