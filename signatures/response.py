# coding: utf-8

"""
The response dspy signatures
"""

import logging
import dspy
from models.chat import Record
from prompts.templates import RESPONSE_NOTICES
from tools.common import count_tokens

logger = logging.getLogger(__name__)

class Response(dspy.Signature):
    """As an AI ACM assistant, you respond to the user's ACM query.
    """

    notices: str = dspy.InputField(desc="Notices for providing the response.")
    documents: list[str] = dspy.InputField(desc="The relevant documents.")
    history_records: list[Record] = dspy.InputField(desc="The previous history records.", default=[])

    query: str = dspy.InputField()

    response: str = dspy.OutputField()

# TODO (optimize) check the token size (> 40k) of the prompt to limit/compress (LLMLingua) the prompt
def respond(documents: list[str], query: str, history_records: list[Record], notices=RESPONSE_NOTICES):
    resp = dspy.ChainOfThought(Response)
    result = resp(
        notices=notices,
        documents=documents,
        query=query,
        history_records=history_records,
    )
    logger.debug(result)
    return result

def size_prompt(documents: list[str], query: str, history_records: list[Record], notices) -> int:
    histories = []
    for r in history_records:
        histories.append(r.role)
        histories.append(r.message)
    return count_tokens("\n".join(documents) + query + "\n" + "\n".join(histories) + notices)
