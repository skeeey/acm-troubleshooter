# coding: utf-8

import os
from dotenv import load_dotenv
from openai import OpenAI
from ollama import Client

# load envs
load_dotenv()

def llm_call(model, base_url, api_key, system_prompt, user_prompt):
    # model=os.getenv("LM_MODEL")

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
        api_key=api_key,
        base_url=base_url,
        # api_key=os.getenv("LM_API_KEY"),
        # base_url=os.getenv("LM_API_BASE"),
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
