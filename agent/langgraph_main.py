"""LangGraph fallback entrypoint (ADR-001 plan B).

Production usage wires the FastAPI tool endpoints and the model gateway; local
development uses the deterministic fakes so the full flow runs without AWS.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List

from agent.graph import build_graph
from agent.tools import HttpToolClients, ToolRegistry


def _env(key: str, default: str) -> str:
    return os.getenv(key, default)


def build_local_clients() -> ToolRegistry:
    from app.embedder import LocalHashingEmbedder
    from app.llm import FakeLLM
    from app.vector_store import InMemoryVectorStore
    from services.memory.fake_provider import FakeMemoryProvider
    from services.rag.service import RetrieveService

    rag = RetrieveService(LocalHashingEmbedder(), InMemoryVectorStore())
    memory = FakeMemoryProvider()
    llm = FakeLLM()

    def retrieve(query: str, top_k: int = 8) -> List[Dict[str, Any]]:
        response = rag.retrieve(query, top_k)
        return [c.model_dump() for c in response.chunks]

    def memory_search(user_id: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        return [m.model_dump() for m in memory.search(user_id, query, limit)]

    def memory_add(user_id: str, messages: List[Dict[str, Any]]) -> None:
        from app.schemas import ChatMessage

        memory.add(user_id, [ChatMessage(**m) for m in messages], {})

    return ToolRegistry(retrieve, memory_search, memory_add), llm


def build_remote_clients() -> tuple[ToolRegistry, Any]:
    from app.llm import OpenAICompatibleLLM

    tools = HttpToolClients(
        rag_url=_env("RAG_SERVICE_URL", "http://localhost:8001"),
        memory_url=_env("MEMORY_SERVICE_URL", "http://localhost:8000"),
    )
    llm = OpenAICompatibleLLM(
        base_url=_env("LLM_BASE_URL", "http://localhost:8002/v1"),
        api_key=_env("LLM_API_KEY", "local-dev-key"),
        model=_env("LLM_MODEL", "qwen2.5-7b-instruct"),
    )
    registry = ToolRegistry(tools.retrieve, tools.memory_search, tools.memory_add)
    return registry, llm


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the knowledge assistant (LangGraph fallback)")
    parser.add_argument("question", nargs="?", help="Question to ask")
    parser.add_argument("--user-id", default="default")
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--mode", choices=["local", "remote"], default="local")
    args = parser.parse_args()

    if args.mode == "remote":
        registry, llm = build_remote_clients()
    else:
        registry, llm = build_local_clients()

    graph = build_graph(
        registry.dispatch_wrapper("knowledge_retrieve"),
        registry.dispatch_wrapper("memory_search"),
        registry.dispatch_wrapper("memory_add"),
        llm.complete,
    )

    question = args.question or "高地的知识库如何接入？"
    result = graph.invoke(
        {"query": question, "user_id": args.user_id, "top_k": args.top_k, "memory_limit": 5, "history": []}
    )
    print(json.dumps({"question": question, "answer": result.get("answer", ""), "chunks": result.get("chunks", [])}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
