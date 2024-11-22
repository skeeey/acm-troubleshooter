# coding: utf-8

import logging
from workflows.rag_workflow import build_graph
from workflows.rag.state import init_state

logger = logging.getLogger(__name__)

class DiagnosisService:
    def __init__(self, rag_svc):
        self.graph = build_graph(rag_svc=rag_svc)
    
    def diagnose(self, issue, plan="", results=[], recursion_limit=50):
        state = init_state(issue=issue, plan=plan, results=results)
        return self.graph.invoke(state, config={"recursion_limit": recursion_limit})
