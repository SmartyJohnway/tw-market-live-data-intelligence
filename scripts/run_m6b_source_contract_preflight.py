from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.m5k_common import dump_json, execute_live_observation, governance, plan_live_observation, utc_now, validate_watchlist

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "research/live_observation_runs/m6b_source_contract"
SCHEMA_VERSION = "m6b_source_contract_preflight.v1"
TARGETS = ["2330", "0050", "TX"]


def bounded_watchlist() -> dict[str, Any]:
    return {
        "schema_version": "m5n_watchlist.v1",
        "watchlist_id": "m6b_source_contract_bounded_targets",
        "name": "M6B source contract bounded targets",
        "description": "Manual bounded source-contract checks; not a scanner and not default CI.",
        "governance": {"bounded_observation_only": True, "trading_signal": False, "recommendations_allowed": False},
        "items": [
            {"id": "twse:2330", "symbol": "2330", "display_name": "2330", "market": "twse", "instrument_type": "listed_stock", "adapter": "twse_mis_equity_etf_quote", "preferred_sources": ["TWSE_MIS"], "category": "m6b_contract", "enabled": True, "display_order": 1, "tags": ["m6b_contract"], "notes": "Source-contract probe target; descriptive only."},
            {"id": "twse:0050", "symbol": "0050", "display_name": "0050", "market": "twse", "instrument_type": "listed_etf", "adapter": "twse_mis_equity_etf_quote", "preferred_sources": ["TWSE_MIS"], "category": "m6b_contract", "enabled": True, "display_order": 2, "tags": ["m6b_contract"], "notes": "Source-contract probe target; descriptive only."},
            {"id": "taifex:TX", "symbol": "TX", "display_name": "TX", "market": "taifex", "instrument_type": "futures", "adapter": "taifex_mis_tx_futures_quote", "preferred_sources": ["TAIFEX_MIS"], "category": "m6b_contract", "enabled": True, "display_order": 3, "tags": ["m6b_contract"], "notes": "Source-contract probe target; descriptive only.", "contract_code": "TXF", "contract_selector": "front_month"},
        ],
    }


def _family(plan: dict[str, Any]) -> str:
    if plan.get("source") == "TAIFEX":
        return "TAIFEX_MIS"
    return "TWSE_MIS"


def _endpoint_kind(plan: dict[str, Any]) -> str:
    return "taifex_mis_tx_route" if plan.get("source") == "TAIFEX" else "twse_mis_equity_etf_route"


def _status_from_evidence(evidence: dict[str, Any] | None, key: str) -> str:
    if not evidence:
        return "not_executed"
    if evidence.get("reason"):
        reason = str(evidence.get("reason"))
        if "CERTIFICATE" in reason.upper() or "SSL" in reason.upper() or "TLS" in reason.upper():
            return "failed_with_tls_diagnostic"
        return "failed_closed"
    return key


def build_report(*, mode: str, live_result: dict[str, Any] | None = None) -> dict[str, Any]:
    watchlist = bounded_watchlist()
    plan = plan_live_observation(watchlist)
    validation = validate_watchlist(watchlist, max_targets=len(TARGETS))
    observations = {o.get("symbol"): o for o in (live_result or {}).get("observations", []) if isinstance(o, dict)}
    failures = {f.get("symbol"): f for f in (live_result or {}).get("failures", []) if isinstance(f, dict)}
    evidence_by_source = {e.get("source"): e for e in (live_result or {}).get("source_investigation_notes", []) if isinstance(e, dict)}
    checks = []
    for planned in plan.get("planned_routes", []):
        symbol = planned.get("symbol")
        obs = observations.get(symbol)
        failure = failures.get(symbol)
        evidence = evidence_by_source.get("TAIFEX" if planned.get("source") == "TAIFEX" else "TWSE_MIS")
        failure_reason = (failure or {}).get("reason") or (evidence or {}).get("reason")
        checks.append({
            "target": symbol,
            "source_family": _family(planned),
            "endpoint_kind": _endpoint_kind(planned),
            "tls_status": "not_executed" if mode == "check_only" else _status_from_evidence(evidence, "strict_tls_completed_or_http_layer_reached"),
            "http_status": None if mode == "check_only" else (evidence or {}).get("status_code") or (live_result or {}).get("request", {}).get("status_code"),
            "json_parse_status": "not_executed" if mode == "check_only" else ("parsed" if obs or failure or (evidence and not evidence.get("reason")) else "failed_closed"),
            "required_fields_status": "not_executed" if mode == "check_only" else ("present_or_governed_failure" if obs or failure else "failed_closed"),
            "normalization_status": "not_executed" if mode == "check_only" else ("normalized_observation" if obs else "governed_failure"),
            "observation_status": (obs or failure or {}).get("status") if mode != "check_only" else "not_executed",
            "reference_only": bool((obs or {}).get("reference_only")),
            "failure_reason": failure_reason,
            "recommended_next_step": (failure or {}).get("recommended_next_step") or ("Execute explicit bounded preflight if preparing release." if mode == "check_only" else "Review governed diagnostic; rerun later only if needed."),
            "raw_payload_included": False,
        })
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": utc_now(),
        "mode": mode,
        "targets": TARGETS,
        "checks": checks,
        "ssl_policy": {"selected": "strict", "strict_default": True, "compatibility_policy": "not_implemented_m6c_follow_up", "unsafe_policy": "not_implemented_and_not_used", "silent_tls_disable": False},
        "raw_payload_included": False,
        "network_calls_may_have_occurred": mode == "execute_live_contract_check",
        "governance": governance() | {"m6b_source_contract_preflight": True, "writes_m5f": False, "writes_frontend_public": False, "writes_research_generated": False, "raw_endpoint_payload_included": False, "default_ci": False, "manual_explicit_only": True, "no_polling": True, "no_scheduler": True, "no_full_market_scan": True, "no_trading_output": True, "watchlist_validation": validation},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="M6B bounded source-contract preflight")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check-only", action="store_true", help="Validate plan only; no network and no writes.")
    group.add_argument("--execute-live-contract-check", action="store_true", help="Explicit bounded live checks for 2330, 0050, and TX.")
    args = parser.parse_args()
    if args.check_only:
        print(dump_json(build_report(mode="check_only")), end="")
        return 0
    live = execute_live_observation(bounded_watchlist(), write_latest=False)
    report = build_report(mode="execute_live_contract_check", live_result=live)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / "latest_summary.json"
    path.write_text(dump_json(report), encoding="utf-8", newline="\n")
    print(f"wrote={path.relative_to(REPO_ROOT).as_posix()}")
    print(dump_json(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
