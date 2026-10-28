from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from app.config import EmbedderSettings, VectorStoreSettings
from app.embedder import Embedder, LocalHashingEmbedder, OpenAICompatibleEmbedder
from app.schemas import Chunk, RetrieveResponse
from app.vector_store import InMemoryVectorStore, S3VectorsStore, VectorStore


def build_embedder() -> Embedder:
    if EmbedderSettings.provider == "openai":
        return OpenAICompatibleEmbedder(
            base_url=EmbedderSettings.base_url,
            api_key=EmbedderSettings.api_key,
            model=EmbedderSettings.model,
            dimensions=EmbedderSettings.dims,
            timeout=EmbedderSettings.timeout_s,
        )
    return LocalHashingEmbedder(dims=EmbedderSettings.dims)


def build_vector_store() -> VectorStore:
    if VectorStoreSettings.provider == "s3_vectors":
        return S3VectorsStore(
            bucket=VectorStoreSettings.bucket,
            index=VectorStoreSettings.index,
            dimension=VectorStoreSettings.dimension,
            distance=VectorStoreSettings.distance,
            region=VectorStoreSettings.region,
            endpoint_url=VectorStoreSettings.endpoint_url or None,
        )
    return InMemoryVectorStore()


class RetrieveService:
    """Owns the retrieval semantic: embed -> S3 Vectors top-k -> chunks."""

    def __init__(self, embedder: Embedder, vector_store: VectorStore) -> None:
        self.embedder = embedder
        self.vector_store = vector_store

    def retrieve(
        self,
        query: str,
        top_k: int = 8,
        filters: Optional[Dict[str, Any]] = None,
    ) -> RetrieveResponse:
        if not query.strip():
            return RetrieveResponse(chunks=[])
        started = time.perf_counter()
        query_vector = self.embedder.embed([query])[0]
        results = self.vector_store.search(query_vector, top_k=top_k, filters=filters)
        chunks = [
            Chunk(
                id=result.id,
                text=result.payload.get("text", ""),
                score=result.score,
                metadata={k: v for k, v in result.payload.items() if k != "text"},
            )
            for result in results
        ]
        latency_ms = (time.perf_counter() - started) * 1000.0
        return RetrieveResponse(chunks=chunks, latency_ms=latency_ms)
