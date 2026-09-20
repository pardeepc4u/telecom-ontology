# Project Plan

Context and phased build plan for the Telecom Network Digital Twin demo,
prepared ahead of a  AI Solutions Architect interview and consultation.

## 1. Research context — Telecom's AI stack

- **Google Cloud partnership (announced Aug 2026):** Telecom consolidated
  legacy data lakes onto Google's **Agentic Data Cloud**, unifying
  structured databases, unstructured documents, and knowledge graphs. Uses
  **Gemini Enterprise** for the contact center (evolved from years of
  Dialogflow CX), agent orchestration, and employee productivity.
- **Likely underlying graph tech:** **Spanner Graph** (operational/real-time)
  and **BigQuery Graph** (analytics) — Google's unified graph offering.
  Spanner Graph is specifically marketed to telecoms for modeling network
  topology as a digital twin (devices, connections, dependencies, service
  configs) for fault detection and root cause analysis.
- **Gemini Enterprise Agent Platform** includes RAG Engine, Vector Search,
  and a graph-based multi-agent orchestration framework (ADK Graph) for
  sub-agent networks.
- **AWS side:** a separate architecture using **Amazon Bedrock Knowledge
  Bases** for RAG, plus 5G edge (AWS Wavelength Zone) for edge-hosted small
  language models.
- **Network/ops AI:** closed-loop automation executed 70M+ autonomous
  network config changes in 2025, using frontier models including
  Anthropic's Claude embedded for traffic management. Agents detect
  anomalies and spin up sub-agents to isolate faulty network domains,
  resolving issues in under 2 minutes. Runs on the on-prem **Telecom Cloud
  Platform** (hosts 5G SA core, vRAN, on-prem GPUs).
- **Caveat:** no public confirmation of the exact graph database vendor
  (e.g. not confirmed as Neo4j specifically) — do not state this as fact in
  the interview.

## 2. Likely interview angles

- **Graph RAG vs. vector RAG trade-offs:** vector RAG is fast, simple, and
  scalable but loses relationships between chunked data; graph RAG preserves
  relationships and is more transparent (traceable subgraphs) — better
  suited to relationship-intensive domains (network topology, customer/
  account relationships), which is exactly Telecom's data shape.
- **Ontology design approach:** modern practice leans on LLMs to infer
  relationships/entities and map them to ontologies dynamically, rather than
  fully hand-building OWL/RDF schemas upfront.
- **Cross-cloud / zero-ETL data unification** (the siloed data problem) —
  relevant since Telecom runs both Google Cloud and AWS AI stacks.

## 3. Background: RDF, OWL, property graphs, Palantir Ontology

Full learning notes, kept for interview prep reference:

### RDF / OWL

- **RDF** (Resource Description Framework): every fact is a
  subject-predicate-object triple (e.g. "router A, connects-to, tower B").
  Millions of triples form a graph — the formal/academic sense of "knowledge
  graph." Query language is **SPARQL** (`SELECT` + `WHERE` with triple
  patterns using variables as wildcards).
- **OWL** (Web Ontology Language): builds on RDF/RDFS to add the actual
  ontology rulebook — classes, object properties (link two entities) vs.
  data properties (link an entity to a literal), and restrictions
  (cardinality, equivalence, disjointness, transitive/symmetric/inverse/
  functional relationships). Workflow: define properties → add restrictions
  → test with a reasoner to catch contradictions/inferences → iterate.
- OWL's key value-add over plain RDF is the **reasoner**: real logical
  inference (e.g. deducing two records refer to the same individual), not
  just fact storage.
- **OWL flavors** trade expressiveness for computability: OWL Lite
  (simplest, restricted), OWL DL (description logic — nearly full
  expressiveness but stays decidable/complete), OWL Full (no restrictions,
  but reasoning can become undecidable). Good interview point:
  expressiveness vs. guaranteed computability.

### RDF vs. property graphs

- RDF triples of the same type between the same two nodes collapse to one
  statement — you can't attach distinct properties (date, source) to
  individual relationship instances without **reification** (creating an
  extra node to represent the relationship itself).
- Property graphs let relationships carry properties directly on the edge —
  simpler and faster to query. This is the concrete technical reason
  enterprises with heavy relationship data (like telecom network topology)
  tend to favor property graphs (Neo4j, Spanner Graph) over pure RDF triple
  stores.

### Tooling decision for this project

Protégé (Stanford, free/open-source OWL editor) is the classic tool, but has
a reputation for being effectively unmaintained/buggy — many practitioners
hand-edit ontologies in plain-text Turtle instead. **For this project,
decided against Protégé/OWL** — the ontology is instead defined as a
hand-written **Neo4j-native schema** (Cypher constraints plus a documented
YAML/JSON file), which is more aligned with modern practice and easier to
demo in a code review. See [ONTOLOGY.md](ONTOLOGY.md).

### Palantir Ontology vs. OWL/RDF

- Palantir's Ontology is not a competitor to OWL/RDF in the academic sense —
  it's a different paradigm. It integrates an enterprise's data, logic,
  actions, and security policies into a representation usable by both
  humans and AI agents: data sources map into **"objects"** (nouns — e.g.
  plants, production lines, customer orders) linked together, paired with
  **"actions"** (verbs — governed operations a user or agent can execute
  against real systems). Often described as functioning like a digital twin
  of the organization.
- **Key differentiator vs. OWL/RDF:** Palantir's ontology is
  operational/action-oriented (bound to workflows, security, and AI agent
  execution), not primarily about formal semantic reasoning.
