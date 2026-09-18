"""Centralized environment configuration for the ingestion layer.

Copy .env.example to .env and fill in values that match your local Phase 1
stack. Values with a sensible default (ports, hosts) fall back to it;
values with no safe default (passwords, model names) come back as None and
each script that actually needs one checks it explicitly via `require()`,
so e.g. running the Neo4j loader alone doesn't force you to also configure
the embedding model.
"""

import os

from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD")

QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY") or None
QDRANT_COLLECTION = os.environ.get("QDRANT_COLLECTION", "tickets")

VLLM_BASE_URL = os.environ.get("VLLM_BASE_URL", "http://localhost:8000/v1")
VLLM_EMBEDDING_MODEL = os.environ.get("VLLM_EMBEDDING_MODEL")
VLLM_API_KEY = os.environ.get("VLLM_API_KEY", "EMPTY")


def require(name: str, value):
    if not value:
        raise RuntimeError(
            f"Missing required environment variable {name}. "
            f"Copy .env.example to .env and set it."
        )
    return value
