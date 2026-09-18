"""Generates the network topology: core/regional/access Routers and the
CellTowers they serve, per ontology/schema.yaml.

Structure is a tree: each core router has several regional children, each
regional router has several access children, and each access router has
several cell towers connected to it. DEPENDS_ON always points from a lower
tier to its parent; CONNECTS_TO always points from a CellTower to its
access router.
"""

import random

CORE_ROUTER_COUNT = 3
REGIONAL_PER_CORE = (2, 3)
ACCESS_PER_REGIONAL = (2, 3)
TOWERS_PER_ACCESS = (1, 3)


def generate_topology(rng: random.Random, cities, router_models):
    routers = []
    towers = []
    depends_on = []
    connects_to = []

    router_seq = 0
    tower_seq = 0

    def next_router_id():
        nonlocal router_seq
        router_seq += 1
        return f"router-{router_seq:03d}"

    def next_tower_id():
        nonlocal tower_seq
        tower_seq += 1
        return f"tower-{tower_seq:03d}"

    for _ in range(CORE_ROUTER_COUNT):
        city_name, lat, lon = rng.choice(cities)
        core_id = next_router_id()
        routers.append({
            "id": core_id,
            "name": f"Core Router {core_id.split('-')[1]} ({city_name})",
            "tier": "core",
            "location": f"{lat:.4f},{lon:.4f}",
            "model": rng.choice(router_models),
        })

        for _ in range(rng.randint(*REGIONAL_PER_CORE)):
            city_name, lat, lon = rng.choice(cities)
            regional_id = next_router_id()
            routers.append({
                "id": regional_id,
                "name": f"Regional Router {regional_id.split('-')[1]} ({city_name})",
                "tier": "regional",
                "location": f"{lat:.4f},{lon:.4f}",
                "model": rng.choice(router_models),
            })
            depends_on.append({"from": regional_id, "to": core_id})

            for _ in range(rng.randint(*ACCESS_PER_REGIONAL)):
                city_name, lat, lon = rng.choice(cities)
                access_id = next_router_id()
                routers.append({
                    "id": access_id,
                    "name": f"Access Router {access_id.split('-')[1]} ({city_name})",
                    "tier": "access",
                    "location": f"{lat:.4f},{lon:.4f}",
                    "model": rng.choice(router_models),
                })
                depends_on.append({"from": access_id, "to": regional_id})

                for _ in range(rng.randint(*TOWERS_PER_ACCESS)):
                    tower_lat = lat + rng.uniform(-0.02, 0.02)
                    tower_lon = lon + rng.uniform(-0.02, 0.02)
                    tower_id = next_tower_id()
                    towers.append({
                        "id": tower_id,
                        "name": f"Tower {tower_id.split('-')[1]} ({city_name})",
                        "location": f"{tower_lat:.4f},{tower_lon:.4f}",
                        "capacity": rng.choice([500, 750, 1000, 1500]),
                    })
                    connects_to.append({"from": tower_id, "to": access_id})

    return routers, towers, depends_on, connects_to
