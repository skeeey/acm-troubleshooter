# coding: utf-8

import dspy

class Response(dspy.Signature):
    """Provide a response for an ACM issue.
    """

    documents: list[str] = dspy.InputField(desc="The relevant documents")
    notices: str = dspy.InputField(desc="Notices for providing the response.")
    issue: str = dspy.InputField()

    response: str = dspy.OutputField(desc="The response for the given issue")
    # hub_commands: list[str] = dspy.OutputField(desc="Optional, the executable commands that are run on the hub.")
    # spoke_commands: list[str] = dspy.OutputField(desc="Optional, the executable commands that are run on the spoke.")

class ResponseWithContext(dspy.Signature):
    """Provide a response for the ACM issue based on the previous responses, user feedback, and relevant documents.
    """

    documents: list[str] = dspy.InputField(desc="The relevant documents.")
    notices: str = dspy.InputField(desc="Notices for providing the response.")
    previous_responses: str = dspy.InputField(desc="The previous responses.")
    issue: str = dspy.InputField()
    user_feedback: str = dspy.InputField(desc="The user feedback.")
    
    response: str = dspy.OutputField()
    # hub_commands: list[str] = dspy.OutputField(desc="Optional, the executable commands that are run on the hub.")
    # spoke_commands: list[str] = dspy.OutputField(desc="Optional, the executable commands that are run on the spoke.")
