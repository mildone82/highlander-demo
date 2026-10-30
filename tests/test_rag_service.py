from app.embedder import LocalHashingEmbedder
from app.vector_store import InMemoryVectorStore
from services.rag.service import RetrieveService


def _seeded_service():
    embedder = LocalHashingEmbedder(dims=64)
    store = InMemoryVectorStore()
    store.put(
        ids=["c1", "c2"],
        vectors=embedder.embed(["S3 Vectors 索引容量", "完全无关的内容"]),
        payloads=[{"text": "S3 Vectors 索引容量", "source": "a"}, {"text": "完全无关的内容", "source": "b"}],
    )
    return RetrieveService(embedder, store)


def test_retrieve_returns_most_relevant_chunk():
    service = _seeded_service()
    response = service.retrieve("S3 Vectors 容量", top_k=2)
    assert response.chunks
    assert response.chunks[0].id == "c1"
    assert response.chunks[0].metadata["source"] == "a"
    assert response.latency_ms >= 0


def test_retrieve_empty_query():
    service = _seeded_service()
    response = service.retrieve("   ", top_k=2)
    assert response.chunks == []
