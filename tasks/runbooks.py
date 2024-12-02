# coding: utf-8

import logging
import os
import uuid
from services.index import RAGService
from services.storage import StorageService
from tools.loaders.markdown import load_runbooks
from tools.git import clone, pull, fetch_head_commit

logger = logging.getLogger(__name__)

def index(id: uuid.UUID, repo_dir: str, version: str, rag_svc: RAGService, storage_svc: StorageService):
    rs = storage_svc.get_runbook_set(id)
    if rs is None:
        logger.error("runbook set %s is not found", str(id))
        return

    rsv = storage_svc.add_runbook_set_version(runbook_set_id=id, version=version)

    source = f"{os.path.basename(repo_dir)}-{version}"
    docs = load_runbooks(dir=repo_dir, source=source)
    rag_svc.index_docs(docs=docs)

    rsv.state = "indexed"
    storage_svc.update_runbook_set_version(rsv)
    logger.info("runbooks %s (%s) were indexed", source, version)
