# coding: utf-8

from pydantic import BaseModel

class LLMConfig(BaseModel):
    api_base: str | None = None
    api_key: str | None = None
    model: str | None = None

class RetrievalConfig(BaseModel):
    doc_sources: list[str] | None = None

class Context(BaseModel):
    llm_config: LLMConfig | None = None
    retrieval_config: RetrievalConfig | None = None
