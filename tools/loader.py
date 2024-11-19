# coding: utf-8

import os
from langchain_community.document_loaders import UnstructuredMarkdownLoader

def load_runbooks(dir, exclude_list=None):
    if exclude_list is None:
        exclude_list = ["README.md", "SECURITY.md", "GUIDELINE.md", "index.md"]
    
    contents = []
    mds = load_markdowns(dir, exclude_list)
    for md in mds:
        content = md.page_content
        contents.append(content)
    return "Runbook: " + "\n\n---\n\nRunbook: ".join(contents)

def load_markdowns(dir, exclude_list):
    files = list_files(dir, exclude_list)
    mds = []
    for md_file in files:
        loader = UnstructuredMarkdownLoader(md_file)
        data = loader.load()
        mds.extend(data)
    return mds

def list_files(start_path, exclude_list, suffix=".md"):
    file_list = []
    for root, dirs, files in os.walk(start_path):
        dirs[:] = [d for d in dirs if not d == '.git']
        
        for f in files:
            if f.endswith(suffix) and f not in exclude_list:
                file_list.append(os.path.join(root, f))

    return file_list
