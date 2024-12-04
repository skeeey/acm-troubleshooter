# coding: utf-8

import logging
import dspy
from signatures.diagnosis import Planner, Query, Replan
from prompts.templates import PLANNER_NOTICES
from services.index import RAGService
from workflows.diagnosis.state import new_state

logger = logging.getLogger(__name__)

def transform_func():
    def transform(state):
        current_state = new_state(state)
        issue = current_state["issue"]
        plan = current_state["plan"]
        results = current_state["user_inputs"]

        logger.info("generate a rag query for the issue: %s", issue)
        if len(plan) == 0:
            # no plan was provided yet, use the issue as the query directly
            return current_state

        query = dspy.ChainOfThought(Query)
        query_response = query(
                issue=issue,
                previous_plan=plan,
                previous_execution_results=results
        )
        logger.debug(query_response)

        current_state["issue"] = query_response.query
        return current_state
    
    return transform

def retrieve_func(rag_svc: RAGService):
    def retrieve(state):
        current_state = new_state(state)
        query = current_state["issue"]
        sources = current_state["sources"]
        retrieval_times = current_state["retrieval_times"]

        relevant_nodes = rag_svc.retrieve(query=query, sources=sources)
        if len(relevant_nodes) == 0:
            logger.warning("no relevant nodes retrieved")
            current_state["terminated"] = True
            current_state["plan"] = "There is no plan for this issue."
            current_state["reasoning"] = "No similar docs are found."
            return current_state
        
        relevant_docs = []
        for node in relevant_nodes:
            relevant_docs.append(node.text)

        current_state["relevant_docs"] = relevant_docs
        current_state["retrieval_times"] = retrieval_times + 1
        return current_state

    return retrieve

def generate_func():    
    def generate(state):
        current_state = new_state(state)
        issue = current_state["issue"]
        plan = current_state["plan"]
        results = current_state["user_inputs"]
        documents = current_state["relevant_docs"]
        
        if len(plan) == 0:
            logger.info("generate the plan for the issue: %s", issue)
            # no plan was provided yet, give an initial plan
            gen_plan = dspy.ChainOfThought(Planner)
            gen_plan_response = gen_plan(
                documents=documents,
                notices=PLANNER_NOTICES,
                issue=issue,
            )
            logger.debug(gen_plan_response)

            current_state["plan"] = gen_plan_response.plan
            current_state["reasoning"] = gen_plan_response.reasoning
            current_state["hub_commands"] = gen_plan_response.hub_commands
            current_state["spoke_commands"] = gen_plan_response.spoke_commands
            return current_state
        
        replan = dspy.ChainOfThought(Replan)
        replan_response = replan(
            issue=issue,
            documents=documents,
            notices=PLANNER_NOTICES,
            previous_plan=plan,
            previous_execution_results=results,
        )
        logger.debug(replan_response)
        current_state["plan"] = replan_response.new_plan
        current_state["reasoning"] = replan_response.reasoning
        current_state["hub_commands"] = replan_response.hub_commands
        current_state["spoke_commands"] = replan_response.spoke_commands
        return current_state

    return generate
