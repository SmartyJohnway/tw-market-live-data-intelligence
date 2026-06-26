"""Build a frontend readonly context package from validated staging payloads."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from controlled_refresh_staging_validator import validate_controlled_refresh_staging_payload
from controlled_refresh_staging_writer import is_forbidden_output_dir

REQUIRED_CONFIRMATIONS = ["confirm_readonly_package", "confirm_no_frontend_public_write", "confirm_no_production_write", "confirm_no_trading_signal"]
REQUIRED_CAVEATS = ["not_realtime_guaranteed", "not_trading_signal", "not_production_current_state", "source_risk_present", "freshness_must_be_displayed"]

def _price(sample: dict):
    for key in ("price", "last_price", "close", "z"):
        if isinstance(sample, dict) and key in sample: return sample[key]
    return None

def build_frontend_readonly_context_package(staging_payload: dict) -> dict:
    errors = validate_controlled_refresh_staging_payload(staging_payload)
    if errors: raise ValueError(f"invalid staging payload: {errors}")
    symbols = []
    sources = []
    for run in staging_payload.get("source_runs", []):
        sources.append({"source_id": run["source_id"], "source_authority": run["authority_level"], "source_risk_flags": run["source_risk_flags"]})
        sample = run.get("normalized_sample_preview") or {}
        symbol = sample.get("symbol") or sample.get("code") or "unknown"
        caveats = list(REQUIRED_CAVEATS)
        if run["freshness_status"] == "stale": caveats.append("stale_source_row")
        if run["delay_status"] == "delayed_candidate": caveats.append("delayed_source_row")
        if run["freshness_status"] == "live_candidate": caveats.append("live_candidate_not_realtime_guaranteed")
        symbols.append({
            "symbol": symbol, "source_id": run["source_id"], "source_authority": run["authority_level"],
            "price_like_value": _price(sample), "price_semantics": "source_normalized_preview_only",
            "freshness_status": run["freshness_status"], "delay_status": run["delay_status"],
            "staleness_seconds": run["staleness_seconds"], "retrieved_at": run["retrieved_at_utc"],
            "source_timestamp": run["source_timestamp"], "normalization_status": run["normalization_status"],
            "data_quality_flags": run["data_quality_flags"], "source_risk_flags": run["source_risk_flags"],
            "display_caveats": caveats,
        })
    package = {
        "schema_version": "frontend_readonly_context_package.v1",
        "generated_at_utc": staging_payload["generated_at_utc"],
        "readonly_only": True, "production_current_state": False, "frontend_public_artifact": False,
        "realtime_guaranteed": False, "trading_signal": False,
        "sources": sources, "symbols": symbols, "global_caveats": REQUIRED_CAVEATS,
        "validation": {"staging_payload_valid": True, "required_caveats_present": True},
    }
    return package

def validate_frontend_readonly_context_package(package: dict) -> list[dict]:
    errors=[]
    for key in REQUIRED_CAVEATS:
        if key not in package.get("global_caveats", []): errors.append({"code":"missing_caveat","path":"$.global_caveats","message":key})
    for flag in ("readonly_only",):
        if package.get(flag) is not True: errors.append({"code":"flag_required","path":f"$.{flag}","message":"must be true"})
    for flag in ("production_current_state", "frontend_public_artifact", "realtime_guaranteed", "trading_signal"):
        if package.get(flag) is not False: errors.append({"code":"flag_forbidden","path":f"$.{flag}","message":"must be false"})
    return errors

def write_frontend_readonly_context_package(package: dict, output_dir: str | Path) -> Path:
    reason = is_forbidden_output_dir(output_dir)
    if reason: raise ValueError(reason)
    errors = validate_frontend_readonly_context_package(package)
    if errors: raise ValueError(f"invalid frontend readonly package: {errors}")
    out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    dest = out / "frontend_readonly_context_package.json"
    dest.write_text(json.dumps(package, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return dest

def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument("--input-staging-payload", required=True); ap.add_argument("--output-dir", required=True)
    for c in REQUIRED_CONFIRMATIONS: ap.add_argument("--"+c.replace("_","-"), action="store_true")
    args=ap.parse_args(argv)
    missing=[c for c in REQUIRED_CONFIRMATIONS if not getattr(args,c)]
    if missing: raise SystemExit(f"missing required confirmation flags: {', '.join(missing)}")
    reason=is_forbidden_output_dir(args.output_dir)
    if reason: raise SystemExit(reason)
    payload=json.loads(Path(args.input_staging_payload).read_text(encoding="utf-8"))
    write_frontend_readonly_context_package(build_frontend_readonly_context_package(payload), args.output_dir)
    return 0
if __name__ == "__main__": raise SystemExit(main())
