"""LangGraph fallback orchestration (ADR-001 plan B)."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from agent.orchestrator import build_messages


class AssistantState(TypedDict, total=False):
    query: str
    user_id: str
    top_k: int
    memory_limit: int
    history: List[Dict[str, Any]]
    chunks: List[Dict[str, Any]]
    memories: List[Dict[str, Any]]
    answer: str


def build_graph(
    retrieve_fn: Callable[[str, int], List[Dict[str, Any]]],
    memory_search_fn: Callable[[str, str, int], List[Dict[str, Any]]],
    memory_add_fn: Callable[[str, List[Dict[str, Any]]], None],
    complete_fn: Callable[[List[Dict[str, Any]]], str],
) -> Any:
    def retrieve(state: AssistantState) -> Dict[str, Any]:
        return {"chunks": retrieve_fn(state["query"], state.get("top_k", 8))}

    def recall(state: AssistantState) -> Dict[str, Any]:
        memories = memory_search_fn(
            state["user_id"],
            state["query"],
            state.get("memory_limit", 5),
        )
        return {"memories": memories}

    def generate(state: AssistantState) -> Dict[str, Any]:
        messages = build_messages(
            state["query"],
            state.get("chunks", []),
            state.get("memories", []),
            state.get("history"),
        )
        return {"answer": complete_fn(messages)}

    def remember(state: AssistantState) -> Dict[str, Any]:
        memory_add_fn(
            state["user_id"],
            [
                {"role": "user", "content": state["query"]},
                {"role": "assistant", "content": state.get("answer", "")},
            ],
        )
        return {}

    builder = StateGraph(AssistantState)
    builder.add_node("retrieve", retrieve)
    builder.add_node("recall", recall)
    builder.add_node("generate", generate)
    builder.add_node("remember", remember)
    builder.add_edge(START, "retrieve")
    builder.add_edge("retrieve", "recall")
    builder.add_edge("recall", "generate")
    builder.add_edge("generate", "remember")
    builder.add_edge("remember", END)
    return builder.compile()
