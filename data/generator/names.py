"""Small self-contained word lists for generating realistic-looking names,
locations, and ticket text without an external dependency like Faker."""

import random

FIRST_NAMES = [
    "James", "Maria", "Robert", "Linda", "Michael", "Patricia", "David",
    "Jennifer", "John", "Elizabeth", "Carlos", "Aisha", "Wei", "Fatima",
    "Daniel", "Priya", "Thomas", "Sofia", "Kevin", "Grace", "Marcus",
    "Nadia", "Ethan", "Yuki", "Omar", "Rachel", "Andre", "Chloe",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Chen", "Lee", "Patel", "Khan", "Nguyen",
    "Kim", "Anderson", "Taylor", "Thomas", "Moore", "Jackson", "White",
    "Harris", "Clark", "Lewis", "Walker", "Young", "King", "Wright",
]

CITIES = [
    ("Newark", 40.7357, -74.1724), ("Trenton", 40.2206, -74.7597),
    ("Camden", 39.9259, -75.1196), ("Jersey City", 40.7178, -74.0431),
    ("Paterson", 40.9168, -74.1718), ("Edison", 40.5187, -74.4121),
    ("Elizabeth", 40.6640, -74.2107), ("Toms River", 39.9537, -74.1979),
]

ROUTER_MODELS = ["Cisco NCS 5500", "Juniper MX960", "Nokia 7750 SR", "Ciena 8180"]

INCIDENT_SYMPTOMS = [
    "intermittent dropouts during calls",
    "data speeds dropping to near zero for a few minutes at a time",
    "text messages arriving 10-20 minutes late",
    "no signal indoors despite full bars outside",
    "repeated 'network busy' errors when trying to place calls",
    "video calls freezing every few minutes",
    "connection resetting every time I move between rooms",
]

ROUTINE_SYMPTOMS = [
    "slightly slower streaming than usual in the evening",
    "occasional single dropped call, otherwise fine",
    "billing shows a charge I don't recognize",
    "asking about upgrading to a higher tier plan",
    "phone won't connect to 5G, falls back to LTE",
    "voicemail notifications arriving twice",
    "requesting a replacement SIM card",
]

TIME_QUALIFIERS = [
    "since this morning", "for the past two days", "starting last night",
    "on and off for a week", "since yesterday evening", "just now",
    "consistently for the last hour",
]


def random_person_name(rng: random.Random) -> str:
    return f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"


def random_location_near(rng: random.Random, base_lat: float, base_lon: float, spread: float = 0.05):
    lat = base_lat + rng.uniform(-spread, spread)
    lon = base_lon + rng.uniform(-spread, spread)
    return f"{lat:.4f},{lon:.4f}"
