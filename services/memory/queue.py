"""SQS transport for asynchronous memory writes.

When ``MEMORY_WRITE_QUEUE_URL`` is set, the memory service enqueues writes
instead of calling mem0 inline. A separate memory worker drains the queue so a
slow embedding/LLM call never blocks the request path.
"""

from __future__ import annotations

import json
from typing import Any, Dict


class MemoryWriteQueue:
    def __init__(self, queue_url: str, region: str = "cn-north-1") -> None:
        import boto3

        self.queue_url = queue_url
        self.sqs = boto3.client("sqs", region_name=region)

    def enqueue(self, payload: Dict[str, Any]) -> str:
        response = self.sqs.send_message(
            QueueUrl=self.queue_url,
            MessageBody=json.dumps(payload, ensure_ascii=False),
        )
        return response.get("MessageId", "")
