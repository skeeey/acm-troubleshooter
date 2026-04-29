from unittest.mock import MagicMock

import pytest

from v2.server.models.db import DocumentState
from v2.server.tasks.index import index_documents


@pytest.fixture
def docs_dir(tmp_path):
    docs = tmp_path / "repo"
    docs.mkdir()
    (docs / "doc1.md").write_text("# Doc 1\nFirst document.")
    (docs / "doc2.md").write_text("# Doc 2\nSecond document.")
    return str(docs)


@pytest.fixture
def mock_vector_svc():
    svc = MagicMock()
    svc.list_file_hashes.return_value = {}
    svc.index_docs.return_value = None
    svc.delete_docs_by_file.return_value = None
    return svc


@pytest.mark.asyncio
async def test_index_new_documents(db_svc, docs_dir, mock_vector_svc):
    doc = await db_svc.create_document(repo="https://github.com/org/repo", branch="main", desc="test")

    await index_documents(
        doc_id=doc.id,
        repo_dir=docs_dir,
        repo_url="https://github.com/org/repo",
        branch="main",
        vector_svc=mock_vector_svc,
        db_svc=db_svc,
    )

    mock_vector_svc.index_docs.assert_called_once()
    indexed_docs = mock_vector_svc.index_docs.call_args[0][0]
    assert len(indexed_docs) > 0

    updated_doc = await db_svc.get_document(doc.id)
    assert updated_doc.state == DocumentState.INDEXED
    assert updated_doc.error is None


@pytest.mark.asyncio
async def test_index_incremental_skip_unchanged(db_svc, docs_dir, mock_vector_svc):
    from v2.server.tools.loaders import load_markdown_files

    files = load_markdown_files(docs_dir, "https://github.com/org/repo/tree/main")
    existing_hashes = {f.path: f.content_hash for f in files}
    mock_vector_svc.list_file_hashes.return_value = existing_hashes

    doc = await db_svc.create_document(repo="https://github.com/org/repo", branch="main", desc="test")

    await index_documents(
        doc_id=doc.id,
        repo_dir=docs_dir,
        repo_url="https://github.com/org/repo",
        branch="main",
        vector_svc=mock_vector_svc,
        db_svc=db_svc,
    )

    mock_vector_svc.index_docs.assert_not_called()
    mock_vector_svc.delete_docs_by_file.assert_not_called()

    updated_doc = await db_svc.get_document(doc.id)
    assert updated_doc.state == DocumentState.INDEXED


@pytest.mark.asyncio
async def test_index_incremental_changed_file(db_svc, docs_dir, mock_vector_svc):
    mock_vector_svc.list_file_hashes.return_value = {
        "doc1.md": "old_hash",
        "doc2.md": "old_hash",
    }

    doc = await db_svc.create_document(repo="https://github.com/org/repo", branch="main", desc="test")

    await index_documents(
        doc_id=doc.id,
        repo_dir=docs_dir,
        repo_url="https://github.com/org/repo",
        branch="main",
        vector_svc=mock_vector_svc,
        db_svc=db_svc,
    )

    assert mock_vector_svc.delete_docs_by_file.call_count == 2
    mock_vector_svc.index_docs.assert_called_once()


@pytest.mark.asyncio
async def test_index_incremental_deleted_file(db_svc, docs_dir, mock_vector_svc):
    mock_vector_svc.list_file_hashes.return_value = {
        "doc1.md": "some_hash",
        "doc2.md": "some_hash",
        "removed.md": "old_hash",
    }

    doc = await db_svc.create_document(repo="https://github.com/org/repo", branch="main", desc="test")

    await index_documents(
        doc_id=doc.id,
        repo_dir=docs_dir,
        repo_url="https://github.com/org/repo",
        branch="main",
        vector_svc=mock_vector_svc,
        db_svc=db_svc,
    )

    deleted_calls = [
        call for call in mock_vector_svc.delete_docs_by_file.call_args_list
        if call[0][1] == "removed.md"
    ]
    assert len(deleted_calls) == 1


@pytest.mark.asyncio
async def test_index_failure_sets_error(db_svc, docs_dir, mock_vector_svc):
    mock_vector_svc.index_docs.side_effect = RuntimeError("embedding failed")

    doc = await db_svc.create_document(repo="https://github.com/org/repo", branch="main", desc="test")

    await index_documents(
        doc_id=doc.id,
        repo_dir=docs_dir,
        repo_url="https://github.com/org/repo",
        branch="main",
        vector_svc=mock_vector_svc,
        db_svc=db_svc,
    )

    updated_doc = await db_svc.get_document(doc.id)
    assert updated_doc.state == DocumentState.FAILED
    assert "embedding failed" in updated_doc.error
