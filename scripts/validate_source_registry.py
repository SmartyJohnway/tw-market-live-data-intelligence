"""Validate source registry, schema, risk catalog, and coverage matrix consistency."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.json_schema_validation import validate_json_schema_subset

REQUIRED_SOURCE_IDS = {
    "TWSE_OpenAPI",
    "TPEx_OpenAPI",
    "TWSE_MIS",
    "Yahoo_Finance",
    "Fixture_Synthetic",
    "Manual_Operator_Input",
}


def validate_source_registry(reg: dict, cat: dict, schema: dict, cov: dict) -> list[dict]:
    errors: list[dict] = []
    if not isinstance(reg, dict):
        return [{"code": "registry_not_object", "path": "$"}]
    sources = reg.get("sources")
    if not isinstance(sources, list):
        return [{"code": "registry_sources_missing_or_not_array", "path": "$.sources"}]
    if not sources:
        errors.append({"code": "registry_sources_empty", "path": "$.sources"})
    flags = {x.get("risk_flag") for x in cat.get("risk_flags", []) if isinstance(x, dict)}
    families = cov.get("families", {}) if isinstance(cov, dict) else {}
    seen_source_ids: set[str] = set()
    for idx, source in enumerate(sources):
        source_path = f"$.sources[{idx}]"
        if not isinstance(source, dict):
            errors.append({"code": "source_entry_not_object", "path": source_path})
            continue
        errors.extend(validate_json_schema_subset(source, schema, source_path))
        source_id = source.get("source_id")
        if source_id:
            seen_source_ids.add(source_id)
        for risk_flag in source.get("risk_flags", []):
            if risk_flag not in flags:
                errors.append({"code": "unknown_risk_flag", "source_id": source_id, "flag": risk_flag, "path": f"{source_path}.risk_flags"})
        if source.get("source_family") not in families:
            errors.append({"code": "missing_family_coverage", "source_id": source_id, "family": source.get("source_family"), "path": f"{source_path}.source_family"})
    missing_required = sorted(REQUIRED_SOURCE_IDS - seen_source_ids)
    if missing_required:
        errors.append({"code": "required_sources_missing", "path": "$.sources", "source_ids": missing_required})
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
