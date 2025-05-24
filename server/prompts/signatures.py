# coding: utf-8

import dspy
from server.models.workflow import HistoryRecord

class Response(dspy.Signature):
    """As an AI ACM assistant, you respond to the user's ACM query.
    """

    notices: str = dspy.InputField(desc="Notices for providing the response.")
    documents: list[str] = dspy.InputField(desc="The relevant documents.")
    history_records: list[HistoryRecord] = dspy.InputField(desc="The previous history records.", default=[])

    query: str = dspy.InputField()

    response: str = dspy.OutputField()

class Convertor(dspy.Signature):
    """ Convert a query with contexts to a better version that is optimized for vector store retrieval.
    """

    notices: str = dspy.InputField(desc="Notices for converting the query.")
    contexts: dict[str, str] = dspy.InputField(desc="Contexts for the query.", default={})
    query: str = dspy.InputField()

    new_query: str = dspy.OutputField()

class Grader(dspy.Signature):
    """Assess the relevance of the answer to the question. 
    Give a score from 0 to 10. 10 means most relevant and 0 means least relevant."
    """

    question: str = dspy.InputField()
    answer: str = dspy.InputField()

    score: int = dspy.OutputField(default=0)

class Runbook(dspy.Signature):
    """Refer to the context to write a runbook with the runbook template.
    """

    context: str = dspy.InputField()
    template: str = dspy.InputField(desc="The runbook template.")

    runbook: str = dspy.OutputField()

class Squad(dspy.Signature):
    """Assign the given issue to a suitable squads from the squad list.
    """

    issue: str = dspy.InputField()
    squads: str = dspy.InputField(desc="The list of squads")

    assigned: list[str] = dspy.OutputField(desc="The assigned squads")
