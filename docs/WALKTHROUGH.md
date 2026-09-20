# Interview Walkthrough

A rehearsal script for demoing this repo — suggested order, what to say at
each step, the exact commands to run live, and the questions most likely
to come up with concise answers. Everything here cross-references the
fuller write-ups in the other docs; this file is the condensed version to
actually talk from.

## 60-second pitch

"I built a small telecom network digital twin — synthetic topology,
customers, and support tickets, modeled against an explicit ontology, in
Neo4j and Qdrant. The interesting part is the retrieval layer: a router
classifies each question as needing graph traversal, vector search, or
both, and for the 'both' case, fuses the two result sets with Reciprocal
Rank Fusion. It's all served through a FastAPI endpoint, and I built a
small evaluation harness that runs a fixed question set against all three
modes and scores them against ground truth — which actually caught a real
bug in my first fusion implementation. Everything's synthetic, self
contained, and on GitHub."

## Suggested walkthrough order (~10-15 min)

1. **[README.md](../README.md)** — repo structure and status. Orients
   where everything lives before diving in.
2. **[ontology/schema.yaml](../ontology/schema.yaml)** — the ontology as a
   real artifact, not implicit in code. Mention the deliberate choice *not*
   to use OWL/RDF/Protégé (see [Decisions to narrate](#decisions-to-narrate) below).
3. **[data/generator/tickets.py](../data/generator/tickets.py)** — show
   the incident-clustering logic. This is what makes the eval meaningful:
   tickets aren't random noise, they're generated with a real (synthetic)
   root cause a retrieval system should be able to trace back to.
4. **[docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md)** diagram — router →
   parallel structural/semantic recall → fusion. Walk through
   `retrieval/graph_retrieval.py`'s `tickets_near` intent and
   `retrieval/fusion.py` specifically — these are the two files worth
   reading closely if asked to go deeper.
5. **Live demo** — run the commands below against the real stack.
6. **[docs/EVALUATION.md](../docs/EVALUATION.md)** — the results table and
   findings. This is the strongest part of the demo: real numbers, an
   honest result (hybrid didn't win everywhere), and a real bug caught and
   fixed by the harness itself.

## Live demo commands

```bash
# Structural: pure graph traversal, no ticket text involved
.venv/bin/python -m retrieval.pipeline "which customers are served by tower-032?"

# Semantic: pure vector search, no location mentioned
.venv/bin/python -m retrieval.pipeline "have customers reported intermittent dropouts during calls?"

# Hybrid: root-cause question, exercises fusion
.venv/bin/python -m retrieval.pipeline "what's likely causing the outage tickets near router-025?"

# Same hybrid question through the actual HTTP API, with synthesized answer
.venv/bin/uvicorn serving.main:app --port 8000 &
curl -s -X POST http://localhost:8000/ask -H "Content-Type: application/json" \
  -d '{"question": "what'"'"'s likely causing the outage tickets near router-025?"}' | python3 -m json.tool

# The evaluation run itself
.venv/bin/python -m eval.run_eval
```

If asked "can I see it live" and the home-lab stack happens to be down,
fall back to `eval/results.json` and `docs/EVALUATION.md` — real output
from a real run, not fabricated for the slide.

## Decisions to narrate

These are the moments in the build where there was a real fork in the
road and a reason for the choice made — the parts worth explaining as
*decisions*, not just describing what the code does.

- **Ontology as hand-written Neo4j schema, not OWL/RDF.** Protégé is
  effectively unmaintained; OWL's reasoner buys real inference but at a
  cost most projects with heavy relationship data don't need. Property
  graphs (Neo4j) let relationships carry properties directly, avoiding
  RDF's reification workaround. Full trade-off in
  [PLAN.md §3](PLAN.md#3-background-rdf-owl-property-graphs-palantir-ontology).
- **Constrained Cypher templates, not open NL-to-Cypher.** The original
  plan said "NL-to-Cypher." Built instead: LLM extracts an entity + one of
  four fixed intents, mapped to hand-written parameterized templates.
  Reason: free-form generated Cypher can be syntactically valid but
  semantically wrong, with no signal anything's off — a real production
  risk. Full reasoning in
  [ARCHITECTURE.md's implementation note](ARCHITECTURE.md#implementation-note-constrained-templates-not-open-nl-to-cypher).
- **Reciprocal Rank Fusion, not raw score summing.** The evaluation
  harness caught this one empirically: structural scores
  (`1/(1+hops)`) and semantic cosine similarity live on different scales,
  so raw summation let weak semantic hits silently outrank strong
  structural ones. RRF fixes it generically by only ever comparing rank
  position. This is the single best "tell me about a bug you caught and
  fixed" story in the repo — see
  [EVALUATION.md's findings](EVALUATION.md#findings).
- **Palantir Ontology vs. OWL/RDF**, if it comes up: Palantir's is
  operational/action-oriented (objects + actions bound to workflows and
  agent execution), not about formal reasoning, and proprietary (no
  OWL/RDF export — real vendor lock-in). This project's ontology is closer
  to the OWL/RDF tradition in spirit (open, portable, reasoned-over by
  explicit code) but implemented pragmatically rather than academically.
  Full comparison in
  [PLAN.md §3](PLAN.md#palantir-ontology-vs-owlrdf).

## Anticipated questions

**"Why doesn't hybrid beat graph-only in your own eval?"**
Don't dodge this — lead with it if it doesn't come up. This synthetic
dataset's `CONCERNS` edges are complete and noise-free by construction
(the generator assigns them deterministically), so graph recall alone
already has near-perfect signal for "is this ticket about this location."
Hybrid's real value shows up when that structural link is missing,
inconsistent, or wrong — which real operational data has and this clean
synthetic dataset doesn't. Flagged as a concrete follow-up: re-run the
same eval after deliberately corrupting some `CONCERNS` edges and check
whether hybrid degrades more gracefully than graph-only. Not run — stated
as the honest next step, not fabricated.

**"Is this what Telecom actually uses?"**
No — explicitly not claiming that. The Google Cloud partnership research
(Spanner Graph, BigQuery Graph, Gemini Enterprise) is public information
used to motivate *why* this shape of system (graph + vector hybrid RAG)
is relevant to a telecom's actual data shape, not a claim about their
internal implementation. Say so plainly if asked — see the caveat in
[PLAN.md §1](PLAN.md#1-research-context--telecoms-ai-stack).

**"How would this scale beyond a home lab?"**
The retrieval layer's clients are all synchronous (`neo4j` driver,
`requests`, `qdrant-client`); hybrid mode already runs structural and
semantic recall concurrently via a thread pool
(`retrieval/pipeline.py`) rather than sequentially. Real scale-up would
mean: async clients instead of a thread pool, connection pooling on the
Neo4j driver (currently opens a fresh driver per call — fine at this
scale, not at production scale), and caching entity resolution instead of
an LLM call per query.

**"What would you do differently with more time?"**
The corrupted-`CONCERNS`-edges follow-up eval above is the strongest
answer — it directly tests hybrid's actual value proposition instead of
this dataset's best case. Also: a ranking-aware eval metric (this one is
set-based precision/recall/F1, not rank-sensitive) and multi-hop dependency
questions beyond the current 1-2 hop templates.

## Known limitations to volunteer, not wait to be asked

- **Answer synthesis isn't perfectly faithful.** Observed: a structural
  question correctly retrieved 7 customers, but the synthesized prose
  claimed "these customers have business accounts" when only 4 of 7 were.
  Retrieval was complete and correct; the LLM's summarization over
  generalized. This is why the API always returns the raw retrieval result
  alongside the prose answer — see
  [ARCHITECTURE.md's Serving section](ARCHITECTURE.md#serving).
- **Small, synthetic, seeded dataset** (32 towers, 28 routers, 180
  customers, 164 tickets). Chosen deliberately for a demoable, fully
  understood ground truth — not represented as production scale.
- **Evaluation is set-based, not rank-aware.** Precision/recall/F1 treat
  the top-k as an unordered set; a ranking metric (NDCG, MRR) would be more
  rigorous but less legible to explain live.
