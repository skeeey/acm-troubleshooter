# coding: utf-8

import os
import dspy
from dotenv import load_dotenv
from openai import OpenAI

# load envs
load_dotenv()

def dspy_call():
    lm = dspy.LM(
        model=os.getenv("LM_MODEL"),
        api_key=os.getenv("LM_API_KEY"),
        api_base=os.getenv("LM_API_BASE"),
        launch_kwargs={"timeout": 300}
    )
    dspy.configure(lm=lm)

    math = dspy.ChainOfThought("question -> answer: float")
    result = math(question="Two dice are tossed. What is the probability that the sum equals two?")
    print(result)

def openai_call():
    client = OpenAI(
        api_key=os.getenv("LM_API_KEY"),
        base_url=os.getenv("LM_API_BASE"),
    )
    response = client.chat.completions.create(
        model=os.getenv("LM_MODEL"),
        messages=[
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Two dice are tossed. What is the probability that the sum equals two?"},
        ],
        stream=False
    )
    print(response.choices[0].message.content)

if __name__ == "__main__":
    openai_call()
