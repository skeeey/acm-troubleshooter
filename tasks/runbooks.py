# coding: utf-8

"""
The task of indexing runbooks
"""

import logging
import os
import uuid
from services.index import RAGService
from services.storage import StorageService
from tools.loaders.markdown import load_runbooks
from tools.loaders.adoc import load_acm_docs

logger = logging.getLogger(__name__)

def index(uid: uuid.UUID, repo_dir: str, version: str, rag_svc: RAGService, storage_svc: StorageService):
    rs = storage_svc.get_runbook_set(uid)
    if rs is None:
        logger.error("runbook set %s is not found", str(uid))
        return

    rsv = storage_svc.add_runbook_set_version(runbook_set_id=uid, version=version)

    source = f"{os.path.basename(repo_dir)}-{version}"
    docs = []
    if "rhacm-docs" in repo_dir:
        docs = load_acm_docs(adoc_dir=repo_dir, source=source)
    else:
        docs = load_runbooks(md_dir=repo_dir, source=source)

    rag_svc.index_docs(docs=docs)

    rsv.state = "indexed"
    storage_svc.update_runbook_set_version(rsv)
    logger.info("runbooks %s (%s) were indexed", source, version)
