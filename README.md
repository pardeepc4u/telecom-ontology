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

Phases 1 (environment) and 2 (ontology + synthetic data) are done. See
[docs/PLAN.md](docs/PLAN.md) for phase tracking.

## Getting started (Phase 2 — generate the dataset)

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m data.generator.generate --seed 42
```

Writes `data/generated/graph.json` (all entities + relationships),
`data/generated/tickets.json` (ticket text for Phase 3's vector store
ingestion), and `data/generated/summary.json` (counts + incident clusters).
Output is validated against [`ontology/schema.yaml`](ontology/schema.yaml)
at generation time and is reproducible from the seed, so it isn't committed
(see `.gitignore`).

## Stack

- **Graph store:** Neo4j Community Edition (Docker)
- **Vector store:** Chroma or Qdrant (Docker)
- **LLM access:** local vLLM stack
- **Serving:** FastAPI
- **Data:** fully synthetic — no real Verizon data
