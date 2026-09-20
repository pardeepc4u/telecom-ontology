# Retrieval Architecture

> Status: implemented and live-tested (Phase 4, confirmed 2026-09-20). See
> `retrieval/` — `router.py`, `graph_retrieval.py`, `vector_retrieval.py`,
> `fusion.py`, and the orchestrating `pipeline.py`. See the implementation
> note below for one deliberate deviation from the original plan.

## Overview

The retrieval layer is the core module of this project — the part meant to
read cleanly in a code review and to demonstrate the graph-RAG-vs-vector-RAG
trade-off directly rather than just asserting it.

```
                     ┌─────────────┐
   query ──────────▶ │   Router    │
                     │ (LLM class-  │
                     │  ifier)      │
                     └──────┬──────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
        structural      hybrid        semantic
              │             │             │
              ▼             ▼             ▼
      ┌───────────────┐           ┌───────────────┐
      │ Graph recall   │           │ Vector recall  │
      │ (Neo4j: entity │  ◀─run───▶│ (cosine sim.   │
      │ match + n-hop  │  concurr. │  over ticket   │
      │ neighbor exp.) │           │  embeddings)   │
      └───────┬────────┘           └───────┬────────┘
              │                             │
              └─────────────┬───────────────┘
                             ▼
                    ┌─────────────────┐
                    │  Fusion logic    │
                    │  (boost overlap, │
                    │  keep single-    │
                    │  path scores,    │
                    │  sort → top-k)   │
                    └────────┬────────┘
                             ▼
                         top-k results
```

## Components

### 1. Router

An LLM-based classifier that decides, per incoming query, whether it's:

- **structural** — best answered by graph traversal (e.g. "what depends on
  Router X?", "which customers are served by Tower Y?")
- **semantic** — best answered by similarity search over ticket text (e.g.
  "have customers reported anything like intermittent dropouts?")
- **hybrid** — needs both (e.g. "what's likely causing the outage tickets
  near Tower Y?")

### 2. Parallel retrieval

- **Structural recall:** entity matching against the ontology's entity
  types, followed by neighbor expansion (n-hop traversal) in Neo4j.
- **Vector recall:** cosine similarity search over ticket embeddings in the
  vector store.

These two paths run concurrently rather than sequentially, since they're
independent until fusion.

### 3. Fusion logic

Scoring that:

- **Boosts** results found by both retrieval paths (structural + semantic
  agreement is a strong relevance signal),
- **Keeps** single-path scores for results found by only one path,
- **Sorts** the combined, scored set down to a final top-k.

This is the piece most worth walking through in an interview: it's a
concrete, inspectable answer to "how do you combine graph and vector
retrieval" rather than a hand-wave.

## Why this shape

This mirrors the trade-off Telecom's own stack is built around (see
[PLAN.md](PLAN.md#2-likely-interview-angles)): vector RAG is fast and
scalable but loses relationships; graph RAG preserves relationships and is
traceable but doesn't do fuzzy semantic matching. A router + fusion
approach gets both without forcing every query through the slower or less
precise path unnecessarily.

## Implementation note: constrained templates, not open NL-to-Cypher

The original plan (see [PLAN.md](PLAN.md)) described the graph RAG path as
"NL-to-Cypher." The actual implementation (`graph_retrieval.py`) does
something narrower and, on reflection, better: the LLM's job is limited to
extracting (a) which entity a question is about and (b) which of four fixed
intents it maps to (`dependents_of`, `towers_under_router`,
`customers_of_tower`, `tickets_near`) — not writing arbitrary Cypher.

Each intent maps to one hand-written, parameterized Cypher template. This
still delivers "ask a question in English, get a graph traversal back," but
avoids the real failure mode of free-form LLM-generated Cypher in
production: a syntactically valid but semantically wrong query that returns
confident, plausible-looking, incorrect results with no signal that
anything went wrong. Constrained templates are also what make the entity
resolution, intent mapping, and Cypher correctness testable offline against
real generated data (`data/generated/graph.json`) without a live LLM call —
which is exactly how this module was verified before a live stack was
available.

`tickets_near` is the intent hybrid mode actually uses: it walks
`CONCERNS`/`CONNECTS_TO`/`DEPENDS_ON` out from the resolved entity to
related `Ticket` nodes, returning ticket-shaped hits (`ticket_id`, `text`,
`score`) directly comparable to vector search hits — the mechanism that
makes fusion's overlap-boost possible at all.
