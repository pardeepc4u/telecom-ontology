"""Structural retrieval: entity matching + n-hop neighbor expansion in
Neo4j, per docs/ARCHITECTURE.md.

Design note: this is deliberately *not* open-ended NL-to-Cypher generation.
The LLM's job is narrow — extract which entity the question is about and
which of a small fixed set of intents it maps to — and each intent maps to
one hand-written, parameterized Cypher template. Free-form LLM-generated
Cypher is a real injection/hallucination risk in production (a plausible-
looking but wrong query fails silently); constrained template selection
gets the same "natural language in, graph traversal out" experience while
staying safe and deterministic enough to unit test. Worth raising in an
interview as a deliberate trade-off, not an oversight.

`tickets_near` is the intent that matters most: it's the one that produces
ticket-shaped hits (ticket_id, text, score) directly comparable to vector
search results, which is what makes hybrid fusion (fusion.py) possible.
"""

import json
from pathlib import Path

from neo4j import GraphDatabase

from data.generator.ontology_check import load_schema
from .config import NEO4J_PASSWORD, NEO4J_URI, NEO4J_USER, require
from .llm_client import chat

INTENTS = ("dependents_of", "towers_under_router", "customers_of_tower", "tickets_near")

ENTITY_INTENT_SYSTEM_PROMPT = """Given a question about a telecom network, extract:
1. "entity": the specific router, cell tower, or customer name/id mentioned, exactly as written.
2. "intent": exactly one of:
   - dependents_of: what depends on / is downstream of a given router (blast radius)
   - towers_under_router: which cell towers sit under a given router
   - customers_of_tower: which customers are served by a given cell tower
   - tickets_near: what support tickets are near/about a given router or tower

Respond with strict JSON only, no markdown fences, no explanation:
{"entity": "<name as mentioned>", "intent": "<one of the four intents>"}"""

# Single-target templates for pure "structural" questions. Each requires
# the resolved entity to be the given label — see run_structural_query.
TEMPLATES = {
    "dependents_of": {
        "required_label": "Router",
        "cypher": """
            MATCH (dep:Router)-[:DEPENDS_ON*1..3]->(target:Router {id: $id})
            RETURN dep.id AS id, dep.name AS name, dep.tier AS tier
            LIMIT $limit
        """,
    },
    "towers_under_router": {
        "required_label": "Router",
        "cypher": """
            MATCH (t:CellTower)-[:CONNECTS_TO]->(:Router)-[:DEPENDS_ON*0..2]->(target:Router {id: $id})
            RETURN DISTINCT t.id AS id, t.name AS name, t.capacity AS capacity
            LIMIT $limit
        """,
    },
    "customers_of_tower": {
        "required_label": "CellTower",
        "cypher": """
            MATCH (target:CellTower {id: $id})-[:SERVES]->(c:Customer)
            RETURN c.id AS id, c.name AS name, c.account_tier AS account_tier
            LIMIT $limit
        """,
    },
}

# tickets_near needs two variants since CONCERNS' target is polymorphic
# (CellTower directly, or Router — see ontology/schema.yaml) and a Router's
# related tickets require walking down through any dependent access routers.
TICKETS_NEAR_CYPHER = {
    "CellTower": """
        MATCH (tk:Ticket)-[:CONCERNS]->(target:CellTower {id: $id})
        RETURN tk.id AS ticket_id, tk.text AS text, tk.category AS category,
               tk.status AS status, 0 AS hops
        LIMIT $limit
    """,
    "Router": """
        MATCH (tk:Ticket)-[:CONCERNS]->(x) WHERE x.id = $id
        RETURN tk.id AS ticket_id, tk.text AS text, tk.category AS category,
               tk.status AS status, 0 AS hops
        UNION
        MATCH (tk:Ticket)-[:CONCERNS]->(t:CellTower)
              -[:CONNECTS_TO]->(:Router)-[:DEPENDS_ON*0..2]->(target:Router {id: $id})
        RETURN tk.id AS ticket_id, tk.text AS text, tk.category AS category,
               tk.status AS status, 1 AS hops
        LIMIT $limit
    """,
}

ENTITY_RESOLUTION_CYPHER = """
    MATCH (n)
    WHERE n.id = $q OR toLower(n.name) CONTAINS toLower($q) OR toLower(n.id) CONTAINS toLower($q)
    RETURN labels(n)[0] AS label, n.id AS id, n.name AS name
    LIMIT 1
"""


def get_driver():
    require("NEO4J_PASSWORD", NEO4J_PASSWORD)
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def run_cypher(cypher: str, params: dict) -> list[dict]:
    driver = get_driver()
    try:
        with driver.session() as session:
            return [dict(record) for record in session.run(cypher, **params)]
    finally:
        driver.close()


def _parse_json_object(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON object found in LLM output: {raw!r}")
    return json.loads(text[start : end + 1])


def extract_entity_intent(question: str) -> dict:
    raw = chat(
        [
            {"role": "system", "content": ENTITY_INTENT_SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
        temperature=0.0,
        max_tokens=100,
    )
    data = _parse_json_object(raw)
    return {
        "entity": data.get("entity", question),
        "intent": data.get("intent") if data.get("intent") in INTENTS else None,
    }


def resolve_entity(name_or_id: str) -> dict | None:
    rows = run_cypher(ENTITY_RESOLUTION_CYPHER, {"q": name_or_id, "limit": 1})
    return rows[0] if rows else None


def _tickets_near_entity(entity: dict, limit: int) -> list[dict]:
    cypher = TICKETS_NEAR_CYPHER.get(entity["label"])
    if cypher is None:
        return []
    rows = run_cypher(cypher, {"id": entity["id"], "limit": limit})
    return [
        {
            "ticket_id": row["ticket_id"],
            "text": row["text"],
            "category": row["category"],
            "status": row["status"],
            "score": 1.0 / (1 + row["hops"]),
            "source": "structural",
        }
        for row in rows
    ]


def structural_ticket_recall(question: str, limit: int = 15) -> dict:
    """The mechanism hybrid mode uses: resolves the entity in the question,
    then neighbor-expands out to related Ticket nodes. Returns ticket-shaped
    hits so fusion.py can compare them directly against vector search hits."""
    extraction = extract_entity_intent(question)
    entity = resolve_entity(extraction["entity"])
    if entity is None:
        return {"entity": None, "extraction": extraction, "hits": []}
    return {"entity": entity, "extraction": extraction, "hits": _tickets_near_entity(entity, limit)}


def run_structural_query(question: str, limit: int = 25) -> dict:
    """Pure structural mode: resolves the entity, picks the matching
    template for the extracted intent, and returns raw rows. Falls back to
    tickets_near if the intent is missing/ambiguous or doesn't match the
    resolved entity's type, rather than erroring out."""
    extraction = extract_entity_intent(question)
    entity = resolve_entity(extraction["entity"])
    if entity is None:
        return {"entity": None, "extraction": extraction, "rows": []}

    intent = extraction["intent"]
    if intent == "tickets_near":
        recall = structural_ticket_recall(question, limit)
        return {"entity": entity, "extraction": extraction, "rows": recall["hits"]}

    template = TEMPLATES.get(intent)
    if template is None or template["required_label"] != entity["label"]:
        recall = structural_ticket_recall(question, limit)
        return {"entity": entity, "extraction": extraction, "rows": recall["hits"], "fallback": "tickets_near"}

    rows = run_cypher(template["cypher"], {"id": entity["id"], "limit": limit})
    return {"entity": entity, "extraction": extraction, "rows": rows}
