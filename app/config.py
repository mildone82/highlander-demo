"""Environment-driven settings helpers.

Configuration is deliberately read from plain environment variables so the
services stay free of framework-specific settings libraries. Every value has a
local-friendly default; production deployments set these in the task
definition / secret manager (see infra/terraform).
"""

from __future__ import annotations

import os
from typing import Optional


def _as_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def _as_int(value: Optional[str], default: int) -> int:
    if value is None or value.strip() == "":
        return default
    return int(value)


def _as_float(value: Optional[str], default: float) -> float:
    if value is None or value.strip() == "":
        return default
    return float(value)


class EmbedderSettings:
    provider = os.getenv("EMBEDDER_PROVIDER", "hashing")
    model = os.getenv("EMBEDDER_MODEL", "bge-m3")
    base_url = os.getenv("EMBEDDER_BASE_URL", "http://localhost:8002/v1")
    api_key = os.getenv("EMBEDDER_API_KEY", "local-dev-key")
    dims = _as_int(os.getenv("EMBEDDER_DIMS"), 64)
    timeout_s = _as_float(os.getenv("EMBEDDER_TIMEOUT_S"), 30.0)


class LLMSettings:
    provider = os.getenv("LLM_PROVIDER", "fake")
    model = os.getenv("LLM_MODEL", "qwen2.5-7b-instruct")
    base_url = os.getenv("LLM_BASE_URL", "http://localhost:8002/v1")
    api_key = os.getenv("LLM_API_KEY", "local-dev-key")
    temperature = _as_float(os.getenv("LLM_TEMPERATURE"), 0.2)
    max_tokens = _as_int(os.getenv("LLM_MAX_TOKENS"), 1024)
    timeout_s = _as_float(os.getenv("LLM_TIMEOUT_S"), 60.0)


class VectorStoreSettings:
    provider = os.getenv("VECTOR_STORE_PROVIDER", "in_memory")
    bucket = os.getenv("VECTOR_BUCKET", "knowledge-assistant-vectors")
    index = os.getenv("VECTOR_INDEX", "knowledge")
    dimension = _as_int(os.getenv("VECTOR_DIMENSION"), 64)
    distance = os.getenv("VECTOR_DISTANCE", "cosine")
    region = os.getenv("VECTOR_REGION", "cn-north-1")
    endpoint_url = os.getenv("VECTOR_ENDPOINT_URL", "")


class MemorySettings:
    provider = os.getenv("MEMORY_PROVIDER", "fake")
    bucket = os.getenv("MEMORY_VECTOR_BUCKET", "knowledge-assistant-vectors")
    collection = os.getenv("MEMORY_VECTOR_INDEX", "memory")
    dimension = _as_int(os.getenv("MEMORY_VECTOR_DIMENSION"), 64)
    region = os.getenv("MEMORY_VECTOR_REGION", "cn-north-1")
    endpoint_url = os.getenv("MEMORY_VECTOR_ENDPOINT_URL", "")
    llm_model = os.getenv("MEMORY_LLM_MODEL", "qwen2.5-7b-instruct")
    llm_base_url = os.getenv("MEMORY_LLM_BASE_URL", "http://localhost:8002/v1")
    llm_api_key = os.getenv("MEMORY_LLM_API_KEY", "local-dev-key")
    embedder_model = os.getenv("MEMORY_EMBEDDER_MODEL", "bge-m3")
    embedder_base_url = os.getenv("MEMORY_EMBEDDER_BASE_URL", "http://localhost:8002/v1")
    embedder_api_key = os.getenv("MEMORY_EMBEDDER_API_KEY", "local-dev-key")
    history_db_path = os.getenv("MEMORY_HISTORY_DB", ".local-data/mem0_history.db")
    agent_id = os.getenv("MEMORY_AGENT_ID", "knowledge-assistant")
