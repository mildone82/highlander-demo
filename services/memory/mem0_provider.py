from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from app.config import MemorySettings
from app.schemas import ChatMessage, MemoryItem
from services.memory.fake_provider import FakeMemoryProvider
from services.memory.service import MemoryProvider

logger = logging.getLogger(__name__)

# mem0 reads this at import time; set it before the lazy import in Mem0Provider.
os.environ.setdefault("MEM0_TELEMETRY", "False")


def build_mem0_config() -> Dict[str, Any]:
    """Assemble the mem0 config the design doc specifies.

    mem0 2.2.1 ships a SQLite-only history DB in the OSS package (the only
    history storage exposed in ``mem0/configs/base.py`` is ``history_db_path``;
    see README "Version deviations"), so ``history_db_path`` is used for the MVP
    and PostgreSQL is documented as a future upgrade once a PostgreSQL history
    backend is available.
    """
    return {
        "vector_store": {
            "provider": "s3_vectors",
            "config": {
                "vector_bucket_name": MemorySettings.bucket,
                "collection_name": MemorySettings.collection,
                "embedding_model_dims": MemorySettings.dimension,
                "distance_metric": "cosine",
                "region_name": MemorySettings.region,
            },
        },
        "llm": {
            "provider": "openai",
            "config": {
                "model": MemorySettings.llm_model,
                "temperature": 0.1,
                "api_key": MemorySettings.llm_api_key,
                "openai_base_url": MemorySettings.llm_base_url,
            },
        },
        "embedder": {
            "provider": "openai",
            "config": {
                "model": MemorySettings.embedder_model,
                "api_key": MemorySettings.embedder_api_key,
                "openai_base_url": MemorySettings.embedder_base_url,
                "embedding_dims": MemorySettings.dimension,
            },
        },
        "history_db_path": MemorySettings.history_db_path,
        "version": "v1.1",
    }


class Mem0Provider(MemoryProvider):
    """mem0 adapter exposing the four-contract surface (search/add/update/delete)."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        from mem0 import Memory  # imported lazily so the fake path has no mem0 dependency

        self._memory = Memory.from_config(config or build_mem0_config())

    def search(self, user_id: str, query: str, limit: int) -> List[MemoryItem]:
        response = self._memory.search(
            query,
            top_k=limit,
            filters={"user_id": user_id, "agent_id": MemorySettings.agent_id},
        )
        return [
            MemoryItem(
                id=result.get("id"),
                memory=result.get("memory", ""),
                score=result.get("score"),
                metadata=result.get("metadata") or {},
            )
            for result in response.get("results", [])
        ]

    def add(
        self,
        user_id: str,
        messages: List[ChatMessage],
        metadata: Optional[Dict[str, Any]],
    ) -> List[str]:
        response = self._memory.add(
            [message.model_dump() for message in messages],
            user_id=user_id,
            agent_id=MemorySettings.agent_id,
            metadata=metadata or {},
            infer=True,
        )
        return [
            str(result["id"])
            for result in response.get("results", [])
            if result.get("id") is not None
        ]

    def update(self, memory_id: str, memory: str, metadata: Optional[Dict[str, Any]]) -> None:
        # mem0 2.2.1 renamed the second positional arg from ``data`` to ``text``.
        # Pass it by keyword so the privacy/correction contract stays valid across
        # versions that accept ``metadata`` (both 2.0.0 and 2.2.1 do).
        self._memory.update(memory_id, text=memory, metadata=metadata)

    def delete(self, memory_id: str) -> None:
        self._memory.delete(memory_id)


def build_memory_provider() -> MemoryProvider:
    if MemorySettings.provider == "mem0":
        return Mem0Provider()
    return FakeMemoryProvider()
