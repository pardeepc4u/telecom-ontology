"""Generates ServicePlans and Customers, and the SERVES / SUBSCRIBES_TO
relationships that link them into the topology, per ontology/schema.yaml.
"""

import random

from .names import random_person_name

SERVICE_PLANS = [
    {"id": "plan-basic", "name": "Basic Talk & Text", "sla_tier": "basic"},
    {"id": "plan-standard", "name": "Standard Unlimited", "sla_tier": "standard"},
    {"id": "plan-premium", "name": "Premium Unlimited 5G", "sla_tier": "premium"},
    {"id": "plan-business-std", "name": "Business Standard", "sla_tier": "standard"},
    {"id": "plan-business-prem", "name": "Business Premium", "sla_tier": "premium"},
]

CUSTOMERS_PER_TOWER = (3, 8)

ACCOUNT_TIER_BY_PLAN = {
    "plan-basic": "standard",
    "plan-standard": "standard",
    "plan-premium": "premium",
    "plan-business-std": "business",
    "plan-business-prem": "business",
}


def generate_customers(rng: random.Random, towers):
    customers = []
    serves = []
    subscribes_to = []

    customer_seq = 0

    for tower in towers:
        n = rng.randint(*CUSTOMERS_PER_TOWER)
        for _ in range(n):
            customer_seq += 1
            customer_id = f"customer-{customer_seq:04d}"
            plan = rng.choice(SERVICE_PLANS)
            customers.append({
                "id": customer_id,
                "name": random_person_name(rng),
                "account_tier": ACCOUNT_TIER_BY_PLAN[plan["id"]],
            })
            serves.append({"from": tower["id"], "to": customer_id})
            subscribes_to.append({"from": customer_id, "to": plan["id"]})

    return SERVICE_PLANS, customers, serves, subscribes_to
