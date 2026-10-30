"""Memory write worker: drain the memory SQS queue and call mem0 synchronously.

Each message carries a ``request_id`` used for idempotent dedup so SQS
redelivery (or a half-failed write) does not duplicate memories.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from typing import Optional

from app.schemas import ChatMessage
from ingestion.idempotency import DynamoDBIdempotencyStore, InMemoryIdempotencyStore
from services.memory.mem0_provider import build_memory_provider
from services.memory.service import MemoryService

logger = logging.getLogger(__name__)


class MemoryWriteWorker:
    def __init__(self, service: MemoryService, queue_url: str, region: str = "cn-north-1") -> None:
        import boto3

        self.service = service
        self.queue_url = queue_url
        self.sqs = boto3.client("sqs", region_name=region)

    def run(self, wait_seconds: int = 20, max_messages: int = 10) -> None:
        logger.info("Memory worker polling %s", self.queue_url)
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
            payload = json.loads(message.get("Body", "{}"))
            self.service.add(
                user_id=payload.get("user_id", "default"),
                messages=[ChatMessage(**m) for m in payload.get("messages", [])],
                metadata=payload.get("metadata") or {},
                request_id=payload.get("request_id"),
            )
            self._ack(receipt)
        except Exception as exc:  # noqa: BLE001 - DLQ redrive policy is the safety net
            logger.exception("Failed to write memory: %s", exc)

    def _ack(self, receipt: Optional[str]) -> None:
        if receipt:
            self.sqs.delete_message(QueueUrl=self.queue_url, ReceiptHandle=receipt)


def build_service() -> MemoryService:
    provider = build_memory_provider()
    table = os.getenv("MEMORY_IDEMPOTENCY_TABLE", "")
    region = os.getenv("MEMORY_VECTOR_REGION", "cn-north-1")
    store = DynamoDBIdempotencyStore(table, region) if table else InMemoryIdempotencyStore()
    return MemoryService(provider, idempotency_store=store)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    parser = argparse.ArgumentParser(description="Drain the memory write queue")
    parser.add_argument("--queue-url", default=os.getenv("MEMORY_WRITE_QUEUE_URL", ""))
    args = parser.parse_args()

    queue_url = args.queue_url
    if not queue_url:
        raise SystemExit("MEMORY_WRITE_QUEUE_URL or --queue-url is required")

    worker = MemoryWriteWorker(
        service=build_service(),
        queue_url=queue_url,
        region=os.getenv("MEMORY_VECTOR_REGION", "cn-north-1"),
    )
    worker.run()
    return 0


if __name__ == "__main__":
    main()
