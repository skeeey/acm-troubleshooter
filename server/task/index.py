# coding: utf-8

"""
The task of indexing documents
"""

import logging
import os
import uuid
from server.services.db import DatabaseService
from server.services.vector import VectorStoreService
from server.tools.loaders.common import to_docs
from server.tools.loaders.acm import convert_docs
from server.tools.loaders.markdown import convert_mds

logger = logging.getLogger(__name__)

def index_documents(uid: uuid.UUID,
                    repo_url: str, branch: str, commit: str, repo_dir: str,
                    vector_store_svc: VectorStoreService, db_svc: DatabaseService):
    doc = db_svc.get_document(uid)
    if doc is None:
        logger.error("runbook set %s is not found", str(uid))
        return

    doc_commit = db_svc.add_document_commit(doc_id=uid, commit=commit)

    source = f"{os.path.basename(repo_dir)}-{commit}"
    logger.info("documents %s (%s) are indexing", source, commit)
    docs = []
    if "rhacm-docs" in repo_dir:
        docs.extend(convert_docs(repo_dir))
    else:
        base_url = f"{repo_url.replace(".git", "")}/tree/{branch}"
        docs.extend(convert_mds(repo_dir, base_url))

    vector_store_svc.index_docs(to_docs(docs, source))

    doc_commit.state = "indexed"
    db_svc.update_document_commit(doc_commit)
    logger.info("documents %s (%s) were indexed", source, commit)
