# coding: utf-8

import os
from pathlib import Path
import hashlib
from llama_index.readers.file import FlatReader
from llama_index.readers.file import MarkdownReader
from llama_index.core.schema import Document

def load_runbooks_as_str(dir: str, exclude_list=None) -> str:
    docs = load_runbooks(path=dir, exclude_list=exclude_list)
    contents = []
    for doc in docs:
        contents.append(doc.text)
    
    return "Runbook: " + "\nRunbook: ".join(contents)

def load_runbooks(path: str, version="2.12", exclude_list=None) -> list[Document]:
    if exclude_list is None:
        exclude_list = ["README.md", "SECURITY.md", "GUIDELINE.md", "index.md"]
    
    files = [path]
    if os.path.isdir(path):
        files = list_files(path, exclude_list, ".md")
    
    docs = []
    for md_file in files:
        md_docs = FlatReader().load_data(Path(md_file))
        docs.extend(md_docs)
    
    for doc in docs:
        doc_name = get_markdown_title(doc.text)
        if doc_name is None:
            raise ValueError(f"title is required for {doc.metadata.filename}")
        
        doc_id = hashlib.md5(f"{doc_name}.{version}".encode()).hexdigest()
        doc_hash = hashlib.md5(doc.text.encode()).hexdigest()
        # override the metadata
        doc.doc_id = doc_id
        doc.metadata = {
            "id": doc_id,
            "hash": doc_hash,
            "name": doc_name,
            "kind": "runbooks",
            "version": version,
        }
    return docs

def load_product_docs(dir: str, version="2.12", exclude_list=None) -> list[Document]:
    if exclude_list is None:
        exclude_list = []
    
    files = list_files(dir, exclude_list, ".md")

    docs = []
    for md_file in files:
        # MarkdownReader splits the markdown with headers, therefore one doc may be splitted by multi-parts
        # TODO find a way to give a fixed id for each doc
        docs.extend(MarkdownReader().load_data(Path(md_file)))

    for doc in docs:
        doc.metadata["kind"]="product_docs"
        doc.metadata["version"]=version
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

if __name__ == "__main__":
    # docs = load_product_docs("/Users/wliu1/Downloads/acm-2_12-doc")
    docs = load_runbooks(path="/Users/wliu1/Workspace/foundation-docs")
    print(len(docs))
    for doc in docs:
        print(doc.metadata)