- **Trade-offs/limitations:** Foundry doesn't perform OWL-style automatic
  logical inference — relationships must be modeled explicitly, no formal
  reasoner. Uses its own proprietary representation, not open standards
  (OWL/RDF/SPARQL) — a Foundry ontology can't be exported as an OWL file for
  another platform to reason over, creating significant vendor lock-in.
  Also depends on forward-deployed engineers embedding with each client to
  manually build/maintain the ontology, rather than a standardized portable
  approach.
- **Framing for interview:** Palantir-style is arguably better for
  operational, action-oriented enterprise use cases (governance, security,
  agent execution matter more than formal inference); OWL/RDF remains
  better where open standards, portability, and genuine automated reasoning
  matter more. Telecom's actual implementation is built on Google's Spanner
  Graph/BigQuery Graph, not Palantir Foundry, but conceptually leans toward
  the operational/action-oriented model in spirit.

## 4. What this repo demonstrates

An end-to-end, clearly staged pipeline:

1. **Data layer** — synthetic data generator producing network topology
   (cell towers, routers, dependencies), customer records, and realistic
   support tickets/outage logs. Fully self-contained, no real Telecom data.
2. **Ontology layer** — explicit ontology definition file checked into the
   repo: entity types (cell tower, router, customer, service plan) and
   relationship types (connects-to, serves, depends-on) as a real design
   artifact, not an implicit schema in code. See [ONTOLOGY.md](ONTOLOGY.md).
3. **Ingestion layer** — scripts to load synthetic data into Neo4j per the
   ontology; a separate pipeline to chunk and embed unstructured tickets
   into a vector store (Chroma or Qdrant).
4. **Retrieval layer** (core module, clean/readable for code review) — see
   [ARCHITECTURE.md](ARCHITECTURE.md) for the router/fusion design.
5. **Serving layer** — a small FastAPI app exposing a single
   question-answering endpoint, so it's live-demoable.
6. **Evaluation layer** — a fixed set of test questions run against
   vector-only, graph-only, and hybrid retrieval, with a results comparison
   table to show measured judgment, not just claims. See
   [EVALUATION.md](EVALUATION.md).

## 5. Phased build plan

- [x] **Phase 1 — Environment.** Stand up Neo4j Community Edition and a
      vector store (Chroma or Qdrant) as Docker containers in the home lab;
      confirm local LLM access via the existing vLLM stack.
- [x] **Phase 2 — Ontology and data.** Write the ontology definition file
      first; build the synthetic data generator (topology, customers,
      tickets) against that ontology.
      See [ONTOLOGY.md](ONTOLOGY.md) and `ontology/schema.yaml` for the
      finalized schema, and `data/generator/` for the generator (run via
      `python -m data.generator.generate --seed 42`, output validated
      against the schema and written to `data/generated/`, which is
      gitignored since it's reproducible from the seed).
- [x] **Phase 3 — Ingestion.** Write and test the Neo4j ingestion script;
      write and test the embedding/ingestion pipeline into the vector
      store.
      See `ingestion/` — `neo4j_loader.py` loads `data/generated/graph.json`
      into Neo4j, driven directly by `ontology/schema.yaml` (including its
      polymorphic `CONCERNS` target); `vector_loader.py` chunks and embeds
      `Ticket` text via a vLLM OpenAI-compatible `/v1/embeddings` endpoint
      and upserts into Qdrant with graph-linking payload metadata
      (`customer_id`, `concerns_id`/`concerns_type`). Both scripts are
      idempotent (MERGE / deterministic point ids). Run both via
      `python -m ingestion.run_ingestion` after copying `.env.example` to
      `.env`. Logic was dry-run tested against real generated data
      (relationship grouping, chunking, payload shape); live DB/Qdrant/vLLM
      connectivity has not yet been exercised end-to-end — see status note
      below.
- [x] **Phase 4 — Retrieval core.** Implement the graph RAG path
      (NL-to-Cypher) alone and test it; implement the vector RAG path alone
      and test it; then build the router and fusion logic to combine them.
      See `retrieval/` and [ARCHITECTURE.md's implementation note](ARCHITECTURE.md#implementation-note-constrained-templates-not-open-nl-to-cypher)
      for why this ended up as LLM-driven entity/intent extraction plus
      fixed Cypher templates rather than free-form NL-to-Cypher generation —
      a deliberate safety/determinism trade-off worth explaining as such,
      not the original literal plan. Router (`router.py`), structural
      recall (`graph_retrieval.py`), semantic recall (`vector_retrieval.py`),
      fusion (`fusion.py`), and the orchestrating `pipeline.py` are all
      written and unit-tested offline (fusion overlap-boost logic, LLM JSON
      output parsing, Cypher template correctness against real generated
      data). Live testing against running Neo4j/Qdrant/vLLM — same caveat as
      Phase 3 — is still pending.
- [ ] **Phase 5 — Serving.** Wrap hybrid retrieval in a FastAPI endpoint for
      live demo.
- [ ] **Phase 6 — Evaluation.** Write the fixed test question set; run all
      three modes (vector-only, graph-only, hybrid); document results in
      [EVALUATION.md](EVALUATION.md) with a comparison table.
- [ ] **Phase 7 — Polish for interview.** Clean README explaining the
      ontology design and fusion logic decisions; push to GitHub; rehearse
      walking through the architecture end to end.
