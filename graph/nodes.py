import logging
import dspy
from graph.signatures import Planner, Executor, Replan
from graph.state import new_status
from prompts.templates import DSPY_PLANNER_NOTICES, DSPY_EXECUTOR_RULES, DSPY_EXECUTOR_EXAMPLES, DSPY_REPLAN_NOTICES
from tools.cmd_executor import execute_commands

logger = logging.getLogger(__name__)

def plan_func(documents):
    def plan(state):
        issue = state["issue"]
        print(f"🤖 Generate troubleshooting plan for the issue\n {issue}")
        gen_plan = dspy.ChainOfThought(Planner)
        gen_plan_response = gen_plan(
            documents=documents,
            notices=DSPY_PLANNER_NOTICES,
            issue=issue,
        )
        logger.debug(gen_plan_response)
        plan = gen_plan_response.plan
        print(f"📋 Troubleshooting Plan 📋\n{plan}")
        return new_status(issue=issue, plan=plan)
    return plan

def execute_func(hub_must_gather_dir, spoke_must_gather_dir):
    def execute(state):
        print(f"🤖 Executing troubleshooting plan ...")
        issue = state["issue"]
        plan = state["plan"]
        exe_plan = dspy.ReAct(Executor, tools=[execute_commands])
        exe_plan_response = exe_plan(
            plan=plan,
            rules=DSPY_EXECUTOR_RULES,
            examples=DSPY_EXECUTOR_EXAMPLES,
            hub_must_gather_dir=hub_must_gather_dir,
            spoke_must_gather_dir=spoke_must_gather_dir,
        )
        logger.debug(exe_plan_response)
        issue_cause = exe_plan_response.issue_cause
        return new_status(issue=issue, plan=plan, result=issue_cause)
    return execute

def replan_func(documents):
    def replan(state):
        issue = state["issue"]
        plan = state["plan"]
        result = state["result"]

        print(f"💡 Issue cause 💡\n{result}")
        print(f"🤖 Replanning or finding issue solution ...")
        replan = dspy.ChainOfThought(Replan)
        replan_response = replan(
            issue=issue,
            documents=documents,
            notices=DSPY_REPLAN_NOTICES,
            previous_plan=plan,
            previous_execution_result=result,
        )
        logger.debug(replan_response)
        next_plan = replan_response.new_plan
        termination = replan_response.termination
        if termination:
            print(f"✨ Solution ✨\n{next_plan}")
            return new_status(termination=True) 
        
        print(f"📋 New troubleshooting Plan 📋\n{next_plan}")
        return new_status(issue=issue, plan=next_plan)
    return replan