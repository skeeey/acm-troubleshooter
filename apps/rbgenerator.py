# coding: utf-8

import click
import os
from dotenv import load_dotenv
# from llama_index.llms.groq import Groq
from llama_index.llms.ollama import Ollama
from llama_index.core.llms import ChatMessage
from tools.loader import query_jira_issues

load_dotenv()

@click.command()
@click.argument("issue")
def main(issue):
    token=os.getenv("JIRA_TOKEN")
    
    issues = query_jira_issues(api_token=token, query=f"key={issue}")
    
    all_comments = ""
    for issue in issues:
        if issue.fields.comment.comments:
            comments = []
            for comment in issue.fields.comment.comments:
                comments.append(comment.body)
            all_comments = "\n".join(comments)
    
    text=f"{issue.fields.summary} \n {issue.fields.description} \n {all_comments}"

    # llm = Groq(model="llama-3.1-70b-versatile", api_key=os.getenv("GROQ_API_KEY"))
    llm = Ollama(model="qwen2.5:14b", request_timeout=600.0)

    messages = [
        ChatMessage(
            role="system",
            content="You are a Red Hat Advanced Cluster Management for Kubernetes (ACM or RHACM) assistant."
        ),
        ChatMessage(
            role="user",
            content=f"""
The following content is about an ACM issue, please 
- Summarize the issue
- Give the issue's symptom
- Give the troubleshooting steps for this issue
- Give the solution of this issue

Here is the content

{text}

"""),
]
    print(llm.chat(messages))

if __name__ == "__main__":
    main()