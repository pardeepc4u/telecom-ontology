"""Main entry point for Phase 2: generates the full synthetic dataset
(topology, customers, tickets), validates it against ontology/schema.yaml,
and writes it to data/generated/.

Usage:
    python -m data.generator.generate [--seed 42]
"""

import argparse
import json
import random
from pathlib import Path

from . import ontology_check
from .customers import generate_customers
from .names import CITIES, ROUTER_MODELS
from .tickets import generate_tickets
from .topology import generate_topology

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "generated"


def build_dataset(seed: int):
    rng = random.Random(seed)

    routers, towers, depends_on, connects_to = generate_topology(rng, CITIES, ROUTER_MODELS)
    service_plans, customers, serves, subscribes_to = generate_customers(rng, towers)
    tickets, filed_by, concerns, incidents_summary = generate_tickets(
        rng, routers, towers, connects_to, depends_on, serves
    )

    entities = {
        "CellTower": towers,
        "Router": routers,
        "Customer": customers,
        "ServicePlan": service_plans,
        "Ticket": tickets,
    }
    relationships = {
        "DEPENDS_ON": depends_on,
        "CONNECTS_TO": connects_to,
        "SERVES": serves,
        "SUBSCRIBES_TO": subscribes_to,
        "FILED_BY": filed_by,
        "CONCERNS": concerns,
    }
    return entities, relationships, incidents_summary


def validate(entities, relationships):
    schema = ontology_check.load_schema()

    for entity_type, records in entities.items():
        ontology_check.validate_entities(schema, entity_type, records)

    entity_ids_by_type = {
        entity_type: {record["id"] for record in records}
        for entity_type, records in entities.items()
    }
    for rel_type, edges in relationships.items():
        ontology_check.validate_relationship_targets(schema, rel_type, edges, entity_ids_by_type)


def write_output(entities, relationships, incidents_summary):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    graph = {"entities": entities, "relationships": relationships}
    with open(OUTPUT_DIR / "graph.json", "w") as f:
        json.dump(graph, f, indent=2)

    # Tickets get their own file too since Phase 3's vector-store ingestion
    # pipeline consumes ticket text independently of the graph loader.
    with open(OUTPUT_DIR / "tickets.json", "w") as f:
        json.dump(entities["Ticket"], f, indent=2)

    summary = {
        "counts": {entity_type: len(records) for entity_type, records in entities.items()},
        "relationship_counts": {rel_type: len(edges) for rel_type, edges in relationships.items()},
        "incidents": incidents_summary,
    }
    with open(OUTPUT_DIR / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    return summary


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic telecom digital twin data.")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    entities, relationships, incidents_summary = build_dataset(args.seed)
    validate(entities, relationships)
    summary = write_output(entities, relationships, incidents_summary)

    print(f"Wrote dataset to {OUTPUT_DIR} (seed={args.seed})")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
