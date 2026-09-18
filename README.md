# Telecom Network Digital Twin — Hybrid Graph + Vector RAG

A home-lab demo project built to prepare for a Verizon AI Solutions Architect
interview. It implements a small but complete **telecom network digital
twin**: synthetic topology, customer, and ticket data modeled against an
explicit ontology, queryable through a **hybrid retrieval pipeline** that
fuses graph (Neo4j) and vector (Chroma/Qdrant) recall behind a single
FastAPI endpoint.

The goal is not scale — it's a clean, demoable, end-to-end pipeline that
shows deliberate architectural judgment: an explicit ontology, a router that
picks (or blends) retrieval strategies, and a measured comparison of
vector-only vs. graph-only vs. hybrid retrieval.

## Why this exists

Verizon's production AI stack (Google Cloud's Agentic Data Cloud, Spanner
Graph / BigQuery Graph, Gemini Enterprise agent orchestration, plus an AWS
Bedrock RAG stack for other workloads) leans heavily on graph representations
of relationship-dense data — network topology, customer/account structure —
combined with vector retrieval for unstructured ticket/document data. This
repo is a small-scale, self-contained analog of that shape, built to
demonstrate the same design trade-offs rather than to claim knowledge of
Verizon's actual internals.

See [docs/PLAN.md](docs/PLAN.md) for the full research context and interview
framing this project is built around.

## Repo structure

```
telecom-ontology/
├── README.md                # this file
├── docs/
│   ├── PLAN.md               # research context, interview angles, phased build plan
│   ├── ONTOLOGY.md           # entity/relationship ontology definition
│   ├── ARCHITECTURE.md       # retrieval pipeline design (router + fusion)
│   └── EVALUATION.md         # eval methodology and results (filled in during Phase 6)
├── data/                     # synthetic data generator + generated fixtures
├── ingestion/                # Neo4j + vector store loaders
├── retrieval/                # graph RAG, vector RAG, router, fusion logic
├── serving/                  # FastAPI app
└── docker-compose.yml         # Neo4j + vector store local stack
```

Directories above are the target layout from [docs/PLAN.md](docs/PLAN.md);
they are created and filled in phase by phase, not all at once.

## Status

Project scaffolding only — ontology and implementation phases not yet
started. See [docs/PLAN.md](docs/PLAN.md) for phase tracking.

## Stack

- **Graph store:** Neo4j Community Edition (Docker)
- **Vector store:** Chroma or Qdrant (Docker)
- **LLM access:** local vLLM stack
- **Serving:** FastAPI
- **Data:** fully synthetic — no real Verizon data
