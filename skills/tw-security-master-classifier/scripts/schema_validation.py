#!/usr/bin/env python3
"""Dependency-free validator for the JSON Schema subset used by this skill."""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any
from urllib.parse import urlparse


def _type_ok(value: Any, expected: str) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }.get(expected, True)


def _format_ok(value: str, name: str) -> bool:
    try:
        if name == "date":
            date.fromisoformat(value)
        elif name == "date-time":
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        elif name == "uri":
            parsed = urlparse(value)
            return bool(parsed.scheme and parsed.netloc)
    except ValueError:
        return False
    return True


def validate(instance: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    errors: list[str] = []
    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: expected const {schema['const']!r}")
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: value not in enum")

    expected = schema.get("type")
    if expected:
        types = expected if isinstance(expected, list) else [expected]
        if not any(_type_ok(instance, item) for item in types):
            errors.append(f"{path}: expected type {types}, got {type(instance).__name__}")
            return errors

    for keyword in ("anyOf", "oneOf"):
        if keyword in schema:
            matches = sum(not validate(instance, branch, path) for branch in schema[keyword])
            required_matches = 1 if keyword == "oneOf" else None
            if (keyword == "oneOf" and matches != required_matches) or (keyword == "anyOf" and matches < 1):
                errors.append(f"{path}: failed {keyword}")

    if isinstance(instance, dict):
        for required in schema.get("required", []):
            if required not in instance:
                errors.append(f"{path}: missing required property {required}")
        properties = schema.get("properties", {})
        for key, value in instance.items():
            if key in properties:
                errors.extend(validate(value, properties[key], f"{path}.{key}"))
            elif schema.get("additionalProperties") is False:
                errors.append(f"{path}: unexpected property {key}")
    elif isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0):
            errors.append(f"{path}: fewer than minItems")
        if isinstance(schema.get("items"), dict):
            for index, value in enumerate(instance):
                errors.extend(validate(value, schema["items"], f"{path}[{index}]"))
    elif isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0):
            errors.append(f"{path}: shorter than minLength")
        if schema.get("pattern") and not re.search(schema["pattern"], instance):
            errors.append(f"{path}: pattern mismatch")
        if schema.get("format") and not _format_ok(instance, schema["format"]):
            errors.append(f"{path}: invalid {schema['format']}")
    elif isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{path}: below minimum")
        if "maximum" in schema and instance > schema["maximum"]:
            errors.append(f"{path}: above maximum")
    return errors
