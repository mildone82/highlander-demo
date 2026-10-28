from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class LLM(ABC):
    @abstractmethod
    def complete(self, messages: List[Dict[str, Any]]) -> str:
        """Return assistant text for an OpenAI-format message list."""
