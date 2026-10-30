"""The knowledge-assistant main flow, shared by both orchestration backends.

Flow (from the phase-2 design): question -> knowledge retrieval -> long-term
memory recall -> answer generation -> asynchronous memory write.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

SYSTEM_PROMPT = (
    "你是组织内部知识助手。请仅依据提供的知识片段与长期记忆回答；"
    "若信息不足，明确说明缺少信息，不要编造。回答使用简体中文。"
)


@dataclass
class AssistantResult:
    query: str
    user_id: str
    answer: str
    chunks: List[Dict[str, Any]] = field(default_factory=list)
    memories: List[Dict[str, Any]] = field(default_factory=list)
    trace: Dict[str, Any] = field(default_factory=dict)


def build_messages(
    query: str,
    chunks: List[Dict[str, Any]],
    memories: List[Dict[str, Any]],
    history: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    messages: List[Dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    if chunks:
        context = "\n\n".join(f"[片段 {i + 1}] {c.get('text', '')}" for i, c in enumerate(chunks))
        messages.append({"role": "system", "content": f"知识库检索结果：\n{context}"})
    if memories:
        memory_text = "\n".join(f"- {m.get('memory', '')}" for m in memories)
        messages.append({"role": "system", "content": f"与该用户相关的长期记忆：\n{memory_text}"})
    messages.extend(history or [])
    messages.append({"role": "user", "content": query})
    return messages


def run_assistant(
    query: str,
    user_id: str,
    retrieve_fn: Callable[[str, int], List[Dict[str, Any]]],
    memory_search_fn: Callable[[str, str, int], List[Dict[str, Any]]],
    memory_add_fn: Callable[[str, List[Dict[str, Any]]], None],
    complete_fn: Callable[[List[Dict[str, Any]]], str],
    top_k: int = 8,
    memory_limit: int = 5,
    history: Optional[List[Dict[str, Any]]] = None,
) -> AssistantResult:
    chunks = retrieve_fn(query, top_k)
    memories = memory_search_fn(user_id, query, memory_limit)
    messages = build_messages(query, chunks, memories, history)
    answer = complete_fn(messages)
    memory_add_fn(user_id, [{"role": "user", "content": query}, {"role": "assistant", "content": answer}])
    return AssistantResult(
        query=query,
        user_id=user_id,
        answer=answer,
        chunks=chunks,
        memories=memories,
        trace={"chunk_count": len(chunks), "memory_count": len(memories), "top_k": top_k},
    )
