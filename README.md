# Telecom Network Digital Twin — Hybrid Graph + Vector RAG

A home-lab demo project implementing a small but complete **telecom network
digital twin**: synthetic topology, customer, and ticket data modeled
against an explicit ontology, queryable through a **hybrid retrieval
pipeline** that fuses graph (Neo4j) and vector (Qdrant) recall behind a
single FastAPI endpoint.

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
├── README.md                # this file
├── docker-compose.yml       # Neo4j + Qdrant local stack (Phase 1)
├── .env.example             # config template — copy to .env
├── requirements.txt
├── docs/
│   ├── PLAN.md               # research context, interview angles, phased build plan
│   ├── ONTOLOGY.md           # entity/relationship ontology definition
│   ├── ARCHITECTURE.md       # retrieval + serving design (router, fusion, RAG)
│   ├── EVALUATION.md         # eval methodology, results table, findings (Phase 6)
│   └── WALKTHROUGH.md        # interview rehearsal script (Phase 7)
├── ontology/
│   ├── schema.yaml           # source-of-truth entity/relationship schema
│   └── constraints.cypher    # Neo4j uniqueness constraints derived from schema.yaml
├── data/
│   ├── generator/             # synthetic data generator (topology, customers, tickets)
│   └── generated/              # generator output — gitignored, reproducible from --seed
├── ingestion/                # Neo4j + vector store loaders (Phase 3)
├── retrieval/                # graph RAG, vector RAG, router, fusion logic (Phase 4)
├── serving/                  # FastAPI app (Phase 5)
└── eval/                     # fixed question set, ground truth, metrics (Phase 6)
```

## Status

All 7 phases are done (environment, ontology + synthetic data, ingestion,
retrieval core, serving, evaluation, polish). Phases 3–6 have been
confirmed working end-to-end against the live home-lab Neo4j / Qdrant /
vLLM stack (2026-09-20) — real ingestion counts, real query results, real
HTTP requests, and a real scored evaluation run, not just offline unit
tests. **New here? Start with [docs/WALKTHROUGH.md](docs/WALKTHROUGH.md)**
— a condensed demo script with live commands, the design decisions worth
narrating, and answers to the questions most likely to come up.
See [docs/PLAN.md](docs/PLAN.md) for phase tracking,
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the retrieval design
(including a deliberate deviation from the original NL-to-Cypher plan, and
a fusion bug the evaluation caught and fixed), and
[docs/EVALUATION.md](docs/EVALUATION.md) for the results table and an
honest write-up of where hybrid did and didn't beat a single-path mode.

## Getting started

```bash
# Phase 1 — stand up Neo4j + Qdrant locally (skip if you already have a
# stack running elsewhere — just point .env at it instead)
docker compose up -d

python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Phase 2 — generate the synthetic dataset
.venv/bin/python -m data.generator.generate --seed 42

# Phase 3 — ingest into Neo4j + Qdrant
cp .env.example .env   # fill in NEO4J_PASSWORD, VLLM_EMBEDDING_MODEL, VLLM_CHAT_MODEL
.venv/bin/python -m ingestion.run_ingestion

# Phase 4 — query the hybrid retrieval pipeline directly
.venv/bin/python -m retrieval.pipeline "what's causing the outage tickets near tower-014?"

# Phase 5 — serve it over HTTP
.venv/bin/uvicorn serving.main:app --port 8000
curl -s -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "what'"'"'s causing the outage tickets near tower-014?"}'

# Phase 6 — run the fixed evaluation question set
.venv/bin/python -m eval.run_eval
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
hybrid, runs structural (graph neighbor-expansion) and semantic (vector
similarity) recall concurrently and fuses the ticket hits. `router.py`,
`graph_retrieval.py`, `vector_retrieval.py`, and `fusion.py` are each
independently importable and were unit-tested in isolation (fusion
overlap-boost ranking, LLM JSON output parsing, Cypher template shape
against real generated data).

Phase 5's `serving/main.py` wraps `retrieve()` in a single `POST /ask`
endpoint and adds an answer-synthesis step (`serving/generation.py`) that
turns the retrieval result into a cited natural-language answer — the
generation half of RAG. The full retrieval result is always returned
alongside the prose `answer` in the response, since LLM synthesis isn't
always perfectly faithful to the retrieved evidence (see
[docs/PLAN.md's Phase 5 note](docs/PLAN.md)) — the raw rows/hits are the
ground truth to fall back on.

Phase 6's `eval/` runs a fixed 9-question set — three categories, each
designed so a *different* mode should win — against all three retrieval
modes, scored against ground truth computed independently of any
retrieval code. See [docs/EVALUATION.md](docs/EVALUATION.md) for the full
results table and findings, including a real fusion scoring bug the
evaluation caught (structural and semantic scores lived on incomparable
scales) and the fix (switching to Reciprocal Rank Fusion).

## Stack

- **Graph store:** Neo4j Community Edition (Docker — see `docker-compose.yml`)
- **Vector store:** Qdrant (Docker — see `docker-compose.yml`); the
  ingestion/retrieval code has no Qdrant-specific coupling beyond
  `qdrant-client`, so swapping in Chroma would only touch
  `ingestion/vector_loader.py` and `retrieval/vector_retrieval.py`
- **LLM access:** an OpenAI-compatible vLLM/gateway endpoint — one model
  for embeddings (`VLLM_EMBEDDING_MODEL`), one for chat/router/entity
  extraction (`VLLM_CHAT_MODEL`); doesn't have to be the same model or the
  same server for both
- **Serving:** FastAPI
- **Data:** fully synthetic — no real Telecom data
