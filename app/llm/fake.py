from __future__ import annotations

from typing import Any, Dict, List

from app.llm.base import LLM


class FakeLLM(LLM):
    """Deterministic LLM for local smoke tests (no network, no GPU)."""

    def __init__(self, prefix: str = "回答：") -> None:
        self.prefix = prefix

    def complete(self, messages: List[Dict[str, Any]]) -> str:
        last_user = next(
            (m["content"] for m in reversed(messages) if m.get("role") == "user"),
            "",
        )
        return f"{self.prefix}{last_user}"
