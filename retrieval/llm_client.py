"""Thin client for an OpenAI-compatible chat completions endpoint, served
by the home lab's vLLM stack. Used by both the router (structural/semantic/
hybrid classification) and graph retrieval (entity/intent extraction).
Mirrors ingestion/embeddings.py's approach: plain `requests`, no SDK.
"""

import requests

from .config import VLLM_API_KEY, VLLM_BASE_URL, VLLM_CHAT_MODEL, require


def chat(messages: list[dict], temperature: float = 0.0, max_tokens: int = 300) -> str:
    require("VLLM_CHAT_MODEL", VLLM_CHAT_MODEL)

    response = requests.post(
        f"{VLLM_BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {VLLM_API_KEY}"},
        json={
            "model": VLLM_CHAT_MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]
