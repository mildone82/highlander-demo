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


def test_chunk_splits_on_sentence_boundaries():
    text = "第一句。第二句！第三句？"
    chunks = chunk_text(text, source="sentences.txt", max_chars=4, overlap_chars=1)
    assert len(chunks) > 1
    # Every chunk must be bounded by max_chars and keep sentence terminators intact.
    assert all(len(c.text) <= 4 for c in chunks)
    joined = "".join(c.text for c in chunks)
    assert "第一句" in joined and "第三句" in joined


def test_chunk_carries_overlap_between_chunks():
    text = "A B C D E F G H"
    chunks = chunk_text(text, source="overlap.txt", max_chars=5, overlap_chars=2)
    assert all(len(c.text) <= 5 for c in chunks)
    assert len(chunks) > 1
    assert chunks[0].text.endswith(chunks[1].text[:2])


def test_chunk_rejects_overlap_not_smaller_than_max():
    try:
        chunk_text("x", source="bad.txt", max_chars=3, overlap_chars=3)
    except ValueError:
        return
    raise AssertionError("expected ValueError for overlap_chars >= max_chars")
