# coding: utf-8

"""
The LLM calls
"""

import logging
import dspy
from llama_index.core.schema import NodeWithScore
from ollama import Client
from openai import OpenAI
from server.models.index import RelevantNode
from server.models.workflow import HistoryRecord
from server.prompts.signatures import Response, Convertor, Grader, Runbook, Squad
from server.prompts.templates import RESPONSE_NOTICES, CONVERTOR_NOTICES, RUNBOOK_TEMPLATE, SQUADS
from server.tools.common import count_tokens

logger = logging.getLogger(__name__)

def llm_call(model, base_url, api_key, system_prompt, user_prompt):
    if model.startswith("ollama/"):
        client = Client(host="http://localhost:11434")
        response = client.chat(
            model=model.removeprefix("ollama/"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )
        return response.message.content

    client = OpenAI(
        base_url=base_url,
        api_key=api_key,
    )
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        stream=False
    )
    return response.choices[0].message.content

# TODO (optimize) check the token size (> 40k) of the prompt to limit/compress (LLMLingua) the prompt
def respond(documents: list[str], query: str, history_records: list[HistoryRecord], notices=RESPONSE_NOTICES):
    resp = dspy.ChainOfThought(Response)
    result = resp(
        notices=notices,
        documents=documents,
        query=query,
        history_records=history_records,
    )
    logger.debug(result)
    return result

def size_prompt(documents: list[str], query: str, history_records: list[HistoryRecord], notices) -> int:
    histories = []
    for r in history_records:
        histories.append(r.role)
        histories.append(r.message)
    return count_tokens("\n".join(documents) + query + "\n" + "\n".join(histories) + notices)

def convert_question(contexts: str, query: str, notices=CONVERTOR_NOTICES) -> str:
    convert = dspy.Predict(Convertor)
    response = convert(notices=notices, contexts=contexts, query=query)
    return response.new_query

def grade_relevant_nodes(nodes: list[NodeWithScore], question: str, relevant_cutoff=5) -> list[RelevantNode]:
    if len(nodes) == 0:
        return []

    relevant_nodes = []
    for node in nodes:
        grade = dspy.ChainOfThought(Grader)
        response = grade(question=question, answer=node.text)
        score = response.score
        logger.debug("%s %d %s",
                        node.metadata["filename"], score, response.reasoning)
        if score < relevant_cutoff:
            logger.info("give up the node: %0.3f %s, (%d<%d) reasoning=%s",
                        node.score, node.metadata["filename"], score, relevant_cutoff, response.reasoning)
            continue

        relevant_nodes.append(RelevantNode(node=node, score=score))

    relevant_nodes.sort(key=lambda n: n.score, reverse=True)
    return relevant_nodes

def gen_runbook(context: str, template: str=RUNBOOK_TEMPLATE):
    runbook = dspy.ChainOfThought(Runbook)
    response = runbook(context=context, template=template)
    return response.runbook

def assign_squads(issue: str, squads: str=SQUADS):
    assign = dspy.ChainOfThought(Squad)
    response = assign(issue=issue, squads=squads)
    return response.assigned
