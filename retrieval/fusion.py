"""Fusion logic: combines structural and semantic ticket hits, keyed by
ticket_id, per docs/ARCHITECTURE.md.

Uses Reciprocal Rank Fusion (RRF): each hit's contribution is 1/(k + rank)
within its own source list, not its raw score. This is deliberate, not
incidental — an earlier version summed raw scores directly (structural's
1/(1+hops) vs. semantic's cosine similarity) and Phase 6's evaluation
caught a real bug from it: structural hits found via a 1-hop router->tower
traversal scored 0.5, below typical semantic cosine scores (0.55-0.9), so
genuinely relevant structural evidence was silently outranked by weaker
semantic matches purely because the two paths' scores live on different,
incomparable scales. RRF sidesteps that entirely by only ever comparing
rank positions, which are always on the same 1..N scale regardless of
source. It's the standard technique for exactly this problem in hybrid
search (see e.g. Qdrant's and Elasticsearch's hybrid search fusion).

- A ticket found by both paths is boosted — its RRF contributions from
  both lists sum together, so agreement is still a stronger signal than
  either alone.
- A ticket found by only one path keeps that path's single RRF
  contribution.
- The combined set is sorted down to a final top-k.
"""

RRF_K = 60  # standard default; dampens the influence of very top ranks


def fuse(structural_hits: list[dict], semantic_hits: list[dict], top_k: int = 10) -> list[dict]:
    combined: dict[str, dict] = {}

    def register(hits: list[dict], source: str):
        for rank, hit in enumerate(hits, start=1):
            ticket_id = hit["ticket_id"]
            entry = combined.setdefault(ticket_id, {
                **hit,
                "structural_score": 0.0,
                "semantic_score": 0.0,
                "fused_score": 0.0,
                "sources": set(),
            })
            entry[f"{source}_score"] = hit["score"]
            entry["fused_score"] += 1.0 / (RRF_K + rank)
            entry["sources"].add(source)
            entry["text"] = hit["text"]  # keep in case only one side had it

    register(structural_hits, "structural")
    register(semantic_hits, "semantic")

    fused = list(combined.values())
    for item in fused:
        item["sources"] = sorted(item["sources"])
    fused.sort(key=lambda item: item["fused_score"], reverse=True)
    return fused[:top_k]
