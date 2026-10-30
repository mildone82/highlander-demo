"""Local ingestion CLI for testing document -> vector index."""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion.chunker import chunk_text
from ingestion.indexer import Indexer


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest a text file into the knowledge index")
    parser.add_argument("path", help="Text file or directory to ingest")
    parser.add_argument("--max-chars", type=int, default=800)
    args = parser.parse_args()

    from app.embedder import LocalHashingEmbedder
    from app.vector_store import InMemoryVectorStore
    from ingestion.idempotency import InMemoryIdempotencyStore

    import os

    paths = []
    if os.path.isdir(args.path):
        for root, _dirs, files in os.walk(args.path):
            for name in files:
                paths.append(os.path.join(root, name))
    else:
        paths = [args.path]

    indexer = Indexer(LocalHashingEmbedder(), InMemoryVectorStore(), InMemoryIdempotencyStore())
    total = 0
    for path in paths:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            text = handle.read()
        chunks = chunk_text(text, source=os.path.basename(path), max_chars=args.max_chars)
        total += indexer.index_chunks(chunks)
    print(f"Indexed {total} chunks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
