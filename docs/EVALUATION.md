# Evaluation

> Status: not yet started (Phase 6). This document will hold the fixed test
> question set, the methodology, and the results comparison table once
> Phases 1–5 are complete.

## Methodology (planned)

1. Define a fixed set of test questions spanning three categories:
   - **Structural** questions (best answered by graph traversal alone)
   - **Semantic** questions (best answered by vector search alone)
   - **Hybrid** questions (need both — e.g. root-cause questions that
     combine topology with reported symptoms)
2. Run every question against three retrieval modes:
   - Vector-only
   - Graph-only
   - Hybrid (router + fusion, as described in
     [ARCHITECTURE.md](ARCHITECTURE.md))
3. Score each mode's results per question (relevance / correctness,
   judged manually against the synthetic ground truth since the dataset is
   fully controlled).
4. Publish a results comparison table here, showing where hybrid wins,
   where it doesn't beat a single-path approach, and why — the point is
   demonstrating measured judgment, not proving hybrid always wins.

## Results

_Not yet available — populated in Phase 6._
