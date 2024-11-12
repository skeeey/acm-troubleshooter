# coding: utf-8

import os
from jira import JIRA
from llama_index.core import SimpleDirectoryReader
from llama_index.core.schema import Document
from llama_index.readers.file import MarkdownReader
from typing import List
# from unstructured.partition.md import optional_decode
from unstructured.partition.md import partition_md

def load_runbooks(dir, exclude_list=None):
    if exclude_list is None:
        exclude_list = ["README.md", "SECURITY.md", "GUIDELINE.md", "index.md"]

    files = list_files(dir, exclude_list)
    docs = []
    for md in files:
        #  with open(md, encoding="utf8") as f:
        #     text = optional_decode(f.read())
        #     docs.append(text)
        # TODO: need test, this will output plain text
        elements = partition_md(filename=md)
        text = "\n\n".join([str(el) for el in elements])
        docs.append(text)

    all = "\n\n---\n\nRunbook: ".join(docs)
    return "Runbook: " + all

def load_runbook_list(dir, exclude_list=None) -> list[str]:
    if exclude_list is None:
        exclude_list = ["README.md", "SECURITY.md", "GUIDELINE.md", "index.md"]

    files = list_files(dir, exclude_list)
    docs = []
    for md in files:
        #  with open(md, encoding="utf8") as f:
        #     text = optional_decode(f.read())
        #     docs.append(text)
        # TODO: need test, this will output plain text
        elements = partition_md(filename=md)
        text = "\n\n".join([str(el) for el in elements])
        docs.append(text)
    
    return docs


def load_local_data(local_data_dir):
    file_extractor = {
        ".md": MarkdownReader(),
    }
    return SimpleDirectoryReader(local_data_dir, file_extractor=file_extractor, recursive=True).load_data()

def load_jira_data(issues) -> List[Document]:
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

def list_files(start_path, exclude_list, suffix=".md"):
    file_list = []
    for root, dirs, files in os.walk(start_path):
        dirs[:] = [d for d in dirs if not d == '.git']
        
        for f in files:
            if f.endswith(suffix) and f not in exclude_list:
                file_list.append(os.path.join(root, f))

    return file_list
