# coding: utf-8

import dspy
from llama_index.core.schema import NodeWithScore
from prompts.templates import PLANNER_NOTICES


class Convertor(dspy.Signature):
    """ Convert a question with contexts to a better version that is optimized for vectorstore retrieval.
    If the question is not related to ACM, return an empty string.
    """

    notices: str = dspy.InputField(desc="Notices for converting the question.")
    contexts: str = dspy.InputField(desc="Contexts for the question.", default="") 
    question: str = dspy.InputField()

    new_question: str = dspy.OutputField()

class Grader(dspy.Signature):
    """Assess whether an answer addresses / resolves a question. 
    Give a binary score 'yes' or 'no'. 'yes' means that the answer resolves the question.
    """
    
    question: str = dspy.InputField()
    answer: str = dspy.InputField()

    # reasoning: str = dspy.OutputField()
    binary_score: str = dspy.OutputField()

def convert_question(contexts: str, question: str, notices=PLANNER_NOTICES) -> str:
    convert = dspy.Predict(Convertor)
    response = convert(notices=notices, contexts=contexts, question=question)
    return response.new_question

# TODO score range?
def grade_relevant_nodes(nodes: list[NodeWithScore], question: str) -> list[NodeWithScore]:
    relevant_nodes = []
    
    for node in nodes:
        grade = dspy.Predict(Grader)
        response = grade(question=question, answer=node.text)
        if response.binary_score.startswith("yes"):
            relevant_nodes.append(node)
    
    return relevant_nodes
