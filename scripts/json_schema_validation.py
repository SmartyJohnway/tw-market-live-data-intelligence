"""Standards-based Draft 2020-12 JSON Schema validation helpers for M4 contracts."""
from __future__ import annotations
from collections.abc import Iterable
from jsonschema import Draft202012Validator, FormatChecker, SchemaError
from datetime import datetime


def _json_path(parts: Iterable) -> str:
    path = "$"
    for part in parts:
        if isinstance(part, int):
            path += f"[{part}]"
        else:
            path += f".{part}"
    return path


def _schema_path(parts: Iterable) -> str:
    return "/" + "/".join(str(part) for part in parts)


def _error_code(error) -> str:
    return f"schema_{error.validator}"


def _normalize_error(error) -> dict:
    result = {
        "code": _error_code(error),
        "path": _json_path(error.absolute_path),
        "message": error.message,
        "schema_path": _schema_path(error.absolute_schema_path),
    }
    if error.validator == "required":
        result["code"] = "schema_required_missing"
    elif error.validator == "additionalProperties":
        result["code"] = "schema_additional_property"
    elif error.validator == "type":
        result["code"] = "schema_type_mismatch"
    elif error.validator == "enum":
        result["code"] = "schema_enum_mismatch"
    elif error.validator == "const":
        result["code"] = "schema_const_mismatch"
    elif error.validator == "pattern":
        result["code"] = "schema_pattern_mismatch"
    elif error.validator == "format":
        result["code"] = "schema_format"
    elif error.validator == "contains":
        result["code"] = "schema_contains_missing"
    return result



def _is_date_time(value: str) -> bool:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def _custom_format_errors(instance, schema: dict, path: str = "$") -> list[dict]:
    errors: list[dict] = []
    if isinstance(schema, dict) and schema.get("format") == "date-time" and isinstance(instance, str) and not _is_date_time(instance):
        errors.append({"code": "schema_format", "path": path, "message": f"{instance!r} is not a 'date-time'", "schema_path": "/format"})
    if isinstance(instance, dict) and isinstance(schema, dict):
        for key, subschema in schema.get("properties", {}).items():
            if key in instance:
                errors.extend(_custom_format_errors(instance[key], subschema, f"{path}.{key}"))
    if isinstance(instance, list) and isinstance(schema, dict) and "items" in schema:
        for idx, item in enumerate(instance):
            errors.extend(_custom_format_errors(item, schema["items"], f"{path}[{idx}]"))
    return errors

def validate_json_schema(instance, schema: dict, path: str = "$") -> list[dict]:
    """Validate an instance with Draft 2020-12 + FormatChecker and return stable JSON errors."""
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        return [{
            "code": "invalid_schema",
            "path": path,
            "message": exc.message,
            "schema_path": _schema_path(exc.absolute_schema_path),
        }]
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = [_normalize_error(error) for error in validator.iter_errors(instance)]
    errors.extend(_custom_format_errors(instance, schema, "$"))
    for error in errors:
        if path != "$" and error["path"].startswith("$"):
            error["path"] = path + error["path"][1:]
    return sorted(errors, key=lambda e: (e["path"], e["code"], e["message"], e.get("schema_path", "")))


# Backwards-compatible alias for older M4 call sites/tests.
def validate_json_schema_subset(instance, schema: dict, path: str = "$") -> list[dict]:
    return validate_json_schema(instance, schema, path)


def check_schema(schema: dict) -> list[dict]:
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        return [{"code": "invalid_schema", "path": "$", "message": exc.message, "schema_path": _schema_path(exc.absolute_schema_path)}]
    return []
