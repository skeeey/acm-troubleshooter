# coding: utf-8

import logging
import dspy
from prompts.templates import PLANNER_NOTICES

logger = logging.getLogger(__name__)

class Response(dspy.Signature):
    """Provide a response for the ACM issue based on the previous responses, user feedback, and relevant documents.
    """

    notices: str = dspy.InputField(desc="Notices for providing the response.")
    documents: list[str] = dspy.InputField(desc="The relevant documents.")
    issue: str = dspy.InputField()

    previous_responses: str = dspy.InputField(desc="The previous responses.", default="")
    user_feedback: str = dspy.InputField(desc="The user feedback.", default="")
    
    response: str = dspy.OutputField()

def respond(documents: list[str], issue: str, previous_responses = "", user_feedback="", notices=PLANNER_NOTICES):
    resp = dspy.ChainOfThought(Response)
    result = resp(
        notices=notices,
        documents=documents,
        issue=issue,
        previous_responses=previous_responses,
        user_feedback=user_feedback,
    )
    logger.debug(result)
    return result