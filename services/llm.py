# coding: utf-8

import dspy
import logging
from server.models import LLMConfig, RetrievalConfig
from workflows.self_rag_graph import build_self_rag_graph
from workflows.self_rag.state import new_state

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self, rag_svc):
        self.resp_graph = build_self_rag_graph(rag_svc=rag_svc)
        # self.diagnosis_graph = build_graph(rag_svc=rag_svc)

    def response(self, mcfg: LLMConfig,  rcfg: RetrievalConfig,
                 issue: str, last_asst_resp="", feedback="",
                 recursion_limit=50):
        # llm settings
        lm = dspy.LM(model=mcfg.model, api_base=mcfg.api_base, api_key=mcfg.api_key)
        dspy.configure(lm=lm)

        state = new_state(
            doc_sources=rcfg.doc_sources,
            issue=issue,
            response=last_asst_resp,
            feedback=feedback,
        )
        return self.resp_graph.invoke(state, config={"recursion_limit": recursion_limit})
    
    # def diagnose(self, mcfg: LLMConfig,  rcfg: RetrievalConfig, issue: str, plan="", results="", recursion_limit=50):
    #     # llm settings
    #     lm = dspy.LM(model=mcfg.model, api_base=mcfg.api_base, api_key=mcfg.api_key)
    #     dspy.configure(lm=lm)

    #     state = init_state(
    #         issue=issue,
    #         sources=rcfg.doc_sources,
    #         plan=plan,
    #         user_inputs=results)
    #     return self.diagnosis_graph.invoke(state, config={"recursion_limit": recursion_limit})
