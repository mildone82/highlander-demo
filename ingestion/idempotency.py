"""Idempotency bookkeeping for the ingestion pipeline (design: request_id key)."""

from __future__ import annotations

import hashlib
import threading
from abc import ABC, abstractmethod
from typing import Optional


class IdempotencyStore(ABC):
    @abstractmethod
    def is_done(self, key: str) -> bool:
        """True if this ingest key was already indexed successfully."""

    @abstractmethod
    def mark_done(self, key: str) -> None:
        """Record a successful index operation."""


def document_key(source: str, ordinal: int, content: str) -> str:
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
    return f"{source}#{ordinal}#{digest}"


class InMemoryIdempotencyStore(IdempotencyStore):
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._done: set = set()

    def is_done(self, key: str) -> bool:
        with self._lock:
            return key in self._done

    def mark_done(self, key: str) -> None:
        with self._lock:
            self._done.add(key)


class DynamoDBIdempotencyStore(IdempotencyStore):
    """DynamoDB-backed store with conditional put for exactly-once semantics."""

    def __init__(self, table: str, region: str = "cn-north-1") -> None:
        import boto3

        self._table = boto3.resource("dynamodb", region_name=region).Table(table)

    def is_done(self, key: str) -> bool:
        item = self._table.get_item(Key={"request_id": key}).get("Item")
        return item is not None

    def mark_done(self, key: str) -> None:
        self._table.put_item(
            Item={"request_id": key, "status": "indexed"},
            ConditionExpression="attribute_not_exists(request_id)",
        )
