"""Turns a retrieval result (retrieval/pipeline.py's output) into a
natural-language answer: the generation half of RAG, on top of Phase 4's
retrieval half. The LLM is instructed to answer only from the supplied
evidence and to cite ticket/entity ids, so the answer stays traceable back
to specific graph rows or ticket hits rather than free-floating.
"""

from retrieval.llm_client import chat

SYSTEM_PROMPT = """You are a network operations assistant for a telecom digital twin.
Answer the user's question using ONLY the evidence provided below — do not \
use outside knowledge about real telecom networks. Cite the specific \
ticket id(s) or entity id(s) you relied on. If the evidence doesn't \
support a confident answer, say so plainly rather than guessing. Keep the \
answer to a few sentences."""

MAX_CONTEXT_ITEMS = 12


def _format_structural_rows(structural: dict) -> str:
    entity = structural.get("entity")
    rows = structural.get("rows", [])
    if entity is None:
        return "No matching network entity was found for this question."

    lines = [f"Entity resolved: {entity['name']} ({entity['label']}, id={entity['id']})", "Rows:"]
    for row in rows[:MAX_CONTEXT_ITEMS]:
        lines.append(f"- {row}")
    if not rows:
        lines.append("- (no rows returned)")
    return "\n".join(lines)


def _format_ticket_hits(hits: list[dict], score_key: str = "score") -> str:
    if not hits:
        return "(no ticket hits)"
    lines = []
    for hit in hits[:MAX_CONTEXT_ITEMS]:
        lines.append(
            f"- [{hit['ticket_id']}] (score={hit[score_key]:.3f}, "
            f"category={hit.get('category')}, status={hit.get('status')}): {hit['text']}"
        )
    return "\n".join(lines)


def build_context(result: dict) -> str:
    mode = result["mode"]

    if mode == "structural":
        return _format_structural_rows(result["structural"])

    if mode == "semantic":
        return f"Ticket search results:\n{_format_ticket_hits(result['semantic'])}"

    entity = result["structural"].get("entity")
    entity_line = (
        f"Entity resolved: {entity['name']} ({entity['label']}, id={entity['id']})"
        if entity
        else "No matching network entity was found."
    )
    return (
        f"{entity_line}\n\n"
        f"Fused evidence (tickets found by graph traversal, ticket search, or both, "
        f"ranked by combined relevance):\n{_format_ticket_hits(result['fused'], score_key='fused_score')}"
    )


def synthesize_answer(question: str, result: dict) -> str:
    context = build_context(result)
    return chat(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Question: {question}\n\nEvidence:\n{context}\n\nAnswer:"},
        ],
        temperature=0.1,
        max_tokens=400,
    )
