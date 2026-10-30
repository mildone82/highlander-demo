"""Dependency-free text chunking for the ingestion worker."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

_PARAGRAPH_RE = re.compile(r"\n\s*\n|\r\n\s*\r\n")
_SENTENCE_RE = re.compile(r"(?<=[。！？.!?])\s*")


@dataclass
class TextChunk:
    text: str
    metadata: dict


def chunk_text(
    text: str,
    source: str,
    max_chars: int = 800,
    overlap_chars: int = 100,
) -> List[TextChunk]:
    """Split text into overlapping chunks bounded by ``max_chars``.

    Prefers paragraph boundaries, then sentence boundaries, then a hard cut for
    over-long sentences. Adjacent chunks share ``overlap_chars`` characters so a
    fact split across a boundary remains retrievable. Each chunk records its
    source and ordinal for idempotent indexing.
    """
    text = text.strip()
    if not text:
        return []
    if max_chars <= overlap_chars:
        raise ValueError("max_chars must be greater than overlap_chars")

    chunks: List[TextChunk] = []
    for paragraph in [p.strip() for p in _PARAGRAPH_RE.split(text) if p.strip()]:
        sentences = [s.strip() for s in _SENTENCE_RE.split(paragraph) if s.strip()]
        for piece in _chunk_sentences(sentences, max_chars, overlap_chars):
            chunks.append(
                TextChunk(text=piece, metadata={"source": source, "ordinal": len(chunks)})
            )
    return chunks


def _chunk_sentences(sentences: List[str], max_chars: int, overlap_chars: int) -> List[str]:
    """Pack sentences into ``max_chars`` chunks, carrying ``overlap_chars`` forward."""
    chunks: List[str] = []
    current = ""
    for sentence in sentences:
        if not sentence:
            continue
        if len(sentence) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(_hard_cut(sentence, max_chars, overlap_chars))
            continue
        if not current:
            current = sentence
            continue
        if len(current) + len(sentence) <= max_chars:
            current += sentence
            continue
        chunks.append(current)
        tail = current[-overlap_chars:] if overlap_chars else ""
        current = tail + sentence
        if len(current) > max_chars:
            chunks.extend(_hard_cut(sentence, max_chars, overlap_chars))
            current = ""
    if current:
        chunks.append(current)
    return chunks


def _hard_cut(segment: str, max_chars: int, overlap_chars: int) -> List[str]:
    """Split an over-long segment into ``max_chars`` pieces sharing an overlap."""
    pieces: List[str] = []
    start = 0
    while start < len(segment):
        end = min(len(segment), start + max_chars)
        piece = segment[start:end]
        pieces.append(piece)
        if end >= len(segment):
            break
        start = end - overlap_chars
    return pieces
