import hashlib
import logging
import uuid

from llama_index.core.node_parser import MarkdownNodeParser, SentenceSplitter
from llama_index.core.schema import Document

from v2.server.models.db import DocumentState
from v2.server.models.embeddings import BGE
from v2.server.services.db import DatabaseService
from v2.server.services.vector import VectorStoreService
from v2.server.tools.loaders import DocFile, load_markdown_files

logger = logging.getLogger(__name__)


def _build_source(repo: str, branch: str) -> str:
    return f"{repo}/{branch}"


def _chunk_file(doc_file: DocFile, source: str) -> list[Document]:
    metadata = {
        "source": source,
        "file_path": doc_file.path,
        "file_link": doc_file.url,
        "content_hash": doc_file.content_hash,
    }

    doc = Document(text=doc_file.content, metadata=metadata)

    md_parser = MarkdownNodeParser()
    nodes = md_parser.get_nodes_from_documents([doc])

    splitter = SentenceSplitter(chunk_size=BGE.chunk_size, chunk_overlap=BGE.chunk_overlap)
    nodes = splitter.get_nodes_from_documents(nodes)

    docs = []
    for node in nodes:
        node.metadata = metadata
        docs.append(Document(text=node.get_content(), metadata=metadata))
    return docs


async def index_documents(
    doc_id: uuid.UUID,
    repo_dir: str,
    repo_url: str,
    branch: str,
    vector_svc: VectorStoreService,
    db_svc: DatabaseService,
):
    doc = await db_svc.get_document(doc_id)
    if doc is None:
        logger.error("document %s not found", doc_id)
        return

    source = _build_source(repo_url, branch)

    try:
        base_url = repo_url.removesuffix(".git") + f"/tree/{branch}"
        doc_files = load_markdown_files(repo_dir, base_url)

        existing_hashes = vector_svc.list_file_hashes(source)
        current_paths = {f.path for f in doc_files}

        new_files = [f for f in doc_files if f.path not in existing_hashes]
        changed_files = [
            f for f in doc_files
            if f.path in existing_hashes and existing_hashes[f.path] != f.content_hash
        ]
        deleted_paths = [p for p in existing_hashes if p not in current_paths]

        logger.info(
            "diff result for %s: new=%d, changed=%d, deleted=%d",
            source, len(new_files), len(changed_files), len(deleted_paths),
        )

        for path in deleted_paths:
            vector_svc.delete_docs_by_file(source, path)

        for f in changed_files:
            vector_svc.delete_docs_by_file(source, f.path)

        to_embed = new_files + changed_files
        if to_embed:
            all_docs = []
            for f in to_embed:
                all_docs.extend(_chunk_file(f, source))
            vector_svc.index_docs(all_docs)

        doc = await db_svc.get_document(doc_id)
        if doc is None:
            logger.warning("document %s was deleted during indexing, skipping state update", doc_id)
            return

        doc.state = DocumentState.INDEXED
        doc.error = None
        await db_svc.update_document(doc)
        logger.info("document %s indexed successfully", doc_id)

    except Exception as e:
        logger.exception("failed to index document %s", doc_id)
        doc = await db_svc.get_document(doc_id)
        if doc is None:
            logger.warning("document %s was deleted during indexing, skipping error update", doc_id)
            return

        doc.state = DocumentState.FAILED
        doc.error = str(e)
        await db_svc.update_document(doc)
