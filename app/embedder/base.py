from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List


class Embedder(ABC):
    @abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of texts, preserving order."""
