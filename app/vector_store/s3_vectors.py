"""Amazon S3 Vectors direct-API store (used in AWS China, no Bedrock KB)."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

from app.vector_store.base import SearchResult, VectorStore

logger = logging.getLogger(__name__)


class S3VectorsStore(VectorStore):
    """Thin, defensive wrapper over the boto3 ``s3vectors`` client.

    AWS China does not expose Bedrock Knowledge Bases, so knowledge indexing
    talks to S3 Vectors directly. ``endpoint_url`` can be supplied to work
    around aws-cn metadata lag in older botocore releases.
    """

    def __init__(
        self,
        bucket: str,
        index: str = "knowledge",
        dimension: int = 1024,
        distance: str = "cosine",
        region: str = "cn-north-1",
        endpoint_url: Optional[str] = None,
    ) -> None:
        self.bucket = bucket
        self.index_name = index
        self.dimension = dimension
        self.distance = distance
        self.descending = distance == "cosine"  # cosine returns similarity (higher is closer)
        kwargs: Dict[str, Any] = {"region_name": region}
        if endpoint_url:
            kwargs["endpoint_url"] = endpoint_url
        self.client = boto3.client("s3vectors", **kwargs)
        self._ensure_resources()

    def _ensure_resources(self) -> None:
        self._ensure_bucket()
        self._ensure_index()

    def _ensure_bucket(self) -> None:
        try:
            self.client.get_vector_bucket(vectorBucketName=self.bucket)
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") == "NotFoundException":
                logger.info("Creating S3 vector bucket %s", self.bucket)
                self.client.create_vector_bucket(vectorBucketName=self.bucket)
            else:
                raise

    def _ensure_index(self) -> None:
        try:
            self.client.get_index(vectorBucketName=self.bucket, indexName=self.index_name)
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") == "NotFoundException":
                logger.info("Creating S3 vector index %s/%s", self.bucket, self.index_name)
                self.client.create_index(
                    vectorBucketName=self.bucket,
                    indexName=self.index_name,
                    dataType="float32",
                    dimension=self.dimension,
                    distanceMetric=self.distance,
                )
            else:
                raise

    def put(
        self,
        ids: List[str],
        vectors: List[List[float]],
        payloads: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        payloads = payloads or [{} for _ in ids]
        if not (len(ids) == len(vectors) == len(payloads)):
            raise ValueError("ids, vectors, and payloads must have equal length")
        records = [
            {
                "key": vector_id,
                "data": {"float32": vector},
                "metadata": payload,
            }
            for vector_id, vector, payload in zip(ids, vectors, payloads)
        ]
        # S3 Vectors put_vectors has a per-call payload cap; chunk conservatively.
        batch_size = 100
        for start in range(0, len(records), batch_size):
            self.client.put_vectors(
                vectorBucketName=self.bucket,
                indexName=self.index_name,
                vectors=records[start : start + batch_size],
            )

    def _parse_metadata(self, raw: Any) -> Dict[str, Any]:
        if raw is None:
            return {}
        if isinstance(raw, str):
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                logger.warning("Failed to parse S3 Vectors metadata: %s", raw)
                return {}
        return dict(raw)

    def search(
        self,
        vector: List[float],
        top_k: int = 8,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        params: Dict[str, Any] = {
            "vectorBucketName": self.bucket,
            "indexName": self.index_name,
            "queryVector": {"float32": vector},
            "topK": top_k,
            "returnMetadata": True,
            "returnDistance": True,
        }
        if filters:
            params["filter"] = filters
        response = self.client.query_vectors(**params)
        results = [
            SearchResult(
                id=item.get("key", ""),
                score=float(item.get("distance", 0.0)),
                payload=self._parse_metadata(item.get("metadata")),
            )
            for item in response.get("vectors", [])
        ]
        results.sort(key=lambda r: r.score, reverse=self.descending)
        return results

    def delete(self, ids: List[str]) -> None:
        if not ids:
            return
        self.client.delete_vectors(
            vectorBucketName=self.bucket,
            indexName=self.index_name,
            keys=ids,
        )

    def get(self, vector_id: str) -> Optional[SearchResult]:
        response = self.client.get_vectors(
            vectorBucketName=self.bucket,
            indexName=self.index_name,
            keys=[vector_id],
            returnData=False,
            returnMetadata=True,
        )
        vectors = response.get("vectors", [])
        if not vectors:
            return None
        return SearchResult(
            id=vectors[0].get("key", vector_id),
            score=0.0,
            payload=self._parse_metadata(vectors[0].get("metadata")),
        )

    def count(self) -> int:
        total = 0
        paginator = self.client.get_paginator("list_vectors")
        for page in paginator.paginate(
            vectorBucketName=self.bucket,
            indexName=self.index_name,
            returnData=False,
            returnMetadata=False,
        ):
            total += len(page.get("vectors", []))
        return total
