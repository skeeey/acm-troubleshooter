from langgraph.graph import END, StateGraph, START
from graph.state import StepExecute
from graph.nodes import plan_func, execute_func, replan_func
from graph.edges import should_end

def build_graph(documents, hub_must_gather_dir, spoke_must_gather_dir):
    workflow = StateGraph(StepExecute)

    # Nodes
    workflow.add_node("planer", plan_func(documents))
    workflow.add_node("execute", execute_func(hub_must_gather_dir, spoke_must_gather_dir))
    workflow.add_node("replan", replan_func(documents))

    # Edges
    workflow.add_edge(START, "planer")
    workflow.add_edge("planer", "execute")
    workflow.add_edge("execute", "replan")
    workflow.add_conditional_edges("replan", should_end, ["execute", END])

    # Compile
    return workflow.compile()