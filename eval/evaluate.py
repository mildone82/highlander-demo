"""Offline retrieval evaluation (recall@k and precision@k).

Runs with the deterministic hashing embedder + in-memory store, so it works
without AWS, a GPU, or a network. The production path swaps in the OpenAI-
compatible embedder and the S3 Vectors store via the same interfaces using the
``EMBEDDER_PROVIDER`` / ``VECTOR_STORE_PROVIDER`` environment variables.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.embedder import LocalHashingEmbedder
from app.vector_store import InMemoryVectorStore
from services.rag.service import RetrieveService


def load_documents() -> List[dict]:
    return [
        {"id": "doc1-chunk-0", "text": "S3 Vectors 在中国区支持单索引 20 亿向量，每桶 1 万索引，仅支持直连 API。", "source": "doc1"},
        {"id": "doc1-chunk-1", "text": "S3 Vectors 使用 cosine 或 euclidean 距离度量，向量维度由索引定义。", "source": "doc1"},
        {"id": "doc2-chunk-0", "text": "知识助手主推 Qwen 或 DeepSeek 作为生成模型，BGE-M3 作为嵌入模型。", "source": "doc2"},
        {"id": "doc3-chunk-0", "text": "记忆按 user_id、agent_id、run_id 三级隔离，MVP 使用 user_id。", "source": "doc3"},
        {"id": "doc3-chunk-1", "text": "知识库数据由入库 Worker 写入，RAG 服务只读。", "source": "doc3"},
        {"id": "doc3-chunk-2", "text": "多租户时以 namespace/collection 前缀和 IAM 做租户级隔离。", "source": "doc3"},
        {"id": "doc4-chunk-0", "text": "Multica 平台提供命令行工具与工作区。", "source": "doc4"},
        {"id": "doc4-chunk-1", "text": "使用 multica repo checkout 命令可以拉取工作仓库。", "source": "doc4"},
        {"id": "doc5-chunk-0", "text": "记忆写入通过 SQS 异步解耦，worker 消费后写入 mem0。", "source": "doc5"},
        {"id": "doc5-chunk-1", "text": "memory_add 以 request_id 为键在 DynamoDB 上做幂等去重。", "source": "doc5"},
        {"id": "doc6-chunk-0", "text": "入库 worker 支持 PDF 与 DOCX 文档解析后再分块。", "source": "doc6"},
        {"id": "doc6-chunk-1", "text": "分块器优先按段落与句子边界切分，并保留重叠。", "source": "doc6"},
    ]


def load_dataset(path: str) -> List[dict]:
    items = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                items.append(json.loads(line))
    return items


def build_service(top_k: int = 4) -> RetrieveService:
    if os.getenv("VECTOR_STORE_PROVIDER") == "s3_vectors":
        from app.config import EmbedderSettings, VectorStoreSettings
        from app.embedder import OpenAICompatibleEmbedder
        from app.vector_store import S3VectorsStore

        embedder = OpenAICompatibleEmbedder(
            base_url=EmbedderSettings.base_url,
            api_key=EmbedderSettings.api_key,
            model=EmbedderSettings.model,
            dimensions=EmbedderSettings.dims,
            timeout=EmbedderSettings.timeout_s,
        )
        store = S3VectorsStore(
            bucket=VectorStoreSettings.bucket,
            index=VectorStoreSettings.index,
            dimension=VectorStoreSettings.dimension,
            distance=VectorStoreSettings.distance,
            region=VectorStoreSettings.region,
            endpoint_url=VectorStoreSettings.endpoint_url or None,
        )
    else:
        embedder = LocalHashingEmbedder(dims=int(os.getenv("EVAL_EMBEDDER_DIMS", "64")))
        store = InMemoryVectorStore()
        docs = load_documents()
        store.put(
            ids=[d["id"] for d in docs],
            vectors=embedder.embed([d["text"] for d in docs]),
            payloads=[{"text": d["text"], "source": d["source"]} for d in docs],
        )
    service = RetrieveService(embedder, store)
    return service


def evaluate(dataset_path: str, top_k: int = 4) -> Dict[str, Any]:
    service = build_service(top_k)

    per_query_recall = []
    per_query_precision = []
    for item in load_dataset(dataset_path):
        response = service.retrieve(item["query"], top_k=top_k)
        retrieved = {c.id for c in response.chunks}
        relevant = set(item["relevant"])
        hits = len(retrieved & relevant)
        recall = hits / len(relevant) if relevant else 0.0
        precision = hits / top_k
        per_query_recall.append(recall)
        per_query_precision.append(precision)
        print(f"{item['id']}: recall@{top_k}={recall:.2f} precision@{top_k}={precision:.2f}")

    mean_recall = sum(per_query_recall) / len(per_query_recall) if per_query_recall else 0.0
    mean_precision = sum(per_query_precision) / len(per_query_precision) if per_query_precision else 0.0
    print(f"mean recall@{top_k} = {mean_recall:.3f}; mean precision@{top_k} = {mean_precision:.3f}")
    return {
        "mean_recall": mean_recall,
        "mean_precision": mean_precision,
        "n": len(per_query_recall),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run offline retrieval eval")
    parser.add_argument("--dataset", default=os.path.join(os.path.dirname(__file__), "dataset.jsonl"))
    parser.add_argument("--top-k", type=int, default=4)
    args = parser.parse_args()
    evaluate(args.dataset, args.top_k)
    return 0


if __name__ == "__main__":
    sys.exit(main())
