"""Semantic retrieval: embeds the question with the same vLLM embeddings
endpoint used at ingestion time (ingestion/embeddings.py) and runs cosine
similarity search against the Qdrant ticket collection populated in
Phase 3.
"""

from qdrant_client import QdrantClient

from ingestion.embeddings import embed_texts
from .config import QDRANT_API_KEY, QDRANT_COLLECTION, QDRANT_URL


def search(question: str, top_k: int = 10) -> list[dict]:
    [query_vector] = embed_texts([question])

    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    response = client.query_points(
        collection_name=QDRANT_COLLECTION,
        query=query_vector,
        limit=top_k,
        with_payload=True,
    )

    return [
        {
            "ticket_id": point.payload["ticket_id"],
            "text": point.payload["text"],
            "category": point.payload.get("category"),
            "status": point.payload.get("status"),
            "score": point.score,
            "source": "semantic",
        }
        for point in response.points
    ]
