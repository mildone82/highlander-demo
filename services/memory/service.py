from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.schemas import ChatMessage, MemoryItem


class MemoryProvider(ABC):
    @abstractmethod
    def search(self, user_id: str, query: str, limit: int) -> List[MemoryItem]:
        """Return long-term memories relevant to the query."""

    @abstractmethod
    def add(
        self,
        user_id: str,
        messages: List[ChatMessage],
        metadata: Optional[Dict[str, Any]],
    ) -> List[str]:
        """Extract and store memories; return affected memory ids."""

    @abstractmethod
    def update(self, memory_id: str, memory: str, metadata: Optional[Dict[str, Any]]) -> None:
        """Replace a memory's text (kept for the privacy/correction contract)."""

    @abstractmethod
    def delete(self, memory_id: str) -> None:
        """Delete a memory (right-to-erasure contract)."""


class MemoryService:
    """The only component allowed to own memory read/write semantics."""

    def __init__(self, provider: MemoryProvider) -> None:
        self.provider = provider

    def search(self, user_id: str, query: str, limit: int = 5) -> List[MemoryItem]:
        if not query.strip():
            return []
        return self.provider.search(user_id, query, limit)

    def add(
        self,
        user_id: str,
        messages: List[ChatMessage],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        return self.provider.add(user_id, messages, metadata or {})

    def update(self, memory_id: str, memory: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        self.provider.update(memory_id, memory, metadata)

    def delete(self, memory_id: str) -> None:
        self.provider.delete(memory_id)
