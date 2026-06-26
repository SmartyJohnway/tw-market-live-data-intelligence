"""Fixture-backed controlled refresh staging writer with fail-closed CLI."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from controlled_refresh_staging_validator import validate_controlled_refresh_staging_payload

REQUIRED_CONFIRMATIONS = [
    "confirm_controlled_refresh", "confirm_staging_write_only", "confirm_no_production_write",
    "confirm_no_frontend_write", "confirm_no_generated_artifact_write", "confirm_no_trading_signal",
    "confirm_bounded_targets",
]

def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]

def is_forbidden_output_dir(path: str | Path) -> str | None:
    p = Path(path)
    text = str(p).replace("\\", "/")
    parts = {part.lower() for part in p.parts}
    if "research/generated" in text: return "research/generated output is forbidden"
    if "frontend/public" in text: return "frontend/public output is forbidden"
    if "production" in parts or "prod" in parts or "current_market_state" in text: return "production-looking output path is forbidden"
    return None

def build_controlled_refresh_staging_payload(source_runs: list[dict], *, generated_at_utc: str, target_universe: dict, operator_confirmations: list[str]) -> dict:
    payload = {
        "schema_version": "controlled_refresh_staging_payload.v1",
        "generated_at_utc": generated_at_utc,
        "staging_only": True,
        "operator_confirmations": list(operator_confirmations),
        "target_universe": target_universe,
        "source_runs": source_runs,
        "validation": {
            "network_authorized": False, "production_write": False, "frontend_write": False,
            "generated_artifact_write": False, "full_market_scan": False, "trading_signal": False,
        },
    }
    payload["validation"]["errors"] = validate_controlled_refresh_staging_payload(payload)
    return payload

def write_staging_payload(payload: dict, output_dir: str | Path) -> Path:
    reason = is_forbidden_output_dir(output_dir)
    if reason: raise ValueError(reason)
    errors = validate_controlled_refresh_staging_payload(payload)
    if errors: raise ValueError(f"invalid staging payload: {errors}")
    out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    dest = out / "controlled_refresh_staging_payload.json"
    dest.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return dest

def _confirmations(args) -> list[str]:
    missing = [c for c in REQUIRED_CONFIRMATIONS if not getattr(args, c)]
    if missing: raise SystemExit(f"missing required confirmation flags: {', '.join(missing)}")
    return REQUIRED_CONFIRMATIONS

def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-fixture", required=True); ap.add_argument("--output-dir", required=True)
    for c in REQUIRED_CONFIRMATIONS: ap.add_argument("--" + c.replace("_", "-"), action="store_true")
    args = ap.parse_args(argv)
    confirmations = _confirmations(args)
    reason = is_forbidden_output_dir(args.output_dir)
    if reason: raise SystemExit(reason)
    fixture = json.loads(Path(args.input_fixture).read_text(encoding="utf-8"))
    payload = build_controlled_refresh_staging_payload(
        fixture.get("source_runs", []), generated_at_utc=fixture["generated_at_utc"],
        target_universe=fixture.get("target_universe", {}), operator_confirmations=confirmations)
    write_staging_payload(payload, args.output_dir)
    return 0
if __name__ == "__main__": raise SystemExit(main())
