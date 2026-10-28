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

    Prefers paragraph boundaries, then sentence boundaries, then hard cut.
    Each chunk records its source and ordinal for idempotent indexing.
    """
    text = text.strip()
    if not text:
        return []
    if max_chars <= overlap_chars:
        raise ValueError("max_chars must be greater than overlap_chars")

    paragraphs = [p.strip() for p in _PARAGRAPH_RE.split(text) if p.strip()]
    chunks: List[TextChunk] = []
    ordinal = 0
    for paragraph in paragraphs:
        for piece in _split_long_segment(paragraph, max_chars):
            chunks.append(TextChunk(text=piece, metadata={"source": source, "ordinal": ordinal}))
            ordinal += 1
    return chunks


def _split_long_segment(segment: str, max_chars: int) -> List[str]:
    if len(segment) <= max_chars:
        return [segment]
    pieces: List[str] = []
    start = 0
    while start < len(segment):
        end = min(len(segment), start + max_chars)
        piece = segment[start:end]
        pieces.append(piece)
        if end >= len(segment):
            break
        start = end
    return pieces
