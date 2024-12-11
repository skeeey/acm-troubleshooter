# coding: utf-8

import logging
from signatures.response import respond
from signatures.retriever import grade_relevant_nodes
from services.index import RAGService
from workflows.self_rag.state import copy_state

logger = logging.getLogger(__name__)

def retrieve_func(rag_svc: RAGService):
    def retrieve(state):
        current_state = copy_state(state)
        issue = current_state["issue"]
        sources = current_state["doc_sources"]
        retrieval_times = current_state["retrieval_times"]

        nodes = rag_svc.retrieve(query=issue, sources=sources)
        relevant_nodes = grade_relevant_nodes(nodes, issue)
        if len(relevant_nodes) == 0:
            logger.warning("no relevant nodes for issue: %s", issue)
            current_state["terminated"] = True
            current_state["response"] = "I have no idea for this issue."
            current_state["reasoning"] = "No similar docs are found."
            return current_state
        
        relevant_docs = []
        relevant_doc_names = []
        for node in relevant_nodes:
            relevant_docs.append(node.text)
            relevant_doc_names.append(node.metadata["filename"])

        current_state["relevant_docs"] = relevant_docs
        current_state["relevant_doc_names"] = relevant_doc_names
        current_state["retrieval_times"] = retrieval_times + 1
        return current_state

    return retrieve

def answer_func():    
    def answer(state):
        current_state = copy_state(state)
        documents = current_state["relevant_docs"]
        previous_resp = current_state["response"]
        issue = current_state["issue"]
        feedback = current_state["feedback"]
        
        result = respond(documents=documents, issue=issue,
                         previous_responses=previous_resp, user_feedback=feedback)
        
        current_state["response"] = result.response
        current_state["reasoning"] = result.reasoning
        return current_state

    return answer
