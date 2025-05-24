# coding: utf-8

"""
Help to load doc files
"""

import os
import logging
import hashlib
from pathlib import Path
from llama_index.core.schema import Document
from llama_index.readers.file import FlatReader
from llama_index.readers.file import MarkdownReader
from pydantic import BaseModel
from server.tools.common import count_tokens
from pydantic import BaseModel

logger = logging.getLogger(__name__)

link_pattern = r"\[([^\]]+)\]\(([^ )]+)(?: \"([^\"]+)\")?\)"

class DocLocation(BaseModel):
    path: str
    url: str

def list_files(start_path, exclude_list, suffix):
    file_list = []
    for root, dirs, files in os.walk(start_path):
        dirs[:] = [d for d in dirs if not d == ".git"]

        if os.path.basename(root) in exclude_list:
            continue

        for f in files:
            if f.endswith(suffix) and f not in exclude_list:
                file_list.append(os.path.join(root, f))

    return file_list

def to_docs(files: list[DocLocation], source: str, chunk_limit=2048) -> list[Document]:
    docs = []
    for f in files:
        doc = FlatReader().load_data(Path(f.path))[0]

        tokens = count_tokens(doc.text)
        if tokens > chunk_limit:
            # TODO need a better way to handle this
            logger.info("partition the large docs %s (tokens=%d)", f, tokens)
            docs.extend(do_partition(f, source))
            continue

        # override the metadata
        doc.metadata = {
            "filename": f.path,
            "filelink": f.url,
            "hash": hashlib.md5(doc.text.encode()).hexdigest(),
            "source": source,
        }

        docs.append(doc)
    return docs

def do_partition(f: DocLocation, source: str) -> list[Document]:
    docs = MarkdownReader().load_data(Path(f.path))
    for doc in docs:
        doc.metadata = {
            "filename": f.path,
            "filelink": f.url,
            "hash": hashlib.md5(doc.text.encode()).hexdigest(),
            "source": source,
        }
    return docs
