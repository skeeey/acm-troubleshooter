# coding: utf-8

import os
from pathlib import Path
import hashlib
from llama_index.readers.file import FlatReader
from llama_index.readers.file import MarkdownReader
from llama_index.core.schema import Document

def load_runbooks_as_str(dir: str, exclude_list=None) -> str:
    docs = load_runbooks(dir=dir, exclude_list=exclude_list)
    contents = []
    for doc in docs:
        contents.append(doc.text)
    
    return "Runbook: " + "\nRunbook: ".join(contents)

def load_runbooks(dir: str, source: str, exclude_list=None) -> list[Document]:
    if exclude_list is None:
        exclude_list = ["README.md", "SECURITY.md", "GUIDELINE.md", "index.md"]
    
    files = list_files(dir, exclude_list, ".md")
    
    docs = []
    for md_file in files:
        md_docs = FlatReader().load_data(Path(md_file))
        docs.extend(md_docs)
    
    for doc in docs:
        doc_name = get_markdown_title(doc.text)
        if doc_name is None:
            raise ValueError(f"title is required for {doc.metadata.filename}")
        
        doc_id = hashlib.md5(f"{doc_name}.{source}".encode()).hexdigest()
        doc_hash = hashlib.md5(doc.text.encode()).hexdigest()
        # override the doc_id
        doc.doc_id = doc_id
        # override the metadata
        doc.metadata = {
            "id": doc_id,
            "name": doc_name,
            "hash": doc_hash,
            "source": source,
        }
    return docs

def list_files(start_path, exclude_list, suffix):
    file_list = []
    for root, dirs, files in os.walk(start_path):
        dirs[:] = [d for d in dirs if not d == '.git']
        
        for f in files:
            if f.endswith(suffix) and f not in exclude_list:
                file_list.append(os.path.join(root, f))

    return file_list

def get_markdown_title(content):
    lines = content.splitlines()
    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith('#'):
            title = stripped_line.lstrip('#').strip()
            return title
    return None
