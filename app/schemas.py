"""Pydantic models shared by the RAG, memory, and model-gateway services."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str
    content: str


class RetrieveRequest(BaseModel):
    query: str
    top_k: int = 8
    user_id: str = "default"
    request_id: Optional[str] = None


class Chunk(BaseModel):
    id: str
    text: str
    score: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RetrieveResponse(BaseModel):
    chunks: List[Chunk] = Field(default_factory=list)
    latency_ms: float = 0.0


class MemoryItem(BaseModel):
    id: Optional[str] = None
    memory: str = ""
    score: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MemorySearchRequest(BaseModel):
    user_id: str = "default"
    query: str
    limit: int = 5


class MemorySearchResponse(BaseModel):
    memories: List[MemoryItem] = Field(default_factory=list)


class MemoryAddRequest(BaseModel):
    user_id: str = "default"
    messages: List[ChatMessage]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    request_id: Optional[str] = None


class MemoryAddResponse(BaseModel):
    memory_ids: List[str] = Field(default_factory=list)
    request_id: Optional[str] = None
    queued: bool = False


class MemoryUpdateRequest(BaseModel):
    memory: str
    metadata: Optional[Dict[str, Any]] = None


class MemoryDeleteResponse(BaseModel):
    deleted: bool = True


class CompletionRequest(BaseModel):
    model: str = "default"
    messages: List[ChatMessage]
    temperature: float = 0.2
    max_tokens: int = 1024
    stream: bool = False


class CompletionChoice(BaseModel):
    index: int = 0
    message: ChatMessage
    finish_reason: str = "stop"


class CompletionUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class CompletionResponse(BaseModel):
    id: str = "chatcmpl-local"
    object: str = "chat.completion"
    model: str = "default"
    choices: List[CompletionChoice] = Field(default_factory=list)
    usage: CompletionUsage = Field(default_factory=CompletionUsage)


class EmbeddingRequest(BaseModel):
    input: List[str]
    model: str = "default"
    dimensions: Optional[int] = None


class EmbeddingData(BaseModel):
    object: str = "embedding"
    index: int = 0
    embedding: List[float]


class EmbeddingResponse(BaseModel):
    object: str = "list"
    model: str = "default"
    data: List[EmbeddingData] = Field(default_factory=list)
    usage: Dict[str, int] = Field(default_factory=dict)
