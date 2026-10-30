"""Deterministic hashing embedder for local development and offline evals.

It is NOT a production embedder. It produces normalized bag-of-hashed-tokens
vectors so local smoke tests and recall experiments run with zero external
dependencies; production deployments use ``OpenAICompatibleEmbedder``.
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import List

from app.embedder.base import Embedder

_ASCII_WORD_RE = re.compile(r"[a-z0-9_]+")
_CJK_CHAR_RE = re.compile(r"[\u4e00-\u9fff]")


def tokenize(text: str) -> List[str]:
    """Split into ASCII words and CJK unigrams + bigrams.

    A contiguous CJK run has no spaces, so a plain ``\\w+`` regex would swallow
    an entire Chinese sentence as one token. Unigrams give overlap, bigrams add
    just enough order sensitivity for a deterministic local embedder.
    """
    lowered = text.lower()
    tokens = _ASCII_WORD_RE.findall(lowered)
    cjk_chars = _CJK_CHAR_RE.findall(lowered)
    tokens.extend(cjk_chars)
    tokens.extend(a + b for a, b in zip(cjk_chars, cjk_chars[1:]))
    return tokens


class LocalHashingEmbedder(Embedder):
    def __init__(self, dims: int = 64) -> None:
        if dims <= 0:
            raise ValueError("dims must be positive")
        self.dims = dims

    def _embed_one(self, text: str) -> List[float]:
        vector = [0.0] * self.dims
        for token in tokenize(text):
            digest = hashlib.md5(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dims
            vector[index] += 1.0
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]
        return vector

    def embed(self, texts: List[str]) -> List[List[float]]:
        return [self._embed_one(text) for text in texts]
