from ingestion.chunker import chunk_text


def test_chunk_short_text_returns_single_chunk():
    chunks = chunk_text("一句话文档。", source="a.txt")
    assert len(chunks) == 1
    assert chunks[0].metadata["source"] == "a.txt"
    assert chunks[0].metadata["ordinal"] == 0


def test_chunk_long_text_splits_within_limit():
    text = "这是第一句。" + "这是第二句。" * 500
    chunks = chunk_text(text, source="long.txt", max_chars=300)
    assert all(len(c.text) <= 300 for c in chunks)
    assert len(chunks) > 1
    ordinals = [c.metadata["ordinal"] for c in chunks]
    assert ordinals == list(range(len(chunks)))


def test_chunk_empty_text():
    assert chunk_text("   \n\n ", source="empty.txt") == []
