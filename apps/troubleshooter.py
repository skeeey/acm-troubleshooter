# coding: utf-8

import os
import click
import dspy
import logging
from dotenv import load_dotenv
from graph.workflow import build_graph
from tools.loader import load_runbooks
from prompts.templates import DSPY_EXECUTOR_RULES

load_dotenv()

# log settings
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_FORMAT = "%(levelname)s: [%(asctime)s, %(module)s, line:%(lineno)d] %(message)s"

logging.basicConfig(level=logging.WARNING, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
logger = logging.getLogger(__name__)

lm = dspy.LM('llama-3.1-70b-versatile', api_base='https://api.groq.com/openai/v1', api_key=os.getenv("GROQ_API_KEY"))
dspy.configure(lm=lm)

@click.command()
@click.option("--runbooks", required=True, type=click.Path(file_okay=True, dir_okay=True, exists=True), help="the path of runbooks")
@click.option("--hub-mg", type=click.Path(file_okay=False, dir_okay=True, exists=True), help="the path of hub must-gather")
@click.option("--cluster-mg", type=click.Path(file_okay=False, dir_okay=True, exists=True), help="the path of managed cluster must-gather")
@click.option("--executor-rules", type=click.STRING, help="the rules of executing commands")
@click.option("--interactive", is_flag=True, default=False, help="interactive mode")
@click.argument("issue")
def main(runbooks, hub_mg, cluster_mg, executor_rules, interactive, issue):
    if cluster_mg is None:
        cluster_mg = hub_mg
    
    if executor_rules is None or not executor_rules.strip():
        executor_rules = DSPY_EXECUTOR_RULES

    if interactive:
        print("TODO interactive")

    documents = load_runbooks(runbooks)
    graph = build_graph(
        documents=documents,
        hub_must_gather_dir=hub_mg,
        spoke_must_gather_dir=cluster_mg,
        executor_rules=executor_rules,
    )
    graph.invoke({"issue": issue}, config={"recursion_limit": 50})

if __name__ == "__main__":
    main()
