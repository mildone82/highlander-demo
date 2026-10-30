"""Vectorize chunks and write them to the knowledge index."""

from __future__ import annotations

from typing import List

from app.embedder import Embedder
from app.vector_store import VectorStore
from ingestion.chunker import TextChunk
from ingestion.idempotency import IdempotencyStore, document_key


class Indexer:
    def __init__(
        self,
        embedder: Embedder,
        vector_store: VectorStore,
        idempotency: IdempotencyStore,
        batch_size: int = 32,
    ) -> None:
        self.embedder = embedder
        self.vector_store = vector_store
        self.idempotency = idempotency
        self.batch_size = batch_size

    def index_chunks(self, chunks: List[TextChunk]) -> int:
        pending = [c for c in chunks if not self.idempotency.is_done(document_key(c.metadata["source"], c.metadata["ordinal"], c.text))]
        indexed = 0
        for start in range(0, len(pending), self.batch_size):
            batch = pending[start : start + self.batch_size]
            vectors = self.embedder.embed([c.text for c in batch])
            ids = []
            payloads = []
            for chunk, vector in zip(batch, vectors):
                key = document_key(chunk.metadata["source"], chunk.metadata["ordinal"], chunk.text)
                ids.append(key)
                payloads.append(
                    {
                        "text": chunk.text,
                        "source": chunk.metadata["source"],
                        "ordinal": chunk.metadata["ordinal"],
                        "namespace": "knowledge",
                    }
                )
            self.vector_store.put(ids, vectors, payloads)
            for key in ids:
                self.idempotency.mark_done(key)
            indexed += len(batch)
        return indexed
