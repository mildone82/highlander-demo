"""Vector-store abstraction shared by RAG and ingestion."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SearchResult:
    id: str
    score: float
    payload: Dict[str, Any] = field(default_factory=dict)


class VectorStore(ABC):
    @abstractmethod
    def put(
        self,
        ids: List[str],
        vectors: List[List[float]],
        payloads: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Insert or overwrite vectors keyed by ``ids``."""

    @abstractmethod
    def search(
        self,
        vector: List[float],
        top_k: int = 8,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Return the top-k nearest vectors."""

    @abstractmethod
    def delete(self, ids: List[str]) -> None:
        """Delete vectors by id."""

    @abstractmethod
    def get(self, vector_id: str) -> Optional[SearchResult]:
        """Fetch metadata for a single vector id."""

    @abstractmethod
    def count(self) -> int:
        """Number of vectors in the store (diagnostics only)."""
