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
      `.env`. Confirmed working live (2026-09-20) against the home-lab
      stack: 32 CellTower, 28 Router, 180 Customer, 5 ServicePlan, and 164
      Ticket nodes plus all six relationship types merged into Neo4j, and
      164 ticket chunk embeddings upserted into Qdrant.
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
      data), and confirmed working live against the running Neo4j/Qdrant/
      vLLM stack (2026-09-20): router correctly classified structural/
      semantic/hybrid questions; entity resolution + both `customers_of_tower`
      and `dependents_of` structural intents returned correct rows; semantic
      search ranked ticket text sensibly; hybrid fusion correctly boosted
      tickets found by both paths above single-path hits.
- [x] **Phase 5 — Serving.** Wrap hybrid retrieval in a FastAPI endpoint for
      live demo.
      See `serving/main.py` — a single `POST /ask` endpoint (plus
      `GET /health`) that calls `retrieval.pipeline.retrieve()` and then
      `serving/generation.py`'s `synthesize_answer()` to turn the retrieval
      result into a cited natural-language answer (the generation half of
      RAG, on top of Phase 4's retrieval half). Run with `uvicorn
      serving.main:app --port 8000`; interactive docs at `/docs`.
      Also: hybrid mode's structural and semantic recall now genuinely run
      concurrently (`retrieval/pipeline.py`, `ThreadPoolExecutor`) rather
      than sequentially, matching the "parallel retrieval" claim in
      [ARCHITECTURE.md](ARCHITECTURE.md).
      Confirmed working live (2026-09-20) against the running stack for all
      three modes via real HTTP requests. One honest caveat: the LLM's
      prose synthesis isn't always perfectly faithful to the retrieved
      evidence — in one structural test it summarized 7 correctly-retrieved
      customers as "these customers have business accounts" when only 4 of
      the 7 were. The retrieval rows themselves were complete and correct;
      the drop happened in prose generation. `retrieval` is always returned
      alongside `answer` in the API response for exactly this reason — the
      demo should show both, not just the prose.
- [x] **Phase 6 — Evaluation.** Write the fixed test question set; run all
      three modes (vector-only, graph-only, hybrid); document results in
      [EVALUATION.md](EVALUATION.md) with a comparison table.
      See `eval/` and [EVALUATION.md](EVALUATION.md) for the full
      methodology, results table, and findings write-up. Headline results:
      each single-path mode wins decisively on the category built for it
      (graph_only: 1.0 F1 on location-only questions; vector_only: clears
      graph_only by a wide margin on symptom-only questions); hybrid did
      **not** beat graph_only on root-cause questions in this run (0.53 vs.
      0.84 mean F1) — explained honestly in EVALUATION.md's Findings
      section rather than glossed over (this synthetic dataset's `CONCERNS`
      edges are complete and noise-free by construction, so there's little
      for a second, noisier signal to add; hybrid's real value likely shows
      up on messier data with missing/wrong structural links, which is
      flagged as a follow-up eval, not run here).
      Evaluation itself caught and fixed a real fusion bug: the first run
      showed `hybrid` producing results *identical* to `vector_only` on
      every root-cause question — traced to `fusion.py` summing raw
      structural (`1/(1+hops)`) and semantic (cosine similarity) scores
      directly, which live on incomparable scales, so weaker semantic hits
      routinely outranked genuinely relevant structural ones. Fixed by
      switching `fusion.py` to Reciprocal Rank Fusion (rank position within
      each list, not raw score) — the standard technique for exactly this
      problem. Confirmed fixed and re-verified against the live stack
      (2026-09-20).
- [x] **Phase 7 — Polish for interview.** Clean README explaining the
      ontology design and fusion logic decisions; push to GitHub; rehearse
      walking through the architecture end to end.
      README rewritten: fixed a leftover grammar break from an earlier
      find-and-replace, corrected the "Chroma or Qdrant" stack description
      to state what's actually configured and tested (Qdrant), and added a
      pointer to the new [WALKTHROUGH.md](WALKTHROUGH.md). Added
      `docker-compose.yml` for Neo4j + Qdrant — previously referenced in
      the repo structure listing but never actually created, since the
      user's own home-lab stack was already running independently; it now
      exists for portability/reproducibility (anyone cloning the repo can
      stand up the same two services locally). Added
      [WALKTHROUGH.md](WALKTHROUGH.md): a condensed interview rehearsal
      script — suggested walkthrough order, live demo commands, the
      specific design decisions worth narrating (ontology-not-OWL,
      constrained-templates-not-open-NL-to-Cypher, RRF fusion fix),
      anticipated questions with concise answers, and limitations to
      volunteer rather than wait to be asked about. All phases (1-7) now
      complete.
