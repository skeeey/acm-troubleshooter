# coding: utf-8

import dspy
import logging
from llama_index.core.schema import NodeWithScore
from prompts.templates import CONVERTOR_NOTICES
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class RelevantNode(BaseModel):
    node: NodeWithScore
    score: int = 0

class Convertor(dspy.Signature):
    """ Convert a query with contexts to a better version that is optimized for vector store retrieval.
    """

    notices: str = dspy.InputField(desc="Notices for converting the query.")
    contexts: dict[str, str] = dspy.InputField(desc="Contexts for the query.", default={}) 
    query: str = dspy.InputField()

    new_query: str = dspy.OutputField()

class Grader(dspy.Signature):
    """Assess the relevance of the answer to the question. 
    Give a score from 0 to 10. 10 means most relevant and 0 means least relevant."
    """
    
    question: str = dspy.InputField()
    answer: str = dspy.InputField()

    # reasoning: str = dspy.OutputField()
    score: int = dspy.OutputField(default=0)

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
