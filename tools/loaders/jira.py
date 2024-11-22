# coding: utf-8

from jira import JIRA
from llama_index.core.schema import Document

def load_jira_issues(api_token: str, query: str, server="https://issues.redhat.com")-> list[Document]:
    options = {
        "server": server,
        "headers": {"Authorization": f"Bearer {api_token}"},
    }
    
    jira = JIRA(options=options)

    issues = jira.search_issues(query)
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
                metadata={
                    "source": f"{server}/{issue.key}",
                    "id": issue.key,
                    "type": "jira",
                    "components": components,
                    "affects_versions": affects_versions,
                    "fix_versions": fix_versions,
                },
        ))

    return docs
