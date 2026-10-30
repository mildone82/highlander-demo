from __future__ import annotations

from typing import Any, Dict, List, Optional

from openai import OpenAI

from app.llm.base import LLM


class OpenAICompatibleLLM(LLM):
    """OpenAI-compatible chat client (in-region endpoint or domestic API)."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        timeout: float = 60.0,
    ) -> None:
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = OpenAI(base_url=base_url, api_key=api_key or "not-needed", timeout=timeout)

    def complete(self, messages: List[Dict[str, Any]]) -> str:
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        first = response.choices[0]
        return (first.message.content or "").strip()
