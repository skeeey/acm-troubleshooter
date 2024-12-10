# coding: utf-8

from llama_index.core.schema import Document
from tools.loaders.helper import list_files, to_docs

def load_runbooks(dir: str, source: str, exclude_list=None) -> list[Document]:
    if exclude_list is None:
        exclude_list = ["README.md", "SECURITY.md", "GUIDELINE.md", "index.md"]
    
    return to_docs(list_files(dir, exclude_list, ".md"), source)
