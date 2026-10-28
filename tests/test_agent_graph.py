from agent.graph import build_graph
from app.embedder import LocalHashingEmbedder
from app.llm import FakeLLM
from app.schemas import ChatMessage
from app.vector_store import InMemoryVectorStore
from services.memory.fake_provider import FakeMemoryProvider
from services.rag.service import RetrieveService


def _make_graph():
    embedder = LocalHashingEmbedder(dims=64)
    store = InMemoryVectorStore()
    store.put(
        ids=["kb-1"],
        vectors=embedder.embed(["S3 Vectors 支持单索引 20 亿向量，需直连 API"]),
        payloads=[{"text": "S3 Vectors 支持单索引 20 亿向量，需直连 API", "source": "kb"}],
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
    return graph, memory


def test_main_flow_question_retrieve_generate_remember():
    graph, memory = _make_graph()
    result = graph.invoke(
        {"query": "S3 Vectors 支持多大的索引？", "user_id": "u1", "top_k": 8, "memory_limit": 5, "history": []}
    )
    assert result["answer"] == "回答：S3 Vectors 支持多大的索引？"
    assert result["chunks"] and "20 亿" in result["chunks"][0]["text"]
    stored = memory.search("u1", "S3 Vectors 索引", 5)
    assert stored, "memory write should have persisted this turn"
