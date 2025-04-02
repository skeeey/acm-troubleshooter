# coding: utf-8

import dspy

class Planner(dspy.Signature):
    """Generate a troubleshooting plan for issues with Red Hat Advanced Cluster Management for Kubernetes (ACM or RHACM).
    """

    documents: str = dspy.InputField(desc="The relevant documents")
    notices: str = dspy.InputField(desc="Notices for generating the troubleshooting plan.")
    issue: str = dspy.InputField()

    plan: str = dspy.OutputField(desc="The troubleshooting plan for the given issue")

class Executor(dspy.Signature):
    """Execute the troubleshooting plan to find the cause of the issue.
    """

    plan: str = dspy.InputField(desc="The troubleshooting plan")
    rules: str = dspy.InputField(desc="The rules to convert a troubleshooting plan to executable commands")
    examples: str = dspy.InputField(desc="The examples for this task")
    hub_must_gather_dir: str = dspy.InputField(desc="The hub must-gather dir")
    spoke_must_gather_dir: str = dspy.InputField(desc="The spoke must-gather dir")

    issue_cause: str = dspy.OutputField(desc="The cause of the issue")


class Replan(dspy.Signature):
    """Generate a new plan for the issue based on the previous plan, execution results, and relevant documents.
    """

    issue: str = dspy.InputField()
    documents: str = dspy.InputField(desc="The relevant documents.")
    notices: str = dspy.InputField(desc="Notices for generating the new plan.")
    previous_plan: str = dspy.InputField(desc="The previous plan.")
    previous_execution_result: str = dspy.InputField(desc="The previous execution result.")
    
    new_plan: str = dspy.OutputField()
    termination: bool = dspy.OutputField()
