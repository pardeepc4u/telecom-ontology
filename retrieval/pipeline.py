"""Orchestrates the full retrieval pipeline: router -> (parallel structural
+ semantic recall) -> fusion, per docs/ARCHITECTURE.md. This is the single
entry point Phase 5's FastAPI endpoint calls.

Usage:
    python -m retrieval.pipeline "what's causing the outage tickets near tower-014?"
"""

import sys

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

    # hybrid — the two recall paths are independent of each other so, in a
    # server context with an async client, they'd run concurrently; here
    # they're sequential since both are simple synchronous calls.
    structural = graph_retrieval.structural_ticket_recall(question, limit=top_k * 2)
    semantic = vector_retrieval.search(question, top_k=top_k * 2)
    fused = fuse(structural["hits"], semantic, top_k=top_k)
    return {"question": question, "mode": mode, "structural": structural, "semantic": semantic, "fused": fused}


def main():
    question = " ".join(sys.argv[1:]) or "What's causing the recent outage tickets?"
    result = retrieve(question)
    import json

    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
