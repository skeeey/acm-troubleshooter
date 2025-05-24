# coding: utf-8

"""
The self RAG workflow
"""

from langgraph.graph import END, StateGraph, START
from server.services.vector import VectorStoreIndex
from server.workflows.self_rag.state import GraphState
from server.workflows.self_rag.nodes import retrieve_func, answer_func
from server.workflows.self_rag.edges import dispatch

def build_graph(vector_store_svc: VectorStoreIndex):
    workflow = StateGraph(GraphState)

    workflow.add_node("retrieve", retrieve_func(vector_store_svc=vector_store_svc))
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
