from __future__ import annotations

import threading
import uuid
from typing import Any, Dict, List, Optional

from app.schemas import ChatMessage, MemoryItem
from services.memory.service import MemoryProvider


class FakeMemoryProvider(MemoryProvider):
    """Deterministic, in-process memory provider for local verification.

    Search is simple token-overlap scoring; enough to prove the orchestration
    path (add -> search -> use in prompt) without AWS or a GPU.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._by_user: Dict[str, List[MemoryItem]] = {}

    def search(self, user_id: str, query: str, limit: int) -> List[MemoryItem]:
        terms = set(query.lower().split())
        with self._lock:
            items = list(self._by_user.get(user_id, []))
        scored = []
        for item in items:
            words = set(item.memory.lower().split())
            overlap = len(terms & words) / max(1, len(terms))
            scored.append((overlap, item))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [item for _, item in scored[:limit]]

    def add(
        self,
        user_id: str,
        messages: List[ChatMessage],
        metadata: Optional[Dict[str, Any]],
    ) -> List[str]:
        ids: List[str] = []
        with self._lock:
            bucket = self._by_user.setdefault(user_id, [])
            for message in messages:
                if message.role not in ("user", "assistant"):
                    continue
                memory_id = f"mem-{uuid.uuid4().hex}"
                bucket.append(
                    MemoryItem(
                        id=memory_id,
                        memory=message.content,
                        metadata={"role": message.role, **(metadata or {})},
                    )
                )
                ids.append(memory_id)
        return ids

    def update(self, memory_id: str, memory: str, metadata: Optional[Dict[str, Any]]) -> None:
        with self._lock:
            for items in self._by_user.values():
                for item in items:
                    if item.id == memory_id:
                        item.memory = memory
                        if metadata is not None:
                            item.metadata.update(metadata)
                        return
        raise KeyError(memory_id)

    def delete(self, memory_id: str) -> None:
        with self._lock:
            for user_id, items in list(self._by_user.items()):
                self._by_user[user_id] = [item for item in items if item.id != memory_id]
