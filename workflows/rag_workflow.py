# coding: utf-8

from langgraph.graph import END, StateGraph, START
from services.index import RAGService
from workflows.rag.state import GraphState
from workflows.rag.nodes import transform_func, retrieve_func, generate_func
from workflows.rag.edges import grade_documents

def build_graph(rag_svc: RAGService):
    workflow = StateGraph(GraphState)

    workflow.add_node("transform", transform_func())
    workflow.add_node("retrieve", retrieve_func(rag_svc=rag_svc))
    workflow.add_node("generate", generate_func())

    # Build graph
    workflow.add_edge(START, "transform")
    workflow.add_edge("transform", "retrieve")
    workflow.add_conditional_edges(
        "retrieve",
        grade_documents,
        {
            "useful": "generate",
            "useless": "transform",
            "limit exceed": END,
        },
    )
    workflow.add_edge("generate", END)

    # Compile
    return workflow.compile()
