"""Orchestrates the full retrieval pipeline: router -> (parallel structural
+ semantic recall) -> fusion, per docs/ARCHITECTURE.md. This is the single
entry point Phase 5's FastAPI endpoint calls.

Usage:
    python -m retrieval.pipeline "what's causing the outage tickets near tower-014?"
"""

import sys
from concurrent.futures import ThreadPoolExecutor

from . import graph_retrieval, vector_retrieval
from .fusion import fuse
from .router import classify


def retrieve(question: str, top_k: int = 10) -> dict:
    mode = classify(question)

    if mode == "structural":
        structural = graph_retrieval.run_structural_query(question, limit=top_k)
        return {"question": question, "mode": mode, "structural": structural, "semantic": None, "fused": None}

    if mode == "semantic":
        semantic = vector_retrieval.search(question, top_k=top_k)
        return {"question": question, "mode": mode, "structural": None, "semantic": semantic, "fused": None}

    # hybrid — structural and semantic recall are independent of each other,
    # and both are I/O-bound (Neo4j / Qdrant / vLLM network calls), so run
    # them on separate threads rather than sequentially. The underlying
    # clients (neo4j driver, requests, qdrant-client) are all synchronous,
    # so a thread pool is the straightforward way to get real concurrency
    # here without switching the whole retrieval layer to async clients.
    with ThreadPoolExecutor(max_workers=2) as executor:
        structural_future = executor.submit(graph_retrieval.structural_ticket_recall, question, top_k * 2)
        semantic_future = executor.submit(vector_retrieval.search, question, top_k * 2)
        structural = structural_future.result()
        semantic = semantic_future.result()

    fused = fuse(structural["hits"], semantic, top_k=top_k)
    return {"question": question, "mode": mode, "structural": structural, "semantic": semantic, "fused": fused}


def main():
    question = " ".join(sys.argv[1:]) or "What's causing the recent outage tickets?"
    result = retrieve(question)
    import json

    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
