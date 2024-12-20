# coding: utf-8

import logging
from signatures.response import respond
from signatures.retriever import convert_question
from services.index import RAGService
from workflows.self_rag.state import copy_state
from tools.common import is_empty

logger = logging.getLogger(__name__)

def retrieve_func(rag_svc: RAGService):
    def retrieve(state):
        current_state = copy_state(state)

        sources = current_state["doc_sources"]
        retrieval_times = current_state["retrieval_times"]
        query = current_state["query"]

        nodes = rag_svc.retrieve(query=query, sources=sources)
        if len(nodes) == 0:
            # TODO may need contexts (current_state["history_records"]) for new query
            new_query = convert_question(contexts={}, query=query)
            logger.info("no relevant nodes for query: %s, generate a new query: %s", query, new_query)
            nodes = rag_svc.retrieve(query=new_query, sources=sources)
            if len(nodes) == 0:
                logger.warning("no relevant nodes for query: %s", new_query)
                current_state["terminated"] = True
                current_state["response"] = "I have no idea for this issue."
                current_state["reasoning"] = "No similar docs are found."
                return current_state
        
        relevant_docs = []
        relevant_doc_names = []
        for node in nodes:
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
        query = current_state["query"]
        history_records = current_state["history_records"]
        
        # TODO (optimize) check the token size of the documents and history to limit the context 
        result = respond(documents=documents, query=query, history_records=history_records)
        
        current_state["response"] = result.response
        current_state["reasoning"] = result.reasoning
        return current_state

    return answer
