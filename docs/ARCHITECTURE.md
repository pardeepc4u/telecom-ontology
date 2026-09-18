# Retrieval Architecture

> Status: not yet started (Phase 4). This document describes the target
> design; implementation follows the phased plan in [PLAN.md](PLAN.md).

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

This mirrors the trade-off Verizon's own stack is built around (see
[PLAN.md](PLAN.md#2-likely-interview-angles)): vector RAG is fast and
scalable but loses relationships; graph RAG preserves relationships and is
traceable but doesn't do fuzzy semantic matching. A router + fusion
approach gets both without forcing every query through the slower or less
precise path unnecessarily.
