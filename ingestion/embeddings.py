"""Thin client for an OpenAI-compatible embeddings endpoint, served by the
home lab's vLLM stack. Uses plain `requests` rather than the `openai` SDK
to keep the dependency footprint small — vLLM's /v1/embeddings response
shape matches OpenAI's.
"""

import requests

from .config import VLLM_API_KEY, VLLM_BASE_URL, VLLM_EMBEDDING_MODEL, require


def embed_texts(texts: list[str], batch_size: int = 32) -> list[list[float]]:
    """Embeds a list of strings, preserving input order. Batches requests
    so a large ticket set doesn't go into a single oversized call."""
    require("VLLM_EMBEDDING_MODEL", VLLM_EMBEDDING_MODEL)

    embeddings: list[list[float]] = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        response = requests.post(
            f"{VLLM_BASE_URL}/embeddings",
            headers={"Authorization": f"Bearer {VLLM_API_KEY}"},
            json={"model": VLLM_EMBEDDING_MODEL, "input": batch},
            timeout=120,
        )
        response.raise_for_status()
        results = sorted(response.json()["data"], key=lambda d: d["index"])
        embeddings.extend(r["embedding"] for r in results)

    return embeddings
