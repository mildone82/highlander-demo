"""One-time bootstrap for S3 Vectors bucket + knowledge/memory indexes.

Terraform's AWS provider does not yet expose S3 Vectors resources, so this is a
documented post-apply step. Run from an environment with aws-cn credentials and
the s3vectors service enabled in boto3.
"""

from __future__ import annotations

import argparse
import sys

import boto3
from botocore.exceptions import ClientError


def ensure_bucket(client, name: str) -> None:
    try:
        client.get_vector_bucket(vectorBucketName=name)
        print(f"bucket exists: {name}")
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") != "NotFoundException":
            raise
        client.create_vector_bucket(vectorBucketName=name)
        print(f"bucket created: {name}")


def ensure_index(client, bucket: str, name: str, dimension: int, distance: str) -> None:
    try:
        client.get_index(vectorBucketName=bucket, indexName=name)
        print(f"index exists: {bucket}/{name}")
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") != "NotFoundException":
            raise
        client.create_index(
            vectorBucketName=bucket,
            indexName=name,
            dataType="float32",
            dimension=dimension,
            distanceMetric=distance,
        )
        print(f"index created: {bucket}/{name}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket", default="knowledge-assistant-vectors")
    parser.add_argument("--dimension", type=int, default=1024)
    parser.add_argument("--region", default="cn-north-1")
    args = parser.parse_args()

    client = boto3.client("s3vectors", region_name=args.region)
    ensure_bucket(client, args.bucket)
    ensure_index(client, args.bucket, "knowledge", args.dimension, "cosine")
    ensure_index(client, args.bucket, "memory", args.dimension, "cosine")
    print("S3 Vectors bootstrap complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
