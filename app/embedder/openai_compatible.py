from __future__ import annotations

from typing import List, Optional

from openai import OpenAI

from app.embedder.base import Embedder


class OpenAICompatibleEmbedder(Embedder):
    """OpenAI-compatible embeddings client (BGE-M3 via the model gateway)."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        dimensions: Optional[int] = None,
        timeout: float = 30.0,
    ) -> None:
        self.model = model
        self.dimensions = dimensions
        self._client = OpenAI(base_url=base_url, api_key=api_key or "not-needed", timeout=timeout)

    def embed(self, texts: List[str]) -> List[List[float]]:
        kwargs = {"model": self.model, "input": [t.replace("\n", " ") for t in texts]}
        if self.dimensions is not None:
            kwargs["dimensions"] = self.dimensions
        response = self._client.embeddings.create(**kwargs)
        ordered = sorted(response.data, key=lambda item: item.index)
        return [item.embedding for item in ordered]
