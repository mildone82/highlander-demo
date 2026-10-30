import sys
from unittest import mock

from app.schemas import ChatMessage
from services.memory.mem0_provider import Mem0Provider


def _fake_mem0_module() -> mock.MagicMock:
    """Install a stub ``mem0`` package so tests run without the real dependency."""
    fake_memory = mock.MagicMock()
    module = mock.MagicMock()
    module.Memory.from_config.return_value = fake_memory
    sys.modules["mem0"] = module
    return fake_memory


def test_mem0_update_uses_text_and_metadata_keywords():
    fake_memory = _fake_mem0_module()
    try:
        provider = Mem0Provider()
        provider.update("mem-1", "更正后的记忆", {"source": "privacy"})
    finally:
        sys.modules.pop("mem0", None)

    fake_memory.update.assert_called_once_with(
        "mem-1", text="更正后的记忆", metadata={"source": "privacy"}
    )


def test_mem0_add_scopes_by_identity_and_metadata():
    fake_memory = _fake_mem0_module()
    fake_memory.add.return_value = {"results": [{"id": "mem-9"}]}
    try:
        provider = Mem0Provider()
        ids = provider.add(
            "u1",
            [ChatMessage(role="user", content="我喜欢 S3 Vectors")],
            {"topic": "storage"},
        )
    finally:
        sys.modules.pop("mem0", None)

    assert ids == ["mem-9"]
    assert fake_memory.add.call_args.kwargs["user_id"] == "u1"
    assert fake_memory.add.call_args.kwargs["metadata"] == {"topic": "storage"}
    assert fake_memory.add.call_args.kwargs["infer"] is True
