import time

from services.model_gateway.circuit import CircuitBreaker
from services.model_gateway.router import ModelRouter


def test_fake_completion_is_deterministic():
    router = ModelRouter(providers=[])
    result = router.complete(
        [{"role": "user", "content": "你好"}],
        model="qwen",
        temperature=0.2,
        max_tokens=10,
    )
    assert result["choices"][0]["message"]["content"] == "回答：你好"


def test_fake_embedding_dimension():
    router = ModelRouter(providers=[])
    vectors = router.embed(["hello", "world"], model="bge-m3", dimensions=32)
    assert len(vectors) == 2
    assert all(len(v) == 32 for v in vectors)


def test_circuit_breaker_opens_then_half_opens():
    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout_s=30.0)
    assert breaker.allow()
    breaker.record_failure()
    assert breaker.allow()
    breaker.record_failure()
    assert not breaker.allow()  # now open
    breaker._opened_at = time.monotonic() - 31.0  # simulate cooldown elapsed
    assert breaker.allow()  # half-open probe resets
