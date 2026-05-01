import asyncio
import logging
from collections.abc import AsyncGenerator
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from v2.server.services.llm import LLMService, build_respond_messages
from v2.server.services.rag import RAGResult, RAGService
from v2.server.services.vector import VectorStoreService

logger = logging.getLogger(__name__)

RETRIEVAL_LIMIT = 3
RELEVANCE_CUTOFF = 5


class GraphState(TypedDict):
    query: str
    original_query: str
    doc_sources: list[str]
    history: list[dict]
    retrieved_docs: list[str]
    retrieved_refs: list[str]
    relevant_docs: list[str]
    relevant_refs: list[str]
    response: str
    retrieval_count: int


def _retrieve_node(vector_svc: VectorStoreService):
    async def retrieve(state: GraphState) -> dict:
        query = state["query"]
        doc_sources = state["doc_sources"]
        retrieval_count = state["retrieval_count"]

        nodes = await asyncio.to_thread(
            vector_svc.retrieve, query=query, sources=doc_sources,
        ) if doc_sources else []

        retrieved_docs = [node.text for node in nodes]
        retrieved_refs = [node.metadata.get("filelink", "") for node in nodes]

        logger.info(
            "retrieved %d docs for query: %s (attempt %d)",
            len(nodes), query[:80], retrieval_count + 1,
        )

        return {
            "retrieved_docs": retrieved_docs,
            "retrieved_refs": retrieved_refs,
            "retrieval_count": retrieval_count + 1,
        }

    return retrieve


def _grade_node(llm_svc: LLMService):
    async def grade(state: GraphState) -> dict:
        query = state["original_query"]
        retrieved_docs = state["retrieved_docs"]
        retrieved_refs = state["retrieved_refs"]

        scores = await asyncio.gather(
            *[llm_svc.grade(query, doc) for doc in retrieved_docs]
        )

        relevant_docs = []
        relevant_refs = []
        for doc, ref, score in zip(retrieved_docs, retrieved_refs, scores):
            if score >= RELEVANCE_CUTOFF:
                relevant_docs.append(doc)
                relevant_refs.append(ref)
            else:
                logger.info("filtered doc (score=%d < %d): %s", score, RELEVANCE_CUTOFF, ref[:80])

        logger.info("graded %d docs, %d relevant", len(retrieved_docs), len(relevant_docs))

        return {
            "relevant_docs": relevant_docs,
            "relevant_refs": relevant_refs,
        }

    return grade


def _convert_query_node(llm_svc: LLMService):
    async def convert_query(state: GraphState) -> dict:
        query = state["original_query"]

        new_query = await llm_svc.convert_query(query)

        logger.info("converted query: %s -> %s", query[:80], new_query[:80])
        return {"query": new_query if new_query else query}

    return convert_query


def _answer_node(llm_svc: LLMService):
    async def answer(state: GraphState) -> dict:
        relevant_docs = state["relevant_docs"]
        query = state["original_query"]
        history = state["history"]

        messages = build_respond_messages(
            documents=relevant_docs,
            query=query,
            history=history,
        )

        response = await llm_svc.complete(messages)

        return {"response": response}

    return answer


def _after_grade(state: GraphState) -> str:
    if state["relevant_docs"]:
        return "answer"

    if state["retrieval_count"] >= RETRIEVAL_LIMIT:
        logger.warning("retrieval limit reached (%d), answering with available docs", RETRIEVAL_LIMIT)
        return "answer"

    return "convert_query"


def build_graph(vector_svc: VectorStoreService, llm_svc: LLMService):
    workflow = StateGraph(GraphState)

    workflow.add_node("retrieve", _retrieve_node(vector_svc))
    workflow.add_node("grade", _grade_node(llm_svc))
    workflow.add_node("convert_query", _convert_query_node(llm_svc))
    workflow.add_node("answer", _answer_node(llm_svc))

    workflow.add_edge(START, "retrieve")
    workflow.add_edge("retrieve", "grade")
    workflow.add_conditional_edges("grade", _after_grade, {
        "answer": "answer",
        "convert_query": "convert_query",
    })
    workflow.add_edge("convert_query", "retrieve")
    workflow.add_edge("answer", END)

    return workflow.compile()


def _initial_state(query: str, history: list[dict], doc_sources: list[str]) -> GraphState:
    return GraphState(
        query=query,
        original_query=query,
        doc_sources=doc_sources,
        history=history,
        retrieved_docs=[],
        retrieved_refs=[],
        relevant_docs=[],
        relevant_refs=[],
        response="",
        retrieval_count=0,
    )


class SelfRAGService(RAGService):
    def __init__(self, vector_svc: VectorStoreService, llm_svc: LLMService):
        self.vector_svc = vector_svc
        self.llm_svc = llm_svc
        self.graph = build_graph(vector_svc, llm_svc)

    async def run(
        self,
        query: str,
        history: list[dict],
        doc_sources: list[str],
    ) -> RAGResult:
        state = _initial_state(query, history, doc_sources)
        result = await self.graph.ainvoke(state)
        return RAGResult(
            content=result["response"],
            references=list(set(result["relevant_refs"])),
        )

    async def stream(
        self,
        query: str,
        history: list[dict],
        doc_sources: list[str],
    ) -> AsyncGenerator[RAGResult, None]:
        state = _initial_state(query, history, doc_sources)

        # Run retrieve+grade loop to completion (non-streaming)
        retrieval_count = 0
        current_query = query
        relevant_docs = []
        relevant_refs = []

        while retrieval_count < RETRIEVAL_LIMIT:
            nodes = self.vector_svc.retrieve(
                query=current_query, sources=doc_sources,
            ) if doc_sources else []
            retrieval_count += 1

            retrieved_docs = [node.text for node in nodes]
            retrieved_refs = [node.metadata.get("filelink", "") for node in nodes]

            if retrieved_docs:
                scores = await asyncio.gather(
                    *[self.llm_svc.grade(query, doc) for doc in retrieved_docs]
                )
                for doc, ref, score in zip(retrieved_docs, retrieved_refs, scores):
                    if score >= RELEVANCE_CUTOFF:
                        relevant_docs.append(doc)
                        relevant_refs.append(ref)

            if relevant_docs:
                break

            current_query = await self.llm_svc.convert_query(query)
            if not current_query:
                current_query = query

        # Stream the answer
        messages = build_respond_messages(
            documents=relevant_docs,
            query=query,
            history=history,
        )

        async for chunk in self.llm_svc.stream(messages):
            yield RAGResult(content=chunk)

        yield RAGResult(content="", references=list(set(relevant_refs)))
