from app.schemas import ChatMessage
from ingestion.idempotency import InMemoryIdempotencyStore
from services.memory.fake_provider import FakeMemoryProvider
from services.memory.service import MemoryService


def test_memory_add_search_delete_roundtrip():
    service = MemoryService(FakeMemoryProvider())
    ids = service.add(
        "u1",
        [ChatMessage(role="user", content="我负责 S3 Vectors 集成"), ChatMessage(role="assistant", content="好的")],
    )
    assert len(ids) == 2

    results = service.search("u1", "S3 Vectors", limit=5)
    assert results
    assert "S3 Vectors" in results[0].memory

    service.update(ids[0], "我负责 S3 Vectors 与 mem0 集成")
    service.delete(ids[1])
    remaining = service.search("u1", "S3 Vectors mem0", limit=5)
    assert any("mem0" in m.memory for m in remaining)


def test_memory_is_isolated_by_user():
    service = MemoryService(FakeMemoryProvider())
    service.add("u1", [ChatMessage(role="user", content="用户一的秘密")])
    assert service.search("u2", "秘密", limit=5) == []


def test_memory_add_is_idempotent_by_request_id():
    service = MemoryService(FakeMemoryProvider(), idempotency_store=InMemoryIdempotencyStore())
    messages = [ChatMessage(role="user", content="只应写入一次")]

    first = service.add("u1", messages, request_id="req-123")
    second = service.add("u1", messages, request_id="req-123")

    assert first
    assert second == []
