# coding: utf-8

# pylint: disable=missing-class-docstring

"""
The service to invoke the LLM
"""

import dspy
import logging
from models.contexts import LLMConfig, RetrievalConfig
from models.chat import Record
from services.storage import Response
from workflows.self_rag_graph import build_self_rag_graph
from workflows.self_rag.state import new_state

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self, rag_svc):
        self.resp_graph = build_self_rag_graph(rag_svc=rag_svc)

    def response(self, mcfg: LLMConfig, rcfg: RetrievalConfig,
                 query: str, history_resps: list[Response], recursion_limit=50):
        lm = dspy.LM(model=mcfg.model, api_base=mcfg.api_base, api_key=mcfg.api_key)
        dspy.configure(lm=lm)

        history_records = []
        for resp in history_resps:
            history_records.append(Record(role="user", message=resp.user_query))
            history_records.append(Record(role="assistant", message=resp.asst_resp))

        return self.resp_graph.invoke(
            new_state(doc_sources=rcfg.doc_sources, query=query, history_records=history_records),
            config={"recursion_limit": recursion_limit},
        )
