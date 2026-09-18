"""Generates Ticket entities plus FILED_BY / CONCERNS relationships.

Two kinds of tickets are generated:

- **Incident tickets**: clustered around a handful of deliberately chosen
  "faulty" routers, filed by customers actually downstream of that router
  in the topology. These clusters are what later phases' evaluation
  (docs/EVALUATION.md) uses for root-cause-style hybrid queries — e.g.
  "what's likely causing the outage tickets near Tower Y?" only makes
  sense if the tickets are actually structurally connected to a common
  cause, not just random noise.
- **Routine tickets**: unrelated background noise (billing, minor
  complaints) scattered across random customers, so incident clusters
  aren't the only signal in the dataset.
"""

import random
from datetime import datetime, timedelta, timezone

from .names import INCIDENT_SYMPTOMS, ROUTINE_SYMPTOMS, TIME_QUALIFIERS

INCIDENT_COUNT = 3
TICKETS_PER_INCIDENT = (12, 22)
ROUTINE_TICKET_COUNT = 100

FILED_OPENINGS = [
    "Calling to report",
    "I'm experiencing",
    "Writing in about",
    "Customer reports",
    "Support chat transcript:",
    "Filed via app —",
]


def _build_children_map(depends_on):
    children = {}
    for edge in depends_on:
        children.setdefault(edge["to"], []).append(edge["from"])
    return children


def _descendant_access_routers(router_id, routers_by_id, children_map):
    router = routers_by_id[router_id]
    if router["tier"] == "access":
        return [router_id]
    result = []
    for child_id in children_map.get(router_id, []):
        result.extend(_descendant_access_routers(child_id, routers_by_id, children_map))
    return result


def _random_timestamp(rng: random.Random):
    now = datetime(2026, 9, 15, tzinfo=timezone.utc)
    delta = timedelta(hours=rng.randint(1, 24 * 10), minutes=rng.randint(0, 59))
    return (now - delta).isoformat()


def _make_ticket_text(rng: random.Random, symptom_pool):
    opening = rng.choice(FILED_OPENINGS)
    symptom = rng.choice(symptom_pool)
    qualifier = rng.choice(TIME_QUALIFIERS)
    return f"{opening} {symptom}, {qualifier}."


def generate_tickets(rng: random.Random, routers, towers, connects_to, depends_on, serves):
    routers_by_id = {r["id"]: r for r in routers}
    children_map = _build_children_map(depends_on)

    tower_to_router = {e["from"]: e["to"] for e in connects_to}
    customer_to_tower = {}
    tower_to_customers = {}
    for e in serves:
        tower_id, customer_id = e["from"], e["to"]
        customer_to_tower[customer_id] = tower_id
        tower_to_customers.setdefault(tower_id, []).append(customer_id)

    candidate_routers = [r for r in routers if r["tier"] in ("access", "regional")]
    incident_routers = rng.sample(candidate_routers, min(INCIDENT_COUNT, len(candidate_routers)))

    tickets = []
    filed_by = []
    concerns = []
    ticket_seq = 0
    incidents_summary = []

    def next_ticket_id():
        nonlocal ticket_seq
        ticket_seq += 1
        return f"ticket-{ticket_seq:04d}"

    for incident_router in incident_routers:
        access_router_ids = _descendant_access_routers(incident_router["id"], routers_by_id, children_map)
        affected_towers = [t for t in towers if tower_to_router.get(t["id"]) in access_router_ids]
        affected_customers = [
            c for t in affected_towers for c in tower_to_customers.get(t["id"], [])
        ]
        if not affected_customers:
            continue

        n_tickets = rng.randint(*TICKETS_PER_INCIDENT)
        incidents_summary.append({
            "router_id": incident_router["id"],
            "router_tier": incident_router["tier"],
            "affected_tower_count": len(affected_towers),
            "affected_customer_count": len(affected_customers),
            "ticket_count": n_tickets,
        })

        for _ in range(n_tickets):
            ticket_id = next_ticket_id()
            customer_id = rng.choice(affected_customers)
            tower_id = customer_to_tower[customer_id]
            status = rng.choices(["open", "resolved"], weights=[0.7, 0.3])[0]

            tickets.append({
                "id": ticket_id,
                "text": _make_ticket_text(rng, INCIDENT_SYMPTOMS),
                "category": rng.choices(["outage", "degraded_service"], weights=[0.6, 0.4])[0],
                "created_at": _random_timestamp(rng),
                "status": status,
            })
            filed_by.append({"from": ticket_id, "to": customer_id})

            if incident_router["tier"] == "regional" and rng.random() < 0.3:
                concerns.append({"from": ticket_id, "to": incident_router["id"], "to_type": "Router"})
            else:
                concerns.append({"from": ticket_id, "to": tower_id, "to_type": "CellTower"})

    all_customer_ids = list(customer_to_tower.keys())
    for _ in range(ROUTINE_TICKET_COUNT):
        ticket_id = next_ticket_id()
        customer_id = rng.choice(all_customer_ids)
        tower_id = customer_to_tower[customer_id]
        status = rng.choices(["open", "resolved"], weights=[0.3, 0.7])[0]

        tickets.append({
            "id": ticket_id,
            "text": _make_ticket_text(rng, ROUTINE_SYMPTOMS),
            "category": rng.choices(
                ["degraded_service", "billing", "other"], weights=[0.4, 0.35, 0.25]
            )[0],
            "created_at": _random_timestamp(rng),
            "status": status,
        })
        filed_by.append({"from": ticket_id, "to": customer_id})
        concerns.append({"from": ticket_id, "to": tower_id, "to_type": "CellTower"})

    return tickets, filed_by, concerns, incidents_summary
