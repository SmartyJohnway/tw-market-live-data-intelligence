"""Small local JSON-schema subset validator for M4 contracts (no network, no dependencies)."""
from __future__ import annotations
import re
from datetime import datetime

_TYPE_MAP = {
    "object": dict,
    "array": list,
    "string": str,
    "boolean": bool,
    "integer": int,
    "number": (int, float),
}


def _type_ok(value, expected: str) -> bool:
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, _TYPE_MAP[expected])


def _valid_datetime(value: str) -> bool:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def validate_json_schema_subset(instance, schema: dict, path: str = "$") -> list[dict]:
    errors: list[dict] = []
    if "const" in schema and instance != schema["const"]:
        errors.append({"code": "schema_const_mismatch", "path": path, "expected": schema["const"], "actual": instance})
    if "enum" in schema and instance not in schema["enum"]:
        errors.append({"code": "schema_enum_mismatch", "path": path, "allowed": schema["enum"], "actual": instance})
    expected_type = schema.get("type")
    if expected_type:
        allowed = expected_type if isinstance(expected_type, list) else [expected_type]
        if not any(_type_ok(instance, t) for t in allowed):
            errors.append({"code": "schema_type_mismatch", "path": path, "expected": allowed, "actual_type": type(instance).__name__})
            return errors
    if isinstance(instance, str):
        if schema.get("minLength") is not None and len(instance) < schema["minLength"]:
            errors.append({"code": "schema_min_length", "path": path})
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            errors.append({"code": "schema_pattern_mismatch", "path": path, "pattern": schema["pattern"]})
        if schema.get("format") == "date-time" and not _valid_datetime(instance):
            errors.append({"code": "schema_datetime_format", "path": path})
    if isinstance(instance, dict):
        required = set(schema.get("required", []))
        for key in sorted(required - set(instance)):
            errors.append({"code": "schema_required_missing", "path": f"{path}.{key}"})
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in sorted(set(instance) - set(properties)):
                errors.append({"code": "schema_additional_property", "path": f"{path}.{key}"})
        for key, subschema in properties.items():
            if key in instance:
                errors.extend(validate_json_schema_subset(instance[key], subschema, f"{path}.{key}"))
    if isinstance(instance, list):
        if "items" in schema:
            for idx, item in enumerate(instance):
                errors.extend(validate_json_schema_subset(item, schema["items"], f"{path}[{idx}]"))
        if "contains" in schema and not any(not validate_json_schema_subset(item, schema["contains"], f"{path}[]") for item in instance):
            errors.append({"code": "schema_contains_missing", "path": path})
    return errors
