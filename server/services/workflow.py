
# coding: utf-8

# pylint: disable=missing-class-docstring

"""
The service to run workflow
"""

import logging
from server.models.db import DocumentView
from server.models.workflow import HistoryRecord
from server.services.vector import VectorStoreService
from server.workflows.self_rag_graph import build_graph
from server.workflows.self_rag.state import new_state

logger = logging.getLogger(__name__)

class WorkflowService:
    def __init__(self, vector_store_svc: VectorStoreService):
        self.resp_graph = build_graph(vector_store_svc=vector_store_svc)
        logger.info("Workflow service is initialized")

    def run(self, query: str, histories: list[HistoryRecord], docs: list[DocumentView], recursion_limit=50):
        # TODO select the appropriate docs
        doc_sources = []
        for doc in docs:
            doc_sources.append(doc.source)

        return self.resp_graph.invoke(
            new_state(doc_sources=doc_sources, query=query, history_records=histories),
            config={"recursion_limit": recursion_limit},
        )
