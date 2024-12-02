# coding: utf-8

import dspy

class Planner(dspy.Signature):
    """Generate a troubleshooting plan for issues with Red Hat Advanced Cluster Management for Kubernetes (ACM or RHACM).
    """

    documents: list[str] = dspy.InputField(desc="The relevant documents")
    notices: str = dspy.InputField(desc="Notices for generating the troubleshooting plan.")
    issue: str = dspy.InputField()

    plan: str = dspy.OutputField(desc="The troubleshooting plan for the given issue")
    hub_commands: list[str] = dspy.OutputField(desc="Optional, the executable commands that are run on the hub.")
    spoke_commands: list[str] = dspy.OutputField(desc="Optional, the executable commands that are run on the spoke.")

class Query(dspy.Signature):
    """Generate a query to further retrieve the relevant documents from vector store based on the previous plan and execution results.
    """

    issue: str = dspy.InputField()
    previous_plan: str = dspy.InputField(desc="The previous plan.")
    previous_execution_results: list[str] = dspy.InputField(desc="The previous execution results.")

    query: str = dspy.OutputField(desc="")

class Replan(dspy.Signature):
    """Generate a new plan for the issue based on the previous plan, execution results, and relevant documents.
    """

    issue: str = dspy.InputField()
    documents: list[str] = dspy.InputField(desc="The relevant documents.")
    notices: str = dspy.InputField(desc="Notices for generating the new plan.")
    previous_plan: str = dspy.InputField(desc="The previous plan.")
    previous_execution_results: str = dspy.InputField(desc="The previous execution results.")
    
    new_plan: str = dspy.OutputField()
    hub_commands: list[str] = dspy.OutputField(desc="Optional, the executable commands that are run on the hub.")
    spoke_commands: list[str] = dspy.OutputField(desc="Optional, the executable commands that are run on the spoke.")
