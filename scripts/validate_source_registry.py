"""Validate source registry, schema, risk catalog, and coverage matrix consistency."""
from __future__ import annotations
import argparse, json
from pathlib import Path


def _required_fields(schema: dict) -> set[str]:
    return set(schema.get("required", schema.get("required_source_fields", [])))


def validate_source_registry(reg: dict, cat: dict, schema: dict, cov: dict) -> list[dict]:
    errors = []
    flags = {x["risk_flag"] for x in cat.get("risk_flags", [])}
    fields = _required_fields(schema)
    allowed_enums = {k: set(v.get("enum", [])) for k, v in schema.get("properties", {}).items() if "enum" in v}
    families = cov.get("families", {})
    for source in reg.get("sources", []):
        source_id = source.get("source_id")
        missing = fields - set(source)
        if missing:
            errors.append({"code": "missing_source_fields", "source_id": source_id, "fields": sorted(missing)})
        extra = set(source) - fields
        if schema.get("additionalProperties") is False and extra:
            errors.append({"code": "unexpected_source_fields", "source_id": source_id, "fields": sorted(extra)})
        for field, allowed in allowed_enums.items():
            if field in source and source[field] not in allowed:
                errors.append({"code": "invalid_source_enum", "source_id": source_id, "field": field, "value": source[field]})
        for risk_flag in source.get("risk_flags", []):
            if risk_flag not in flags:
                errors.append({"code": "unknown_risk_flag", "source_id": source_id, "flag": risk_flag})
        if source.get("production_current_state_allowed") is not False:
            errors.append({"code": "production_not_allowed", "source_id": source_id})
        if source.get("source_family") not in families:
            errors.append({"code": "missing_family_coverage", "source_id": source_id, "family": source.get("source_family")})
    return errors


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", default="docs/source_registry/source_authority_registry.json")
    ap.add_argument("--catalog", default="docs/source_registry/source_risk_flag_catalog.json")
    ap.add_argument("--schema", default="docs/source_registry/source_contract_schema.json")
    ap.add_argument("--coverage", default="docs/source_registry/source_family_coverage_matrix.json")
    args = ap.parse_args(argv)
    errs = validate_source_registry(*(json.loads(Path(p).read_text(encoding="utf-8")) for p in [args.registry, args.catalog, args.schema, args.coverage]))
    print(json.dumps({"ok": not errs, "errors": errs}, indent=2, sort_keys=True))
    return 0 if not errs else 1


if __name__ == "__main__":
    raise SystemExit(main())
