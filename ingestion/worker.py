"""Ingestion worker: poll SQS, parse, chunk, vectorize, index."""

from __future__ import annotations

import json
import logging
import os
from typing import Optional

from ingestion.chunker import chunk_text
from ingestion.idempotency import DynamoDBIdempotencyStore, InMemoryIdempotencyStore
from ingestion.indexer import Indexer

logger = logging.getLogger(__name__)


class SQSWorker:
    """Long-polling SQS consumer. Exits cleanly on KeyboardInterrupt."""

    def __init__(self, indexer: Indexer, queue_url: str, region: str = "cn-north-1") -> None:
        import boto3

        self.indexer = indexer
        self.queue_url = queue_url
        self.sqs = boto3.client("sqs", region_name=region)

    def run(self, wait_seconds: int = 20, max_messages: int = 10) -> None:
        logger.info("Ingestion worker polling %s", self.queue_url)
        while True:
            response = self.sqs.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=max_messages,
                WaitTimeSeconds=wait_seconds,
                VisibilityTimeout=120,
            )
            for message in response.get("Messages", []):
                self._handle(message)

    def _handle(self, message: dict) -> None:
        receipt = message.get("ReceiptHandle")
        try:
            event = json.loads(message.get("Body", "{}"))
            records = event.get("Records", [])
            if not records:
                self._ack(receipt)
                return
            for record in records:
                source = record.get("s3", {}).get("object", {}).get("key", "unknown")
                text = record.get("text", "")
                if not text:
                    text = self._download_text(record)
                chunks = chunk_text(text, source=source)
                self.indexer.index_chunks(chunks)
            self._ack(receipt)
        except Exception as exc:  # noqa: BLE001 - DLQ is the safety net
            logger.exception("Failed to process message: %s", exc)

    def _ack(self, receipt: Optional[str]) -> None:
        if receipt:
            self.sqs.delete_message(QueueUrl=self.queue_url, ReceiptHandle=receipt)

    def _download_text(self, record: dict) -> str:
        import boto3

        s3 = boto3.client("s3")
        bucket = record.get("s3", {}).get("bucket", {}).get("name", "")
        key = record.get("s3", {}).get("object", {}).get("key", "")
        body = s3.get_object(Bucket=bucket, Key=key)["Body"].read()
        return body.decode("utf-8", errors="replace")


def build_local_indexer() -> Indexer:
    from app.embedder import LocalHashingEmbedder
    from app.vector_store import InMemoryVectorStore

    return Indexer(LocalHashingEmbedder(), InMemoryVectorStore(), InMemoryIdempotencyStore())
