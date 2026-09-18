"""Runs both ingestion pipelines in order: Neo4j graph load, then Qdrant
vector load. Each is also independently runnable (`python -m
ingestion.neo4j_loader` / `python -m ingestion.vector_loader`) since they
don't depend on each other.

Usage:
    python -m ingestion.run_ingestion
"""

from . import neo4j_loader, vector_loader


def main():
    print("== Neo4j graph ingestion ==")
    neo4j_loader.main()

    print("\n== Qdrant vector ingestion ==")
    vector_loader.main()


if __name__ == "__main__":
    main()
