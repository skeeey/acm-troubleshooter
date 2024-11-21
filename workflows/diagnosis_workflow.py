# coding: utf-8

from langgraph.graph import END, StateGraph, START
from tools.cmd_executor import execute_commands_func
from workflows.diagnosis.state import StepExecute
from workflows.diagnosis.nodes import plan_func, execute_func, replan_func
from workflows.diagnosis.edges import should_end

def build_graph(documents, hub_mg_dir, spoke_mg_dir, executor_rules, interactive):
    workflow = StateGraph(StepExecute)

    # Nodes
    workflow.add_node("planer", plan_func(documents, interactive))
    workflow.add_node("execute", execute_func(hub_mg_dir, spoke_mg_dir, executor_rules, execute_commands_func(interactive)))
    workflow.add_node("replan", replan_func(documents, interactive))

    # Edges
    workflow.add_edge(START, "planer")
    workflow.add_edge("planer", "execute")
    workflow.add_edge("execute", "replan")
    workflow.add_conditional_edges("replan", should_end, ["execute", END])

    # Compile
    return workflow.compile()
