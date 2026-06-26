"""Run local M4 validation checks without network or writes."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.repo_safety_preflight import evaluate_repo_safety
from scripts.validate_governance_policy_manifest import validate_manifest


def _check(name: str, errors: list[dict]) -> dict:
    return {"name": name, "ok": not errors, "errors": errors}


def run_local_validation(repo_root: str | Path = ".", manifest_path: str | Path | None = None) -> dict:
    root = Path(repo_root)
    manifest_file = Path(manifest_path) if manifest_path else root / "docs/governance/governance_policy_manifest.json"
    checks = []
    preflight = evaluate_repo_safety(root)
    checks.append({"name": "repo_safety_preflight", "ok": preflight["ok"], "errors": preflight["errors"]})
    try:
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        manifest_errors = validate_manifest(manifest)
    except Exception as exc:
        manifest_errors = [{"code": "manifest_unreadable", "path": str(manifest_file), "message": str(exc)}]
    checks.append(_check("governance_policy_manifest", manifest_errors))
    return {"ok": all(c["ok"] for c in checks), "checks": checks, "network_used": False, "writes": False}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-only", action="store_true")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--manifest")
    args = ap.parse_args(argv)
    result = run_local_validation(args.repo_root, args.manifest)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
