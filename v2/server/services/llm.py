import json
import logging
from collections.abc import AsyncGenerator

import litellm

from v2.server.prompts.templates import RESPONSE_NOTICES, CONVERTOR_NOTICES

logger = logging.getLogger(__name__)


def build_respond_messages(
    documents: list[str],
    query: str,
    history: list[dict],
    notices: str = RESPONSE_NOTICES,
) -> list[dict]:
    system = (
        "You are an ACM (Red Hat Advanced Cluster Management) troubleshooting assistant. "
        "Answer questions based on the provided documents and conversation history.\n\n"
        f"## Notices\n{notices}"
    )

    parts = []
    if history:
        parts.append("## Conversation History")
        for msg in history:
            parts.append(f"**{msg['role']}**: {msg['content']}")

    if documents:
        parts.append("## Relevant Documents")
        for i, doc in enumerate(documents, 1):
            parts.append(f"### Document {i}\n{doc}")

    parts.append(f"## Question\n{query}")

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": "\n\n".join(parts)},
    ]


class LLMService:
    def __init__(
        self,
        responder_model: str,
        grader_model: str | None = None,
        api_base: str | None = None,
        api_key: str | None = None,
    ):
        self.responder_model = responder_model
        self.grader_model = grader_model or responder_model
        self.api_base = api_base
        self.api_key = api_key

    async def complete(self, messages: list[dict]) -> str:
        response = await litellm.acompletion(
            model=self.responder_model,
            messages=messages,
            api_base=self.api_base,
            api_key=self.api_key,
        )
        return response.choices[0].message.content

    async def stream(self, messages: list[dict]) -> AsyncGenerator[str, None]:
        response = await litellm.acompletion(
            model=self.responder_model,
            messages=messages,
            api_base=self.api_base,
            api_key=self.api_key,
            stream=True,
        )
        async for chunk in response:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    async def grade(self, question: str, document: str) -> int:
        messages = [
            {"role": "system", "content": (
                "You are a relevance grader. Assess how relevant the document is to the question. "
                "Respond with ONLY a JSON object: {\"score\": <0-10>} where 10 is most relevant."
            )},
            {"role": "user", "content": (
                f"Question: {question}\n\n"
                f"Document: {document}"
            )},
        ]
        response = await litellm.acompletion(
            model=self.grader_model,
            messages=messages,
            api_base=self.api_base,
            api_key=self.api_key,
        )
        content = response.choices[0].message.content.strip()
        try:
            return json.loads(content)["score"]
        except (json.JSONDecodeError, KeyError):
            logger.warning("failed to parse grade response: %s", content)
            return 0

    async def convert_query(self, query: str, notices: str = CONVERTOR_NOTICES) -> str:
        messages = [
            {"role": "system", "content": (
                "You are a query optimizer. Rewrite the user's question to be more effective "
                "for searching a vector store of ACM documentation. "
                "Return ONLY the rewritten query, nothing else. "
                "If the query is not related to ACM, return an empty string.\n\n"
                f"## Notices\n{notices}"
            )},
            {"role": "user", "content": query},
        ]
        response = await litellm.acompletion(
            model=self.grader_model,
            messages=messages,
            api_base=self.api_base,
            api_key=self.api_key,
        )
        return response.choices[0].message.content.strip()
