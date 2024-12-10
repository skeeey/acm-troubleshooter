# coding: utf-8

import logging

logger = logging.getLogger(__name__)
retrieval_limit = 10

def dispatch(state):
    terminated = state["terminated"]
    if terminated:
        return "terminated"
    
    retrieval_times = state["retrieval_times"]
    if retrieval_times > retrieval_limit:
        logger.warning("retrieval limit reached for the issue: %s", state["issue"])
        return "terminated"
    
    #TODO do we need to retrieve again?

    return "continue"
