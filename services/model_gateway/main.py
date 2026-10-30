from __future__ import annotations

from fastapi import FastAPI, HTTPException

from app.schemas import (
    CompletionRequest,
    CompletionResponse,
    EmbeddingData,
    EmbeddingRequest,
    EmbeddingResponse,
)
from services.model_gateway.router import ModelRouter

app = FastAPI(title="knowledge-assistant-model-gateway", version="0.1.0")
router = ModelRouter()


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "mode": "fake" if router.fake else "routed"}


@app.post("/v1/chat/completions", response_model=CompletionResponse)
def chat_completions(request: CompletionRequest) -> CompletionResponse:
    try:
        result = router.complete(
            [message.model_dump() for message in request.messages],
            request.model,
            request.temperature,
            request.max_tokens,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return CompletionResponse(**result)


@app.post("/v1/embeddings", response_model=EmbeddingResponse)
def embeddings(request: EmbeddingRequest) -> EmbeddingResponse:
    try:
        vectors = router.embed(request.input, request.model, request.dimensions)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    data = [
        EmbeddingData(object="embedding", index=index, embedding=vector)
        for index, vector in enumerate(vectors)
    ]
    return EmbeddingResponse(
        object="list",
        model=request.model,
        data=data,
        usage={"prompt_tokens": sum(len(t.split()) for t in request.input), "total_tokens": len(data)},
    )
