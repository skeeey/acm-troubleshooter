# coding: utf-8

"""
The helper functions for load files
"""

import os
import logging
import hashlib
from llama_index.readers.file import FlatReader
from llama_index.readers.file import MarkdownReader
from pathlib import Path
from tools.common import count_tokens

logger = logging.getLogger(__name__)

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

def to_docs(files, source, envs=None, partition=False, chunk_size=2048):
    docs = []
    for f in files:
        doc = FlatReader().load_data(Path(f))[0]

        if envs is not None:
            doc.text = set_envs(envs, doc.text)

        tokens = count_tokens(doc.text)
        if tokens > chunk_size:
            # TODO need a better way to handle this
            if partition:
                logger.warning("partition the large docs %s (tokens=%d)", f, tokens)
                docs.extend(do_partition(f, source, envs))
                continue

            logger.warning("ignore the large docs %s (tokens=%d)", f, tokens)
            continue

        # override the metadata
        doc.metadata = {
            "filename": f,
            "hash": hashlib.md5(doc.text.encode()).hexdigest(),
            "source": source,
        }

        docs.append(doc)
    return docs

def do_partition(f, source, doc_envs=None):
    docs = MarkdownReader().load_data(Path(f))
    for doc in docs:
        if doc_envs is not None:
            doc.text = set_envs(doc_envs, doc.text)

        doc.metadata = {
            "filename": f,
            "hash": hashlib.md5(doc.text.encode()).hexdigest(),
            "source": source,
        }
    return docs

def set_envs(envs, text):
    for key in envs:
        text = text.replace("{"+key+"}", envs[key])
    return text
