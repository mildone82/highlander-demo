"""Run the main flow end-to-end locally (question -> retrieve -> generate ->
memory write) with deterministic fakes. No AWS, GPU, or network required."""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.graph import build_graph
from app.embedder import LocalHashingEmbedder
from app.llm import FakeLLM
from app.schemas import ChatMessage
from app.vector_store import InMemoryVectorStore
from services.memory.fake_provider import FakeMemoryProvider
from services.rag.service import RetrieveService


def main() -> int:
    embedder = LocalHashingEmbedder(dims=64)
    store = InMemoryVectorStore()
    store.put(
        ids=["kb-1"],
        vectors=embedder.embed(["S3 Vectors 在中国区支持单索引 20 亿向量，仅支持直连 API"]),
        payloads=[{"text": "S3 Vectors 在中国区支持单索引 20 亿向量，仅支持直连 API", "source": "demo.md"}],
    )
    rag = RetrieveService(embedder, store)
    memory = FakeMemoryProvider()
    llm = FakeLLM()

    graph = build_graph(
        retrieve_fn=lambda q, k: [c.model_dump() for c in rag.retrieve(q, k).chunks],
        memory_search_fn=lambda uid, q, lim: [m.model_dump() for m in memory.search(uid, q, lim)],
        memory_add_fn=lambda uid, msgs: memory.add(uid, [ChatMessage(**m) for m in msgs], {}),
        complete_fn=llm.complete,
    )
    question = "S3 Vectors 在 AWS 中国区支持多大的索引？"
    result = graph.invoke(
        {"query": question, "user_id": "demo-user", "top_k": 8, "memory_limit": 5, "history": []}
    )
    stored = memory.search("demo-user", "S3 Vectors", 5)
    print(json.dumps(
        {
            "question": question,
            "retrieved_chunks": [c["text"] for c in result.get("chunks", [])],
            "answer": result.get("answer", ""),
            "memory_written": [m.memory for m in stored],
        },
        ensure_ascii=False,
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
