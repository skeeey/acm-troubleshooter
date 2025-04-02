# coding: utf-8

import click
import os
from dotenv import load_dotenv
from jira import JIRA
from llama_index.core.schema import Document
from tools.llm import llm_call

load_dotenv()

# default llm settings
llm_model=os.getenv("LM_MODEL")
llm_api_base=os.getenv("LM_API_BASE")
llm_api_key=os.getenv("LM_API_KEY")

# jira token
token=os.getenv("JIRA_TOKEN")

# prompts
system_prompt = "You are a Red Hat Advanced Cluster Management for Kubernetes (ACM or RHACM) assistant."
user_prompt = """
The following content is about an ACM issue, please 
- Summarize the issue
- Give the issue's symptom
- Give the troubleshooting steps for this issue
- Give the solution of this issue

Here is the content

{text}
"""

def load_jira_data(issues) -> list[Document]:
    docs = []

    for issue in issues:
        affects_versions = []
        fix_versions = []
        components = []
        all_comments = ""

        if issue.fields.versions:
            for version in issue.fields.versions:
                affects_versions.append(version.name)

        if issue.raw["fields"]["fixVersions"]:
            for fix_version in issue.raw["fields"]["fixVersions"]:
                fix_versions.append(fix_version["name"])

        if issue.raw["fields"]["components"]:
            for component in issue.raw["fields"]["components"]:
                components.append(component["name"])

        if issue.fields.comment.comments:
            comments = []
            for comment in issue.fields.comment.comments:
                comments.append(comment.body)
            all_comments = "\n".join(comments)

        docs.append(Document(
                text=f"{issue.fields.summary} \n {issue.fields.description} \n {all_comments}",
                extra_info={
                    "id": issue.key,
                    "labels": issue.fields.labels,
                    "components": components,
                    "status": issue.fields.status.name,
                    "assignee": issue.fields.assignee.emailAddress,
                    "reporter": issue.fields.reporter.emailAddress,
                    "project": issue.fields.project.name,
                    "issue_type": issue.fields.issuetype.name,
                    "affects_versions": affects_versions,
                    "fix_versions": fix_versions,
                },
        ))

    return docs

def query_jira_issues(api_token, query):
    options = {
        "server": "https://issues.redhat.com",
        "headers": {"Authorization": f"Bearer {api_token}"},
    }
    jira = JIRA(options=options)
    return jira.search_issues(query)

@click.command()
@click.argument("issue")
def main(issue):
    issues = query_jira_issues(api_token=token, query=f"key={issue}")
    all_comments = ""
    for issue in issues:
        if issue.fields.comment.comments:
            comments = []
            for comment in issue.fields.comment.comments:
                comments.append(comment.body)
            all_comments = "\n".join(comments)
    response = llm_call(
        llm_model,
        llm_api_base,
        llm_api_key,
        system_prompt,
        user_prompt.format(text=f"{issue.fields.summary} \n {issue.fields.description} \n {all_comments}"),
    )
    print(response)

if __name__ == "__main__":
    main()
