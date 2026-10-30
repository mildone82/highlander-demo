from __future__ import annotations

from fastapi import FastAPI

from app.schemas import RetrieveRequest, RetrieveResponse
from services.rag.service import RetrieveService, build_embedder, build_vector_store

app = FastAPI(title="knowledge-assistant-rag", version="0.1.0")
service = RetrieveService(embedder=build_embedder(), vector_store=build_vector_store())


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "vectors": service.vector_store.count()}


@app.post("/retrieve", response_model=RetrieveResponse)
def retrieve(request: RetrieveRequest) -> RetrieveResponse:
    return service.retrieve(
        query=request.query,
        top_k=request.top_k,
    )
