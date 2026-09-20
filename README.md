# Telecom Network Digital Twin — Hybrid Graph + Vector RAG

A home-lab demo project built to implements a small but complete **telecom network digital
twin**: synthetic topology, customer, and ticket data modeled against an
explicit ontology, queryable through a **hybrid retrieval pipeline** that
fuses graph (Neo4j) and vector (Chroma/Qdrant) recall behind a single
FastAPI endpoint.

The goal is not scale — it's a clean, demoable, end-to-end pipeline that
shows deliberate architectural judgment: an explicit ontology, a router that
picks (or blends) retrieval strategies, and a measured comparison of
vector-only vs. graph-only vs. hybrid retrieval.

## Why this exists

Telecom's production AI stack (Google Cloud's Agentic Data Cloud, Spanner
Graph / BigQuery Graph, Gemini Enterprise agent orchestration, plus an AWS
Bedrock RAG stack for other workloads) leans heavily on graph representations
of relationship-dense data — network topology, customer/account structure —
combined with vector retrieval for unstructured ticket/document data. This
repo is a small-scale, self-contained analog of that shape, built to
demonstrate the same design trade-offs rather than to claim knowledge of
Telecom's actual internals.

See [docs/PLAN.md](docs/PLAN.md) for the full research context and interview
framing this project is built around.

## Repo structure

```
telecom-ontology/
├── README.md                 # this file
├── requirements.txt
├── docs/
│   ├── PLAN.md                # research context, interview angles, phased build plan
│   ├── ONTOLOGY.md            # entity/relationship ontology definition
│   ├── ARCHITECTURE.md        # retrieval pipeline design (router + fusion)
│   └── EVALUATION.md          # eval methodology and results (filled in during Phase 6)
├── ontology/
│   ├── schema.yaml             # source-of-truth entity/relationship schema
│   └── constraints.cypher      # Neo4j uniqueness constraints derived from schema.yaml
├── data/
│   ├── generator/               # synthetic data generator (topology, customers, tickets)
│   └── generated/                # generator output — gitignored, reproducible from --seed
├── ingestion/                  # Neo4j + vector store loaders (Phase 3)
├── retrieval/                  # graph RAG, vector RAG, router, fusion logic (Phase 4)
├── serving/                    # FastAPI app (Phase 5)
└── docker-compose.yml           # Neo4j + vector store local stack (Phase 1)
```

## Status

Phases 1 (environment), 2 (ontology + synthetic data), 3 (ingestion), and 4
(retrieval core) are done, and Phases 3–4 have been confirmed working
end-to-end against the live home-lab Neo4j / Qdrant / vLLM stack
(2026-09-20) — real ingestion counts and real structural/semantic/hybrid
query results, not just offline unit tests. See [docs/PLAN.md](docs/PLAN.md)
for phase tracking and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the
retrieval design, including a deliberate deviation from the original
NL-to-Cypher plan.

## Getting started

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Phase 2 — generate the synthetic dataset
.venv/bin/python -m data.generator.generate --seed 42

# Phase 3 — ingest into Neo4j + Qdrant (requires Phase 1's stack running)
cp .env.example .env   # fill in NEO4J_PASSWORD, VLLM_EMBEDDING_MODEL, VLLM_CHAT_MODEL
.venv/bin/python -m ingestion.run_ingestion

# Phase 4 — query the hybrid retrieval pipeline
.venv/bin/python -m retrieval.pipeline "what's causing the outage tickets near tower-014?"
```

Phase 2 writes `data/generated/graph.json` (all entities + relationships),
`data/generated/tickets.json` (ticket text), and `data/generated/summary.json`
(counts + incident clusters). Output is validated against
[`ontology/schema.yaml`](ontology/schema.yaml) at generation time and is
reproducible from the seed, so it isn't committed (see `.gitignore`).

Phase 3's `ingestion/neo4j_loader.py` and `ingestion/vector_loader.py` are
each independently runnable too (`python -m ingestion.neo4j_loader`, `python
-m ingestion.vector_loader`) and idempotent, so re-running after
regenerating data is safe.

Phase 4's `retrieval/` package is driven by `retrieval.pipeline.retrieve()`:
routes a question to structural, semantic, or hybrid handling, and for
hybrid, fuses structural (graph neighbor-expansion) and semantic (vector
similarity) ticket hits. `router.py`, `graph_retrieval.py`,
`vector_retrieval.py`, and `fusion.py` are each independently importable
and were unit-tested in isolation (fusion overlap-boost ranking, LLM JSON
output parsing, Cypher template shape against real generated data).

## Stack

- **Graph store:** Neo4j Community Edition (Docker)
- **Vector store:** Chroma or Qdrant (Docker)
- **LLM access:** local vLLM stack
- **Serving:** FastAPI
- **Data:** fully synthetic — no real Telecom data
