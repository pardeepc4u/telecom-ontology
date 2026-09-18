# Ontology Definition

The ontology for this project is deliberately **not** OWL/RDF. Per the
tooling decision in [PLAN.md](PLAN.md#tooling-decision-for-this-project),
it's defined as a hand-written, Neo4j-native schema: a documented file
(YAML/JSON, TBD in Phase 2) plus Cypher uniqueness/existence constraints
enforcing it at the database level. This section is the design artifact —
filled in during Phase 2 — describing entity types, relationship types, and
the properties each one carries.

> Status: not yet started (Phase 2). This file will define the schema
> before the synthetic data generator or ingestion scripts are written, so
> that data is generated *against* the ontology rather than the ontology
> being reverse-engineered from the data.

## Design principles

- **Entities as nodes, relationships as typed edges** — property graph
  style, not RDF triples. Relationship instances carry their own properties
  (e.g. `since`, `bandwidth_mbps`) directly on the edge, avoiding
  reification.
- **Explicit over implicit** — every entity type and relationship type used
  by the ingestion or retrieval code must be declared here first.
- **Small and demoable** — enough structure to show real modeling judgment
  (cardinality, directionality, dependency chains) without over-engineering
  a toy dataset.

## Planned entity types (draft — to be finalized in Phase 2)

| Entity | Key properties | Notes |
|---|---|---|
| `CellTower` | id, location, capacity | Root of the physical topology |
| `Router` | id, location, model | Network infrastructure node |
| `Customer` | id, name, account_tier | Linked to service plans |
| `ServicePlan` | id, name, sla_tier | What a customer is served by |
| `Ticket` | id, text, created_at, status | Unstructured — embedded into the vector store, referenced from the graph |

## Planned relationship types (draft — to be finalized in Phase 2)

| Relationship | From → To | Notes |
|---|---|---|
| `CONNECTS_TO` | Router → CellTower / Router → Router | Physical topology, directional or bidirectional TBD |
| `SERVES` | CellTower → Customer | Which tower serves which customer |
| `DEPENDS_ON` | Router → Router | Dependency chain used for root-cause/blast-radius queries |
| `SUBSCRIBES_TO` | Customer → ServicePlan | Account structure |
| `FILED_BY` | Ticket → Customer | Links unstructured tickets back into the graph |
| `CONCERNS` | Ticket → CellTower / Router | Links a ticket to the infrastructure it reports on — the key structural/semantic bridge the hybrid retriever exploits |

## Constraints and cardinality

TBD in Phase 2 — this is where uniqueness constraints, required properties,
and cardinality rules (e.g. a `Customer` subscribes to exactly one active
`ServicePlan`) will be documented alongside the Cypher that enforces them.
