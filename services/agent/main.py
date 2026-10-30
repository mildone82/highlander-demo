"""HTTP entrypoint for the LangGraph fallback agent.

This is the path that is actually deployable in aws-cn today: an ECS Fargate
service that runs the LangGraph graph and talks to the rag/memory/model-gateway
services over the internal ALB. The AgentCore path (agent/agentcore_main.py)
stays as the design's A1 path pending an aws-cn account validation.
"""

from __future__ import annotations

import contextvars
import os
import uuid
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

from agent.graph import build_graph
from agent.tools import HttpToolClients, ToolRegistry
from app.llm import OpenAICompatibleLLM


class AskRequest(BaseModel):
    query: str
    user_id: str = "default"
    top_k: int = 8
    memory_limit: int = 5
    request_id: Optional[str] = None
    history: List[Dict[str, Any]] = Field(default_factory=list)


class AskResponse(BaseModel):
    query: str
    user_id: str
    request_id: str
    answer: str
    chunks: List[Dict[str, Any]] = Field(default_factory=list)
    trace: Dict[str, Any] = Field(default_factory=dict)


def _env(key: str, default: str) -> str:
    return os.getenv(key, default)


def build_remote_registry() -> tuple[HttpToolClients, ToolRegistry, OpenAICompatibleLLM]:
    tools = HttpToolClients(
        rag_url=_env("RAG_SERVICE_URL", "http://localhost:8001"),
        memory_url=_env("MEMORY_SERVICE_URL", "http://localhost:8000"),
    )
    llm = OpenAICompatibleLLM(
        base_url=_env("LLM_BASE_URL", "http://localhost:8002/v1"),
        api_key=_env("LLM_API_KEY", ""),
        model=_env("LLM_MODEL", "qwen2.5-7b-instruct"),
    )
    registry = ToolRegistry(tools.retrieve, tools.memory_search, tools.memory_add)
    return tools, registry, llm


app = FastAPI(title="knowledge-assistant-agent", version="0.1.0")
_tools, _registry, _llm = build_remote_registry()

# The graph invokes memory_add_fn(user_id, messages) with exactly two arguments.
# A ContextVar lets each /ask carry its own request_id through to the memory
# service without changing the graph contract.
_request_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "agent_request_id", default=None
)


def _memory_add(user_id: str, messages: List[Dict[str, Any]]) -> None:
    _tools.memory_add(user_id, messages, request_id=_request_id.get())


_graph = build_graph(
    _registry.dispatch_wrapper("knowledge_retrieve"),
    _registry.dispatch_wrapper("memory_search"),
    _memory_add,
    _llm.complete,
)


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    request_id = request.request_id or uuid.uuid4().hex
    token = _request_id.set(request_id)
    try:
        result = _graph.invoke(
            {
                "query": request.query,
                "user_id": request.user_id,
                "top_k": request.top_k,
                "memory_limit": request.memory_limit,
                "history": request.history,
            }
        )
    finally:
        _request_id.reset(token)
    return AskResponse(
        query=request.query,
        user_id=request.user_id,
        request_id=request_id,
        answer=result.get("answer", ""),
        chunks=result.get("chunks", []),
        trace={
            "chunk_count": len(result.get("chunks", [])),
            "memory_count": len(result.get("memories", [])),
        },
    )
