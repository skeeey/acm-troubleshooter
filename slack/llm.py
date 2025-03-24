# coding: utf-8

import os
from dotenv import load_dotenv
from openai import OpenAI
from slack.prompt import system_prompt, squad_template

# load envs
load_dotenv()

def openai_call(system_prompt, user_prompt):
    client = OpenAI(
        api_key=os.getenv("LM_API_KEY"),
        base_url=os.getenv("LM_API_BASE"),
    )

    response = client.chat.completions.create(
        model=os.getenv("LM_MODEL"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        stream=False
    )
    return response.choices[0].message.content
