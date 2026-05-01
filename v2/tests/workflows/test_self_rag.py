from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from v2.server.services.rag import RAGResult
from v2.server.workflows.self_rag import SelfRAGService, RELEVANCE_CUTOFF


def _mock_llm_svc():
    llm = MagicMock()
    llm.complete = AsyncMock(return_value="This is the answer.")
    llm.grade = AsyncMock(return_value=RELEVANCE_CUTOFF + 1)
    llm.convert_query = AsyncMock(return_value="rewritten query")
    return llm


def _mock_vector_svc(nodes=None):
    vector = MagicMock()
    if nodes is None:
        node = MagicMock()
        node.text = "doc content"
        node.metadata = {"filelink": "https://example.com/doc.md"}
        nodes = [node]
    vector.retrieve.return_value = nodes
    return vector


@pytest.mark.asyncio
async def test_run_returns_result():
    llm = _mock_llm_svc()
    vector = _mock_vector_svc()

    svc = SelfRAGService(vector_svc=vector, llm_svc=llm)
    result = await svc.run(query="how to install?", history=[], doc_sources=["repo/main"])

    assert isinstance(result, RAGResult)
    assert result.content == "This is the answer."
    assert "https://example.com/doc.md" in result.references
    vector.retrieve.assert_called_once()
    llm.grade.assert_called_once()
    llm.complete.assert_called_once()


@pytest.mark.asyncio
async def test_run_grade_triggers_rewrite():
    """When grading fails, query gets rewritten and retrieval is retried."""
    llm = _mock_llm_svc()
    # First call: low score, second call: high score
    llm.grade = AsyncMock(side_effect=[RELEVANCE_CUTOFF - 1, RELEVANCE_CUTOFF + 1])

    vector = _mock_vector_svc()

    svc = SelfRAGService(vector_svc=vector, llm_svc=llm)
    result = await svc.run(query="vague question", history=[], doc_sources=["repo/main"])

    assert result.content == "This is the answer."
    assert llm.convert_query.call_count >= 1
    assert vector.retrieve.call_count >= 2


@pytest.mark.asyncio
async def test_run_empty_doc_sources():
    llm = _mock_llm_svc()
    vector = _mock_vector_svc(nodes=[])

    svc = SelfRAGService(vector_svc=vector, llm_svc=llm)
    result = await svc.run(query="test", history=[], doc_sources=[])

    assert isinstance(result, RAGResult)
    llm.complete.assert_called_once()


@pytest.mark.asyncio
async def test_stream_yields_chunks():
    llm = _mock_llm_svc()
    vector = _mock_vector_svc()

    async def mock_stream(messages):
        for chunk in ["Hello", " ", "world"]:
            yield chunk

    llm.stream = mock_stream

    svc = SelfRAGService(vector_svc=vector, llm_svc=llm)
    chunks = []
    async for result in svc.stream(query="test", history=[], doc_sources=["repo/main"]):
        chunks.append(result)

    content_chunks = [c for c in chunks if c.content]
    ref_chunks = [c for c in chunks if c.references]

    assert len(content_chunks) == 3
    assert "".join(c.content for c in content_chunks) == "Hello world"
    assert len(ref_chunks) == 1
    assert "https://example.com/doc.md" in ref_chunks[0].references


@pytest.mark.asyncio
async def test_stream_with_grade_retry():
    llm = _mock_llm_svc()
    llm.grade = AsyncMock(side_effect=[RELEVANCE_CUTOFF - 1, RELEVANCE_CUTOFF + 1])

    vector = _mock_vector_svc()

    async def mock_stream(messages):
        yield "answer"

    llm.stream = mock_stream

    svc = SelfRAGService(vector_svc=vector, llm_svc=llm)
    chunks = [c async for c in svc.stream(query="test", history=[], doc_sources=["repo/main"])]

    assert any(c.content == "answer" for c in chunks)
    assert llm.convert_query.call_count >= 1
