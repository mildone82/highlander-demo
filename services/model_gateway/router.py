from __future__ import annotations

import hashlib
import logging
import math
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from openai import OpenAI

from services.model_gateway.circuit import CircuitBreaker
from services.model_gateway.ratelimit import TokenBucket

logger = logging.getLogger(__name__)


@dataclass
class Provider:
    name: str
    base_url: str
    api_key: str
    llm_model: str
    embed_model: str
    circuit: CircuitBreaker = field(default_factory=CircuitBreaker)
    limiter: TokenBucket = field(default_factory=lambda: TokenBucket(rate_per_second=10, burst=20))

    @property
    def client(self) -> OpenAI:
        return OpenAI(base_url=self.base_url, api_key=self.api_key or "not-needed", timeout=60.0)


def _providers_from_env() -> List[Provider]:
    """Primary in-region provider first, then optional domestic-API fallback."""
    providers: List[Provider] = []
    primary = Provider(
        name="in-region",
        base_url=os.getenv("MG_PRIMARY_BASE_URL", ""),
        api_key=os.getenv("MG_PRIMARY_API_KEY", ""),
        llm_model=os.getenv("MG_PRIMARY_LLM_MODEL", "qwen2.5-7b-instruct"),
        embed_model=os.getenv("MG_PRIMARY_EMBED_MODEL", "bge-m3"),
    )
    _require_key_if_configured("in-region", primary.base_url, primary.api_key)
    if primary.base_url:
        providers.append(primary)
    fallback = Provider(
        name="domestic-api",
        base_url=os.getenv("MG_FALLBACK_BASE_URL", ""),
        api_key=os.getenv("MG_FALLBACK_API_KEY", ""),
        llm_model=os.getenv("MG_FALLBACK_LLM_MODEL", "deepseek-chat"),
        embed_model=os.getenv("MG_FALLBACK_EMBED_MODEL", ""),
    )
    _require_key_if_configured("domestic-api", fallback.base_url, fallback.api_key)
    if fallback.base_url:
        providers.append(fallback)
    return providers


def _require_key_if_configured(name: str, base_url: str, api_key: str) -> None:
    """Fail closed instead of silently using a placeholder credential."""
    if base_url and not api_key:
        raise RuntimeError(
            f"{name} base URL is configured but its API key is empty; "
            "set MG_PRIMARY_API_KEY / MG_FALLBACK_API_KEY from Secrets Manager"
        )


class ModelRouter:
    """Routes OpenAI-compatible calls: in-region primary, domestic API fallback."""

    def __init__(self, providers: Optional[List[Provider]] = None) -> None:
        self.providers = providers if providers is not None else _providers_from_env()
        self.fake = not self.providers

    # --- completion -----------------------------------------------------
    def complete(self, messages: List[Dict[str, Any]], model: str, temperature: float, max_tokens: int) -> Dict[str, Any]:
        if self.fake:
            return self._fake_completion(messages, model)
        last_error: Optional[Exception] = None
        for provider in self.providers:
            if not provider.circuit.allow() or not provider.limiter.acquire():
                continue
            try:
                response = provider.client.chat.completions.create(
                    model=provider.llm_model or model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                provider.circuit.record_success()
                choice = response.choices[0]
                return {
                    "id": response.id,
                    "object": "chat.completion",
                    "model": response.model or provider.llm_model,
                    "choices": [
                        {
                            "index": 0,
                            "message": {"role": "assistant", "content": choice.message.content or ""},
                            "finish_reason": choice.finish_reason or "stop",
                        }
                    ],
                    "usage": {
                        "prompt_tokens": getattr(response.usage, "prompt_tokens", 0) or 0,
                        "completion_tokens": getattr(response.usage, "completion_tokens", 0) or 0,
                        "total_tokens": getattr(response.usage, "total_tokens", 0) or 0,
                    },
                }
            except Exception as exc:  # noqa: BLE001 - fallback boundary
                logger.warning("Provider %s failed: %s", provider.name, exc)
                provider.circuit.record_failure()
                last_error = exc
        raise RuntimeError(f"All model providers failed: {last_error}")

    def embed(self, texts: List[str], model: str, dimensions: Optional[int] = None) -> List[List[float]]:
        if self.fake:
            return [self._fake_embedding(text, dimensions) for text in texts]
        last_error: Optional[Exception] = None
        for provider in self.providers:
            if not provider.embed_model:
                continue
            if not provider.circuit.allow() or not provider.limiter.acquire():
                continue
            try:
                kwargs = {"model": provider.embed_model, "input": [t.replace("\n", " ") for t in texts]}
                if dimensions is not None:
                    kwargs["dimensions"] = dimensions
                response = provider.client.embeddings.create(**kwargs)
                provider.circuit.record_success()
                ordered = sorted(response.data, key=lambda item: item.index)
                return [item.embedding for item in ordered]
            except Exception as exc:  # noqa: BLE001
                logger.warning("Provider %s embedding failed: %s", provider.name, exc)
                provider.circuit.record_failure()
                last_error = exc
        raise RuntimeError(f"All embedding providers failed: {last_error}")

    # --- deterministic local fallbacks ---------------------------------
    @staticmethod
    def _fake_completion(messages: List[Dict[str, Any]], model: str) -> Dict[str, Any]:
        last_user = next((m["content"] for m in reversed(messages) if m.get("role") == "user"), "")
        content = f"回答：{last_user}"
        return {
            "id": "chatcmpl-fake",
            "object": "chat.completion",
            "model": model,
            "choices": [
                {"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}
            ],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }

    @staticmethod
    def _fake_embedding(text: str, dimensions: Optional[int]) -> List[float]:
        dims = dimensions or 64
        vector = [0.0] * dims
        from app.embedder.hashing import tokenize

        for token in tokenize(text):
            digest = hashlib.md5(token.encode("utf-8")).digest()
            vector[int.from_bytes(digest[:4], "big") % dims] += 1.0
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]
        return vector
