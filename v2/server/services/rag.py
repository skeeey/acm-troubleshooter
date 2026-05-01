from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field


@dataclass
class RAGResult:
    content: str = ""
    references: list[str] = field(default_factory=list)


class RAGService(ABC):
    @abstractmethod
    async def run(
        self,
        query: str,
        history: list[dict],
        doc_sources: list[str],
    ) -> RAGResult:
        ...

    @abstractmethod
    async def stream(
        self,
        query: str,
        history: list[dict],
        doc_sources: list[str],
    ) -> AsyncGenerator[RAGResult, None]:
        ...
