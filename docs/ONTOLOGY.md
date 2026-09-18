# Ontology Definition

The ontology is deliberately **not** OWL/RDF. Per the tooling decision in
[PLAN.md](PLAN.md#tooling-decision-for-this-project), it's a hand-written,
Neo4j-native schema: [`ontology/schema.yaml`](../ontology/schema.yaml) is
the source of truth, and [`ontology/constraints.cypher`](../ontology/constraints.cypher)
enforces uniqueness at the database level (Phase 3 ingestion runs it once
against a fresh Neo4j instance).

The synthetic data generator (`data/generator/`) validates its output
against `schema.yaml` at generation time — required fields and enum values
are checked in code (`data/generator/ontology_check.py`), not just asserted
in this document. If the generator's output ever drifted from the schema,
generation would fail loudly rather than silently producing bad data.

## Design principles

- **Entities as nodes, relationships as typed edges** — property graph
  style, not RDF triples. Relationship instances carry their own properties
  directly on the edge, avoiding reification.
- **Explicit over implicit** — every entity type and relationship type used
  by the generator, ingestion, or retrieval code is declared in
  `schema.yaml` first.
- **Small and demoable** — enough structure (a 3-tier router hierarchy,
  deliberate incident clusters in the ticket data) to show real modeling
  and root-cause reasoning, without over-engineering a toy dataset.

## Entity types

| Entity | Key properties | Notes |
|---|---|---|
| `CellTower` | id, name, location, capacity | Leaf of the physical topology |
| `Router` | id, name, tier (core/regional/access), location, model | Tiered infrastructure — tier drives blast-radius traversal |
| `Customer` | id, name, account_tier | Linked to a service plan and a serving tower |
| `ServicePlan` | id, name, sla_tier | Small fixed catalog (5 plans) |
| `Ticket` | id, text, category, created_at, status | Unstructured — embedded into the vector store in Phase 3, also linked into the graph |

## Relationship types

| Relationship | From → To | Cardinality | Notes |
|---|---|---|---|
| `DEPENDS_ON` | Router → Router | many-to-one | access → regional → core; the blast-radius/root-cause chain |
| `CONNECTS_TO` | CellTower → Router | many-to-one | Which access router a tower's traffic routes through |
| `SERVES` | CellTower → Customer | one-to-many | Which tower serves a given customer |
| `SUBSCRIBES_TO` | Customer → ServicePlan | many-to-one | A customer subscribes to exactly one active plan |
| `FILED_BY` | Ticket → Customer | many-to-one | Who filed the ticket |
| `CONCERNS` | Ticket → CellTower \| Router | many-to-one | The structural/semantic bridge the hybrid retriever exploits — see below |

## Why `CONCERNS` targets two types

Most tickets `CONCERNS` the `CellTower` serving the customer who filed them
— realistic, since customers know their local area, not internal router
topology. A minority of tickets generated during a **regional-tier**
incident instead `CONCERNS` the `Router` directly, modeling a support agent
who has already escalated and diagnosed the issue as area-wide. This is
also what exercises both branches of the schema's `to: [CellTower, Router]`
declaration in real generated data, rather than leaving one branch untested.

## Incident clustering (why the ticket data isn't just noise)

The generator (`data/generator/tickets.py`) doesn't scatter tickets
uniformly at random. It:

1. Picks a handful of "faulty" routers (access or regional tier).
2. Traverses `DEPENDS_ON`/`CONNECTS_TO` to find every customer actually
   downstream of each one.
3. Generates a cluster of incident-flavored tickets (outage/degraded
   service language) filed only by those downstream customers.
4. Separately scatters unrelated "routine" tickets (billing, minor
   complaints) across random customers as background noise.

This matters for [EVALUATION.md](EVALUATION.md): a hybrid query like "what's
likely causing the outage tickets near Tower Y?" is only a meaningful test
of graph+vector fusion if the tickets are actually structurally traceable
to a common cause — not coincidental text similarity.

## Constraints

Uniqueness only — Neo4j Community Edition doesn't support property
existence constraints (Enterprise-only), so required-field enforcement
lives in the ontology-check validator in the generator instead. See
[`ontology/constraints.cypher`](../ontology/constraints.cypher).
