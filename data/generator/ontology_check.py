"""Validates generated data against ontology/schema.yaml.

This is intentionally lightweight — it checks that every entity has the
schema's required properties and that every relationship's endpoints are
declared types, not a full validator. The point is to make the "data is
generated against the ontology" claim in docs/PLAN.md actually checked by
code, not just asserted in prose.
"""

from pathlib import Path

import yaml

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "ontology" / "schema.yaml"


def load_schema():
    with open(SCHEMA_PATH) as f:
        return yaml.safe_load(f)


def validate_entities(schema, entity_type, records):
    spec = schema["entities"][entity_type]
    required = [name for name, p in spec["properties"].items() if p.get("required")]
    for record in records:
        missing = [field for field in required if field not in record]
        if missing:
            raise ValueError(f"{entity_type} {record.get('id')} missing required fields: {missing}")
        for field, value in record.items():
            prop_spec = spec["properties"].get(field)
            if prop_spec and "enum" in prop_spec and value not in prop_spec["enum"]:
                raise ValueError(
                    f"{entity_type} {record.get('id')} field {field!r} = {value!r} "
                    f"not in allowed values {prop_spec['enum']}"
                )


def validate_relationship_targets(schema, rel_type, edges, entity_ids_by_type):
    spec = schema["relationships"][rel_type]
    to_types = spec["to"] if isinstance(spec["to"], list) else [spec["to"]]
    valid_to_ids = set()
    for t in to_types:
        valid_to_ids |= entity_ids_by_type.get(t, set())

    from_type = spec["from"]
    valid_from_ids = entity_ids_by_type.get(from_type, set())

    for edge in edges:
        if edge["from"] not in valid_from_ids:
            raise ValueError(f"{rel_type} edge {edge} has invalid 'from' id for type {from_type}")
        if edge["to"] not in valid_to_ids:
            raise ValueError(f"{rel_type} edge {edge} has invalid 'to' id for type {to_types}")
