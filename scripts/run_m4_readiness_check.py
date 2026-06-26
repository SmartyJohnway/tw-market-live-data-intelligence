"""Aggregate M4 readiness checks; fail closed without explicit production refresh confirmation."""
from __future__ import annotations
import argparse, json, sys, hashlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.run_m4_local_validation import run_local_validation
from scripts.validate_source_registry import validate_source_registry
from scripts.run_fixture_replay_scenarios import run_scenarios
from scripts.validate_authorization_ladder import validate_authorization_ladder
from scripts.json_schema_validation import validate_json_schema


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _check(name: str, errors: list[dict] | None = None, ok: bool | None = None, detail=None) -> dict:
    if ok is None:
        ok = not errors
    return {"name": name, "ok": bool(ok), "errors": errors or [], "detail": detail}


def validate_evidence_ledger(repo_root: Path, ledger_path: Path | None = None) -> list[dict]:
    ledger_path = ledger_path or repo_root / "tests/fixtures/evidence/fixture_evidence_ledger.json"
    schema = _load(repo_root / "docs/evidence/evidence_ledger_schema.json")
    errors = []
    try:
        ledger = _load(ledger_path)
    except Exception as exc:
        return [{"code": "ledger_unreadable", "path": str(ledger_path), "message": str(exc)}]
    evidence_entries = ledger.get("evidence") if isinstance(ledger, dict) else None
    if not isinstance(evidence_entries, list):
        return [{"code": "evidence_missing_or_not_array", "path": "$.evidence"}]
    if not evidence_entries:
        errors.append({"code": "evidence_empty", "path": "$.evidence"})
    for idx, entry in enumerate(evidence_entries):
        if not isinstance(entry, dict):
            errors.append({"code": "evidence_entry_not_object", "path": f"$.evidence[{idx}]", "message": "evidence entry must be an object"})
            continue
        for error in validate_json_schema(entry, schema, f"$.evidence[{idx}]"):
            errors.append(error)
        fixture_path = repo_root / entry.get("fixture_path", "")
        if not fixture_path.exists():
            errors.append({"code": "missing_fixture", "path": str(fixture_path)})
        elif hashlib.sha256(fixture_path.read_bytes()).hexdigest() != entry.get("hash_sha256"):
            errors.append({"code": "hash_mismatch", "path": str(fixture_path)})
    return errors


def validate_release_gate_matrix(repo_root: Path, matrix_path: Path | None = None) -> list[dict]:
    matrix_path = matrix_path or repo_root / "docs/release/release_gate_matrix.json"
    try:
        matrix = _load(matrix_path)
    except Exception as exc:
        return [{"code": "release_gate_matrix_unreadable", "path": str(matrix_path), "message": str(exc)}]
    errors = []
    if matrix.get("current_allowed_level") != "local_only_fixture_only":
        errors.append({"code": "current_level_must_remain_local_only_fixture_only", "path": "$.current_allowed_level"})
    for gate in matrix.get("gates", []):
        if gate.get("gate") in {"controlled live probe authorization", "frontend publication authorization", "production refresh authorization"} and gate.get("allowed") is not False:
            errors.append({"code": "future_gate_must_not_be_allowed", "path": gate.get("gate")})
    return errors


def run_readiness_check(repo_root: str | Path = ".", scenarios_path: str | Path | None = None) -> dict:
    root = Path(repo_root)
    checks = []
    local = run_local_validation(root)
    checks.append(_check("local_validation", ok=local["ok"], detail=local))
    checks.append(_check("source_registry", validate_source_registry(
        _load(root / "docs/source_registry/source_authority_registry.json"),
        _load(root / "docs/source_registry/source_risk_flag_catalog.json"),
        _load(root / "docs/source_registry/source_contract_schema.json"),
        _load(root / "docs/source_registry/source_family_coverage_matrix.json"),
    )))
    checks.append(_check("evidence_ledger", validate_evidence_ledger(root)))
    replay_paths = [Path(scenarios_path)] if scenarios_path else [
        root / "tests/fixtures/replay_scenarios/valid_replay_scenarios.json",
        root / "tests/fixtures/replay_scenarios/failure_injection_scenarios.json",
    ]
    replay_details = []
    replay_ok = True
    for replay_path in replay_paths:
        replay = run_scenarios(replay_path)
        replay_details.append({"path": str(replay_path), "result": replay})
        replay_ok = replay_ok and replay["failed"] == 0
    checks.append(_check("fixture_replay", ok=replay_ok, detail=replay_details))
    checks.append(_check("authorization_ladder", validate_authorization_ladder({})))
    checks.append(_check("release_gate_matrix", validate_release_gate_matrix(root)))
    return {"ok": all(c["ok"] for c in checks), "checks": checks, "network_used": False, "writes": False, "production_ready": False}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-only", action="store_true")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--scenarios")
    args = ap.parse_args(argv)
    result = run_readiness_check(args.repo_root, args.scenarios)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
