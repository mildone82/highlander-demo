"""Ingestion worker: poll SQS, parse, chunk, vectorize, index."""

from __future__ import annotations

import argparse
import json
import logging
import os
from typing import Optional

from ingestion.chunker import chunk_text
from ingestion.idempotency import DynamoDBIdempotencyStore, InMemoryIdempotencyStore
from ingestion.indexer import Indexer
from ingestion.parser import parse_document

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
        return parse_document(key, body)


def build_local_indexer() -> Indexer:
    from app.embedder import LocalHashingEmbedder
    from app.vector_store import InMemoryVectorStore

    return Indexer(LocalHashingEmbedder(), InMemoryVectorStore(), InMemoryIdempotencyStore())


def build_indexer_from_env() -> Indexer:
    """Production indexer assembled from the same env vars as the RAG service."""
    from app.config import EmbedderSettings, VectorStoreSettings
    from app.embedder import LocalHashingEmbedder, OpenAICompatibleEmbedder
    from app.vector_store import InMemoryVectorStore, S3VectorsStore

    if EmbedderSettings.provider == "openai":
        embedder = OpenAICompatibleEmbedder(
            base_url=EmbedderSettings.base_url,
            api_key=EmbedderSettings.api_key,
            model=EmbedderSettings.model,
            dimensions=EmbedderSettings.dims,
            timeout=EmbedderSettings.timeout_s,
        )
    else:
        embedder = LocalHashingEmbedder(dims=EmbedderSettings.dims)

    if VectorStoreSettings.provider == "s3_vectors":
        store = S3VectorsStore(
            bucket=VectorStoreSettings.bucket,
            index=VectorStoreSettings.index,
            dimension=VectorStoreSettings.dimension,
            distance=VectorStoreSettings.distance,
            region=VectorStoreSettings.region,
            endpoint_url=VectorStoreSettings.endpoint_url or None,
        )
    else:
        store = InMemoryVectorStore()

    table = os.getenv("INGESTION_STATE_TABLE", "")
    idempotency = (
        DynamoDBIdempotencyStore(table, VectorStoreSettings.region)
        if table
        else InMemoryIdempotencyStore()
    )
    return Indexer(embedder, store, idempotency)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    parser = argparse.ArgumentParser(description="Drain the ingestion SQS queue")
    parser.add_argument("--queue-url", default=os.getenv("INGESTION_QUEUE_URL", ""))
    args = parser.parse_args()

    queue_url = args.queue_url
    if not queue_url:
        raise SystemExit("INGESTION_QUEUE_URL or --queue-url is required")

    worker = SQSWorker(
        indexer=build_indexer_from_env(),
        queue_url=queue_url,
        region=os.getenv("VECTOR_REGION", "cn-north-1"),
    )
    worker.run()
    return 0


if __name__ == "__main__":
    main()
