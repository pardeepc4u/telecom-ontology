"""LLM-based query router: classifies an incoming question as structural,
semantic, or hybrid, per docs/ARCHITECTURE.md. Unparseable output falls
back to "hybrid" rather than guessing narrow — running both retrieval
paths and fusing is always a safe superset of either alone.
"""

from .llm_client import chat

LABELS = ("structural", "semantic", "hybrid")

SYSTEM_PROMPT = """You classify questions about a telecom network digital twin \
into exactly one retrieval strategy.

- structural: answerable by graph traversal over network topology or account \
relationships — dependencies, blast radius, who-serves-whom, subscriptions. \
No need to read free-text ticket content.
- semantic: answerable by searching free-text support ticket content for \
similar reported symptoms or complaints. No need for topology traversal.
- hybrid: needs both — e.g. root-cause questions that connect a piece of \
infrastructure to the symptoms customers are reporting about it.

Respond with exactly one word: structural, semantic, or hybrid. No other text."""


def classify(question: str) -> str:
    raw = chat(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
        temperature=0.0,
        max_tokens=5,
    )
    label = raw.strip().lower()
    for candidate in LABELS:
        if candidate in label:
            return candidate
    return "hybrid"
