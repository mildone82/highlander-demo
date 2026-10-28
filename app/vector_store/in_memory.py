"""Deterministic in-memory vector store for local development and tests."""

from __future__ import annotations

import math
import threading
from typing import Any, Dict, List, Optional

from app.vector_store.base import SearchResult, VectorStore


def cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


class InMemoryVectorStore(VectorStore):
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._data: Dict[str, Dict[str, Any]] = {}

    def put(
        self,
        ids: List[str],
        vectors: List[List[float]],
        payloads: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        payloads = payloads or [{} for _ in ids]
        if not (len(ids) == len(vectors) == len(payloads)):
            raise ValueError("ids, vectors, and payloads must have equal length")
        with self._lock:
            for vector_id, vector, payload in zip(ids, vectors, payloads):
                self._data[vector_id] = {"vector": list(vector), "payload": dict(payload)}

    def search(
        self,
        vector: List[float],
        top_k: int = 8,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        def _matches(payload: Dict[str, Any]) -> bool:
            if not filters:
                return True
            return all(payload.get(key) == value for key, value in filters.items())

        scored: List[SearchResult] = []
        with self._lock:
            for vector_id, record in self._data.items():
                if not _matches(record["payload"]):
                    continue
                scored.append(
                    SearchResult(
                        id=vector_id,
                        score=cosine_similarity(vector, record["vector"]),
                        payload=dict(record["payload"]),
                    )
                )
        scored.sort(key=lambda r: r.score, reverse=True)
        return scored[:top_k]

    def delete(self, ids: List[str]) -> None:
        with self._lock:
            for vector_id in ids:
                self._data.pop(vector_id, None)

    def get(self, vector_id: str) -> Optional[SearchResult]:
        with self._lock:
            record = self._data.get(vector_id)
        if record is None:
            return None
        return SearchResult(id=vector_id, score=0.0, payload=dict(record["payload"]))

    def count(self) -> int:
        with self._lock:
            return len(self._data)
