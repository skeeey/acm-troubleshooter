# coding: utf-8

import dspy
import logging
from llama_index.core.schema import NodeWithScore

logger = logging.getLogger(__name__)

class Grader(dspy.Signature):
    """Assess whether an answer addresses / resolves a question. 
    Give a binary score 'yes' or 'no'. 'yes' means that the answer resolves the question.
    """
    
    question: str = dspy.InputField()
    answer: str = dspy.InputField()

    # reasoning: str = dspy.OutputField()
    binary_score: str = dspy.OutputField()

# TODO score range?
def grade_relevant_nodes(nodes: list[NodeWithScore], question: str) -> list[NodeWithScore]:
    relevant_nodes = []
    
    for node in nodes:
        grade = dspy.Predict(Grader)
        response = grade(question=question, answer=node.text)
        if response.binary_score.startswith("yes"):
            relevant_nodes.append(node)
    
    return relevant_nodes

