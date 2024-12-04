# coding: utf-8

import dspy
import logging
from server.models import LLMConfig, RetrievalConfig
from workflows.diagnosis_graph import build_graph
from workflows.diagnosis.state import init_state

logger = logging.getLogger(__name__)

class DiagnosisService:
    def __init__(self, rag_svc):
        self.graph = build_graph(rag_svc=rag_svc)
    
    def diagnose(self, mcfg: LLMConfig,  rcfg: RetrievalConfig, issue: str, plan="", results="", recursion_limit=50):
        # llm settings
        lm = dspy.LM(model=mcfg.model, api_base=mcfg.api_base, api_key=mcfg.api_key)
        dspy.configure(lm=lm)

        state = init_state(
            issue=issue,
            sources=rcfg.doc_sources,
            plan=plan,
            user_inputs=results)
        return self.graph.invoke(state, config={"recursion_limit": recursion_limit})
