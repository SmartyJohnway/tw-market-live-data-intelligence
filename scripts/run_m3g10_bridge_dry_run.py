"""M3G-10 controlled source refresh bridge dry-run utilities.

This module verifies the refresh bridge in memory only:
controlled probe evidence -> adapter -> latest snapshot -> observations ->
AI context pack -> ChatGPT briefing.

It intentionally does not execute live probes and does not write production
artifacts under research/generated/ or frontend/public/.
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from typing import Any, Dict

from scripts.generate_ai_context_pack import build_ai_context_pack
from scripts.generate_chatgpt_briefing import render_chatgpt_briefing, validate_context_pack
from scripts.generate_latest_market_snapshot import build_snapshot, validate_snapshot_contract
from scripts.generate_watchlist_observations import build_watchlist_observations
from scripts.m3g_live_probe_to_snapshot_adapter import build_adapter_report

PRODUCTION_WRITE_PATHS = ["research/generated/", "frontend/public/"]


def load_targets_config(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _symbol_semantics(snapshot: dict) -> Dict[str, Dict[str, Any]]:
    return {
        sym.get("symbol", "unknown"): {
            "source_used": sym.get("source_used"),
            "source_candidates": sym.get("source_candidates", []),
            "price_semantics": sym.get("price_semantics"),
            "freshness_status": sym.get("freshness_status"),
            "delay_status": sym.get("delay_status"),
            "source_authority": sym.get("source_authority"),
            "caveats": sym.get("caveats", []),
        }
        for sym in snapshot.get("symbols", [])
    }


def _semantic_checks(adapter_report: dict, snapshot: dict) -> dict:
    symbol_semantics = _symbol_semantics(snapshot)
    all_symbols = list(symbol_semantics.values())

    price_semantics = {item.get("price_semantics") for item in all_symbols}
    source_authorities = {item.get("source_authority") for item in all_symbols}

    blocked_sources = set(adapter_report.get("sources_blocked", []))
    mapped_sources = set(adapter_report.get("sources_mapped", []))

    official_ok = all(
        item.get("price_semantics") == "eod_reference"
        for item in all_symbols
        if item.get("source_used") in ["TWSE_OpenAPI", "TPEx_OpenAPI"]
    )
    twse_mis_ok = all(
        item.get("source_authority") == "unofficial_frontend" and "unofficial_source_risk" in item.get("caveats", [])
        for item in all_symbols
        if item.get("source_used") == "TWSE_MIS"
    )
    yahoo_ok = all(
        item.get("source_authority") == "third_party" and "third_party_coverage_caveats" in item.get("caveats", [])
        for item in all_symbols
        if item.get("source_used") == "Yahoo_Finance"
    )

    return {
        "identity_mismatch_blocked": "Yahoo_Finance" not in mapped_sources if "Yahoo_Finance" in blocked_sources else True,
        "failed_targets_preserved": bool(adapter_report.get("failed_targets")),
        "unsupported_targets_preserved": bool(adapter_report.get("unsupported_targets")),
        "delayed_quote_or_stale_preserved": bool(price_semantics.intersection({"delayed_quote", "stale_quote"})) or not all_symbols,
        "eod_reference_preserved": "eod_reference" in price_semantics or not mapped_sources.intersection({"TWSE_OpenAPI", "TPEx_OpenAPI"}),
        "official_openapi_eod_only": official_ok,
        "twse_mis_caveats_preserved": twse_mis_ok,
        "yahoo_caveats_preserved": yahoo_ok,
        "source_authorities_seen": sorted(str(v) for v in source_authorities if v),
        "symbol_semantics": symbol_semantics,
    }


def build_m3g10_dry_run_report(summary_path: str | Path, targets_config: dict) -> dict:
    """Build a no-write M3G-10 dry-run report entirely in memory."""
    adapter_report = build_adapter_report(summary_path)
    mock_inputs = adapter_report.get("mock_inputs_preview", {})

    snapshot = build_snapshot(targets_config, mock_inputs=mock_inputs)
    validate_snapshot_contract(snapshot)

    observations = build_watchlist_observations(snapshot)
    context_pack = build_ai_context_pack(snapshot, observations)
    validate_context_pack(context_pack)

    briefing = render_chatgpt_briefing(context_pack)

    dry_run_status = "pass"
    if adapter_report.get("adapter_status") in {"malformed_input", "blocked_no_valid_inputs", "identity_mismatch_blocked"}:
        dry_run_status = "blocked"
    elif adapter_report.get("adapter_status") == "partial_mapping" or snapshot.get("failed_symbols"):
        dry_run_status = "partial"

    return {
        "milestone": "M3G-10-CONTROLLED-SOURCE-REFRESH-BRIDGE-DRY-RUN-NO-WRITE",
        "dry_run_status": dry_run_status,
        "summary_path": str(summary_path),
        "network_calls_executed": False,
        "production_writes_executed": False,
        "frontend_writes_executed": False,
        "prohibited_write_paths": PRODUCTION_WRITE_PATHS,
        "adapter_status": adapter_report.get("adapter_status"),
        "sources_seen": adapter_report.get("sources_seen", []),
        "sources_mapped": adapter_report.get("sources_mapped", []),
        "sources_blocked": adapter_report.get("sources_blocked", []),
        "targets_mapped": adapter_report.get("targets_mapped", []),
        "failed_targets": adapter_report.get("failed_targets", {}),
        "unsupported_targets": adapter_report.get("unsupported_targets", {}),
        "adapter_warnings": adapter_report.get("warnings", []),
        "adapter_errors": adapter_report.get("errors", []),
        "artifact_status": {
            "latest_market_snapshot": "built_in_memory",
            "watchlist_observations": "built_in_memory",
            "ai_context_pack": "built_in_memory",
            "chatgpt_briefing": "rendered_in_memory",
        },
        "artifact_metrics": {
            "snapshot_symbols": len(snapshot.get("symbols", [])),
            "snapshot_failed_symbols": len(snapshot.get("failed_symbols", [])),
            "observations": len(observations.get("observations", [])),
            "failed_observations": len(observations.get("failed_observations", [])),
            "briefing_characters": len(briefing),
        },
        "semantic_checks": _semantic_checks(adapter_report, snapshot),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an in-memory M3G-10 bridge dry-run from existing evidence.")
    parser.add_argument("summary_path", help="Path to a controlled live probe run summary or fixture summary.")
    parser.add_argument("--targets-config", default="config/market_targets.json", help="Target config JSON path.")
    args = parser.parse_args()

    targets_config = load_targets_config(args.targets_config)
    report = build_m3g10_dry_run_report(args.summary_path, targets_config)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
