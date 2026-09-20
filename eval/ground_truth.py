"""Computes each question's ground-truth relevant-ticket set directly from
data/generated/{graph,tickets,summary}.json — never from retrieval code, so
grading isn't circular (the system checking its own answers).
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "generated"


def _load(name: str):
    path = DATA_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"{path} not found — run `python -m data.generator.generate` first.")
    with open(path) as f:
        return json.load(f)


def _concerns_target_ground_truth(target_id: str) -> set[str]:
    graph = _load("graph.json")
    return {
        edge["from"]
        for edge in graph["relationships"]["CONCERNS"]
        if edge["to"] == target_id
    }


def _symptom_substring_ground_truth(substring: str) -> set[str]:
    tickets = _load("tickets.json")
    return {t["id"] for t in tickets if substring.lower() in t["text"].lower()}


def _incident_ground_truth(router_id: str) -> set[str]:
    summary = _load("summary.json")
    for incident in summary["incidents"]:
        if incident["router_id"] == router_id:
            return set(incident["ticket_ids"])
    raise ValueError(f"No incident found for router_id={router_id!r} in summary.json")


def ground_truth_for(question: dict) -> set[str]:
    spec = question["ground_truth"]
    kind = spec["kind"]
    if kind == "concerns_target":
        return _concerns_target_ground_truth(spec["target_id"])
    if kind == "symptom_substring":
        return _symptom_substring_ground_truth(spec["substring"])
    if kind == "incident":
        return _incident_ground_truth(spec["router_id"])
    raise ValueError(f"Unknown ground truth kind: {kind!r}")
