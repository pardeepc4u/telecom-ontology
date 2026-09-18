"""Chunks and embeds ticket text into Qdrant.

Synthetic tickets in this project are short (a sentence or two), so
chunking is a no-op in practice — but the chunker is real, not stubbed, so
this pipeline still works if pointed at longer ticket/transcript text later.

Each point's payload carries the graph-side context (customer, concerned
CellTower/Router) pulled from data/generated/graph.json's FILED_BY and
CONCERNS relationships, so the retrieval layer's structural-recall path
(Phase 4) can bridge from a vector hit back into the graph, and vice versa.

Usage:
    python -m ingestion.vector_loader
"""

import json
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

from .config import QDRANT_API_KEY, QDRANT_COLLECTION, QDRANT_URL
from .embeddings import embed_texts

GRAPH_PATH = Path(__file__).resolve().parents[1] / "data" / "generated" / "graph.json"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    if len(text) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start : start + chunk_size])
        start += chunk_size - overlap
    return chunks


def load_ticket_context():
    if not GRAPH_PATH.exists():
        raise FileNotFoundError(
            f"{GRAPH_PATH} not found — run `python -m data.generator.generate` first (Phase 2)."
        )
    with open(GRAPH_PATH) as f:
        data = json.load(f)

    tickets = data["entities"]["Ticket"]
    filed_by = {e["from"]: e["to"] for e in data["relationships"]["FILED_BY"]}
    concerns = {e["from"]: (e["to"], e["to_type"]) for e in data["relationships"]["CONCERNS"]}
    return tickets, filed_by, concerns


def ensure_collection(client: QdrantClient, vector_size: int):
    if client.collection_exists(QDRANT_COLLECTION):
        return
    client.create_collection(
        collection_name=QDRANT_COLLECTION,
        vectors_config=qm.VectorParams(size=vector_size, distance=qm.Distance.COSINE),
    )


def build_points(tickets, filed_by, concerns):
    chunk_texts = []
    chunk_payloads = []

    for ticket in tickets:
        concerns_id, concerns_type = concerns.get(ticket["id"], (None, None))
        for chunk_index, chunk in enumerate(chunk_text(ticket["text"])):
            chunk_texts.append(chunk)
            chunk_payloads.append({
                "ticket_id": ticket["id"],
                "chunk_index": chunk_index,
                "text": chunk,
                "category": ticket["category"],
                "status": ticket["status"],
                "created_at": ticket["created_at"],
                "customer_id": filed_by.get(ticket["id"]),
                "concerns_id": concerns_id,
                "concerns_type": concerns_type,
            })

    return chunk_texts, chunk_payloads


def main(batch_size: int = 32):
    tickets, filed_by, concerns = load_ticket_context()
    chunk_texts, chunk_payloads = build_points(tickets, filed_by, concerns)

    if not chunk_texts:
        print("No tickets to embed.")
        return

    embeddings = embed_texts(chunk_texts, batch_size=batch_size)

    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    ensure_collection(client, vector_size=len(embeddings[0]))

    points = [
        qm.PointStruct(id=idx, vector=vector, payload=payload)
        for idx, (vector, payload) in enumerate(zip(embeddings, chunk_payloads))
    ]
    client.upsert(collection_name=QDRANT_COLLECTION, points=points)

    print(
        f"Upserted {len(points)} ticket chunk embedding(s) from {len(tickets)} ticket(s) "
        f"into Qdrant collection '{QDRANT_COLLECTION}'."
    )


if __name__ == "__main__":
    main()
