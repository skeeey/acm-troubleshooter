# coding: utf-8

import logging

logger = logging.getLogger(__name__)
retrieval_limit = 10

def distribute_issue(state):
    if len(state["plan"]) == 0:
        return "retrieve"
    return "transform"

def grade_documents(state):
    retrieval_times = state["retrieval_times"]
    if retrieval_times > retrieval_limit:
        logger.warning("retrieval limit reached for the issue: %s", state["issue"])
        return "limit exceed"

    # TODO evaluate the retrieved result 
    # score = state["score"]
    # if score == "no":
    #     return "useless"

    return "useful"
