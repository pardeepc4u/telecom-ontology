"""Fusion logic: combines structural and semantic ticket hits, keyed by
ticket_id, per docs/ARCHITECTURE.md.

- A ticket found by both paths is boosted — agreement between graph
  traversal and vector similarity is a stronger relevance signal than
  either alone.
- A ticket found by only one path keeps that path's own score, unboosted.
- The combined set is sorted down to a final top-k.
"""

OVERLAP_BOOST = 0.5


def fuse(structural_hits: list[dict], semantic_hits: list[dict], top_k: int = 10) -> list[dict]:
    combined: dict[str, dict] = {}

    for hit in structural_hits:
        combined[hit["ticket_id"]] = {
            **hit,
            "structural_score": hit["score"],
            "semantic_score": 0.0,
            "sources": {"structural"},
        }

    for hit in semantic_hits:
        ticket_id = hit["ticket_id"]
        if ticket_id in combined:
            combined[ticket_id]["semantic_score"] = hit["score"]
            combined[ticket_id]["sources"].add("semantic")
        else:
            combined[ticket_id] = {
                **hit,
                "structural_score": 0.0,
                "semantic_score": hit["score"],
                "sources": {"semantic"},
            }

    fused = []
    for item in combined.values():
        base_score = item["structural_score"] + item["semantic_score"]
        boost = OVERLAP_BOOST if len(item["sources"]) > 1 else 0.0
        item["fused_score"] = base_score + boost
        item["sources"] = sorted(item["sources"])
        fused.append(item)

    fused.sort(key=lambda item: item["fused_score"], reverse=True)
    return fused[:top_k]
