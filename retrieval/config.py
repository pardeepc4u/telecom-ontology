"""Retrieval-layer config. Reuses the stack connection settings already
centralized in ingestion/config.py (Neo4j, Qdrant, vLLM base URL) and adds
the one setting Phase 4 introduces: a chat-capable model for the router and
entity/intent extraction, which may be a different model (or endpoint) than
the one serving embeddings.
"""

import os

from dotenv import load_dotenv

from ingestion.config import (  # noqa: F401
    NEO4J_PASSWORD,
    NEO4J_URI,
    NEO4J_USER,
    QDRANT_API_KEY,
    QDRANT_COLLECTION,
    QDRANT_URL,
    VLLM_API_KEY,
    VLLM_BASE_URL,
    require,
)

load_dotenv()

VLLM_CHAT_MODEL = os.environ.get("VLLM_CHAT_MODEL")
