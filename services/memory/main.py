from __future__ import annotations

import os
import uuid

from fastapi import FastAPI, HTTPException

from app.schemas import (
    MemoryAddRequest,
    MemoryAddResponse,
    MemoryDeleteResponse,
    MemorySearchRequest,
    MemorySearchResponse,
    MemoryUpdateRequest,
)
from ingestion.idempotency import DynamoDBIdempotencyStore, InMemoryIdempotencyStore
from services.memory.mem0_provider import build_memory_provider
from services.memory.queue import MemoryWriteQueue
from services.memory.service import MemoryService

app = FastAPI(title="knowledge-assistant-memory", version="0.1.0")


def _build_service() -> MemoryService:
    table = os.getenv("MEMORY_IDEMPOTENCY_TABLE", "")
    region = os.getenv("MEMORY_VECTOR_REGION", "cn-north-1")
    store = DynamoDBIdempotencyStore(table, region) if table else InMemoryIdempotencyStore()
    return MemoryService(provider=build_memory_provider(), idempotency_store=store)


service = _build_service()
_queue_url = os.getenv("MEMORY_WRITE_QUEUE_URL", "")
queue = MemoryWriteQueue(_queue_url, os.getenv("MEMORY_VECTOR_REGION", "cn-north-1")) if _queue_url else None


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
    if queue is not None:
        request_id = request.request_id or uuid.uuid4().hex
        queue.enqueue(
            {
                "user_id": request.user_id,
                "messages": [message.model_dump() for message in request.messages],
                "metadata": request.metadata,
                "request_id": request_id,
            }
        )
        return MemoryAddResponse(memory_ids=[], request_id=request_id, queued=True)
    ids = service.add(request.user_id, request.messages, request.metadata, request.request_id)
    return MemoryAddResponse(memory_ids=ids, request_id=request.request_id, queued=False)


@app.post("/memory/update/{memory_id}")
def update(memory_id: str, request: MemoryUpdateRequest) -> dict:
    try:
        service.update(memory_id, request.memory, request.metadata)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        # mem0 raises ValueError (not KeyError) for an unknown memory_id.
        if "not found" in str(exc).lower():
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"updated": True}


@app.delete("/memory/{memory_id}", response_model=MemoryDeleteResponse)
def delete(memory_id: str) -> MemoryDeleteResponse:
    try:
        service.delete(memory_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        if "not found" in str(exc).lower():
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return MemoryDeleteResponse(deleted=True)
