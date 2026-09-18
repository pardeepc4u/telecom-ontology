"""Loads data/generated/graph.json into Neo4j, driven by
ontology/schema.yaml rather than hardcoded per-type logic — the relationship
loader reads each relationship's declared `from`/`to` types from the schema
to know which labels to MATCH on, including polymorphic targets like
CONCERNS (Ticket -> CellTower | Router).

Idempotent: entities are MERGEd on `id`, relationships are MERGEd between
already-matched endpoints, so re-running against regenerated data updates
in place rather than duplicating nodes/edges.

Usage:
    python -m ingestion.neo4j_loader
"""

import json
from pathlib import Path

from neo4j import GraphDatabase

from data.generator.ontology_check import load_schema
from .config import NEO4J_PASSWORD, NEO4J_URI, NEO4J_USER, require

GRAPH_PATH = Path(__file__).resolve().parents[1] / "data" / "generated" / "graph.json"
CONSTRAINTS_PATH = Path(__file__).resolve().parents[1] / "ontology" / "constraints.cypher"


def load_graph_data():
    if not GRAPH_PATH.exists():
        raise FileNotFoundError(
            f"{GRAPH_PATH} not found — run `python -m data.generator.generate` first (Phase 2)."
        )
    with open(GRAPH_PATH) as f:
        return json.load(f)


def apply_constraints(session):
    statements = [
        s.strip()
        for s in CONSTRAINTS_PATH.read_text().split(";")
        if s.strip() and not s.strip().startswith("//")
    ]
    for statement in statements:
        session.run(statement)


def merge_entities(session, label, records):
    if not records:
        return
    session.run(
        f"UNWIND $records AS r MERGE (n:{label} {{id: r.id}}) SET n += r",
        records=records,
    )


def merge_relationships(session, rel_type, edges, from_label, to_label):
    if not edges:
        return
    session.run(
        f"""
        UNWIND $edges AS e
        MATCH (a:{from_label} {{id: e.from}})
        MATCH (b:{to_label} {{id: e.to}})
        MERGE (a)-[:{rel_type}]->(b)
        """,
        edges=edges,
    )


def target_groups(rel_type, edges, schema):
    """Groups edges by target label. For a polymorphic relationship (schema
    `to` is a list, e.g. CONCERNS), each edge already carries a `to_type`
    field set by the generator; for a single-typed relationship, every edge
    shares the one declared target label."""
    to_spec = schema["relationships"][rel_type]["to"]
    if isinstance(to_spec, list):
        groups = {}
        for edge in edges:
            groups.setdefault(edge["to_type"], []).append(edge)
        return groups
    return {to_spec: edges}


def main():
    require("NEO4J_PASSWORD", NEO4J_PASSWORD)

    schema = load_schema()
    data = load_graph_data()

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        with driver.session() as session:
            apply_constraints(session)

            for label, records in data["entities"].items():
                merge_entities(session, label, records)
                print(f"Merged {len(records)} {label} node(s).")

            for rel_type, edges in data["relationships"].items():
                from_label = schema["relationships"][rel_type]["from"]
                for to_label, group_edges in target_groups(rel_type, edges, schema).items():
                    merge_relationships(session, rel_type, group_edges, from_label, to_label)
                print(f"Merged {len(edges)} {rel_type} relationship(s).")
    finally:
        driver.close()

    print("Neo4j ingestion complete.")


if __name__ == "__main__":
    main()
