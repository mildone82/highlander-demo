"""Tool definitions and HTTP-backed implementations for tool endpoints.

The same JSON schemas are reused for AgentCore Runtime tool registration and
for the LangGraph fallback, keeping the two backends behaviorally identical.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List

from app.http import JsonHttpClient


RETRIEVE_TOOL = {
    "name": "knowledge_retrieve",
    "description": "从组织知识库检索与问题相关的片段",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "top_k": {"type": "integer", "default": 8},
            "request_id": {"type": "string"},
        },
        "required": ["query"],
    },
}

MEMORY_SEARCH_TOOL = {
    "name": "memory_search",
    "description": "检索当前用户的长期记忆",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "limit": {"type": "integer", "default": 5},
        },
        "required": ["query"],
    },
}

MEMORY_ADD_TOOL = {
    "name": "memory_add",
    "description": "将本轮对话写入长期记忆（幂等）",
    "input_schema": {
        "type": "object",
        "properties": {
            "messages": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "role": {"type": "string"},
                        "content": {"type": "string"},
                    },
                    "required": ["role", "content"],
                },
            }
        },
        "required": ["messages"],
    },
}

TOOL_DEFINITIONS = [RETRIEVE_TOOL, MEMORY_SEARCH_TOOL, MEMORY_ADD_TOOL]


class HttpToolClients:
    """Production tool implementations that talk to the FastAPI services."""

    def __init__(self, rag_url: str, memory_url: str) -> None:
        self.rag = JsonHttpClient(rag_url)
        self.memory = JsonHttpClient(memory_url)

    def retrieve(self, query: str, top_k: int = 8) -> List[Dict[str, Any]]:
        response = self.rag.post(
            "/retrieve",
            {"query": query, "top_k": top_k, "user_id": "default"},
        )
        return [
            {"id": c["id"], "text": c["text"], "score": c.get("score"), "metadata": c.get("metadata", {})}
            for c in response.get("chunks", [])
        ]

    def memory_search(self, user_id: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        response = self.memory.post(
            "/memory/search",
            {"user_id": user_id, "query": query, "limit": limit},
        )
        return [
            {"id": m.get("id"), "memory": m.get("memory", ""), "score": m.get("score")}
            for m in response.get("memories", [])
        ]

    def memory_add(self, user_id: str, messages: List[Dict[str, Any]]) -> None:
        self.memory.post("/memory/add", {"user_id": user_id, "messages": messages})


class ToolRegistry:
    """Maps tool names to implementations; used by both backends."""

    def __init__(self, retrieve_fn, memory_search_fn, memory_add_fn) -> None:
        self._functions: Dict[str, Callable[..., Any]] = {
            "knowledge_retrieve": retrieve_fn,
            "memory_search": memory_search_fn,
            "memory_add": memory_add_fn,
        }

    def dispatch(self, name: str, arguments: Dict[str, Any], user_id: str = "default") -> Any:
        fn = self._functions.get(name)
        if fn is None:
            raise ValueError(f"Unknown tool: {name}")
        if name == "knowledge_retrieve":
            return fn(arguments.get("query", ""), arguments.get("top_k", 8))
        if name == "memory_search":
            return fn(user_id, arguments.get("query", ""), arguments.get("limit", 5))
        if name == "memory_add":
            return fn(user_id, arguments.get("messages", []))
        raise ValueError(f"Unknown tool: {name}")

    def dispatch_wrapper(self, name: str) -> Callable[..., Any]:
        """Return the raw callable for the LangGraph graph nodes."""
        fn = self._functions.get(name)
        if fn is None:
            raise ValueError(f"Unknown tool: {name}")
        return fn
