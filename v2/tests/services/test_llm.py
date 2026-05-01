from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from v2.server.services.llm import LLMService, build_respond_messages


def test_build_respond_messages_basic():
    messages = build_respond_messages(
        documents=["doc1 content"],
        query="How to install ACM?",
        history=[],
    )
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert "ACM" in messages[0]["content"]
    assert messages[1]["role"] == "user"
    assert "How to install ACM?" in messages[1]["content"]
    assert "Document 1" in messages[1]["content"]


def test_build_respond_messages_with_history():
    messages = build_respond_messages(
        documents=[],
        query="follow up",
        history=[
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi"},
        ],
    )
    assert "Conversation History" in messages[1]["content"]
    assert "hello" in messages[1]["content"]


@pytest.mark.asyncio
async def test_complete():
    svc = LLMService(responder_model="test-model")

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "test response"

    with patch("v2.server.services.llm.litellm.acompletion", new_callable=AsyncMock, return_value=mock_response):
        result = await svc.complete([{"role": "user", "content": "hi"}])

    assert result == "test response"


@pytest.mark.asyncio
async def test_stream():
    svc = LLMService(responder_model="test-model")

    async def mock_stream(*args, **kwargs):
        for text in ["Hello", " world"]:
            chunk = MagicMock()
            chunk.choices = [MagicMock()]
            chunk.choices[0].delta.content = text
            yield chunk

    with patch("v2.server.services.llm.litellm.acompletion", new_callable=AsyncMock, return_value=mock_stream()):
        chunks = [c async for c in svc.stream([{"role": "user", "content": "hi"}])]

    assert chunks == ["Hello", " world"]


@pytest.mark.asyncio
async def test_grade():
    svc = LLMService(responder_model="big", grader_model="small")

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '{"score": 8}'

    with patch("v2.server.services.llm.litellm.acompletion", new_callable=AsyncMock, return_value=mock_response) as mock_call:
        score = await svc.grade("how to install?", "install doc content")

    assert score == 8
    assert mock_call.call_args.kwargs["model"] == "small"


@pytest.mark.asyncio
async def test_grade_parse_failure():
    svc = LLMService(responder_model="big", grader_model="small")

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "invalid json"

    with patch("v2.server.services.llm.litellm.acompletion", new_callable=AsyncMock, return_value=mock_response):
        score = await svc.grade("q", "d")

    assert score == 0


@pytest.mark.asyncio
async def test_convert_query():
    svc = LLMService(responder_model="big", grader_model="small")

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "how to install ACM on OpenShift"

    with patch("v2.server.services.llm.litellm.acompletion", new_callable=AsyncMock, return_value=mock_response) as mock_call:
        result = await svc.convert_query("install acm")

    assert result == "how to install ACM on OpenShift"
    assert mock_call.call_args.kwargs["model"] == "small"


@pytest.mark.asyncio
async def test_grader_model_defaults_to_responder():
    svc = LLMService(responder_model="big-model")
    assert svc.grader_model == "big-model"
