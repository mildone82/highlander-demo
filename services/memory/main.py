from __future__ import annotations

from fastapi import FastAPI, HTTPException

from app.schemas import (
    MemoryAddRequest,
    MemoryAddResponse,
    MemoryDeleteResponse,
    MemorySearchRequest,
    MemorySearchResponse,
    MemoryUpdateRequest,
)
from services.memory.mem0_provider import build_memory_provider
from services.memory.service import MemoryService

app = FastAPI(title="knowledge-assistant-memory", version="0.1.0")
service = MemoryService(provider=build_memory_provider())


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@app.post("/memory/search", response_model=MemorySearchResponse)
def search(request: MemorySearchRequest) -> MemorySearchResponse:
    return MemorySearchResponse(
        memories=service.search(request.user_id, request.query, request.limit)
    )


@app.post("/memory/add", response_model=MemoryAddResponse)
def add(request: MemoryAddRequest) -> MemoryAddResponse:
    ids = service.add(request.user_id, request.messages, request.metadata)
    return MemoryAddResponse(memory_ids=ids)


@app.post("/memory/update/{memory_id}")
def update(memory_id: str, request: MemoryUpdateRequest) -> dict:
    try:
        service.update(memory_id, request.memory, request.metadata)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"updated": True}


@app.delete("/memory/{memory_id}", response_model=MemoryDeleteResponse)
def delete(memory_id: str) -> MemoryDeleteResponse:
    try:
        service.delete(memory_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return MemoryDeleteResponse(deleted=True)
