"""Owner-authorized H-SB1-A0 bounded-live source proof for TPEx H2.

This runner is deliberately NOT a production H2 executor.

It performs exactly two fixed official TPEx OpenAPI requests for one exact
target, normalizes only that target through the already accepted H-IMP-3
normalizers, and persists only a compact target-bounded acceptance report.

It does NOT:
- assemble corporate_action_context_evidence.v1;
- invent or bind an H2 requested_window;
- change Catalog / Routing / source activation;
- retain raw full-market payloads;
- retry, poll, schedule, or accumulate history.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any

import scripts.m8r_06_03_production_adapter as production
from server.services.phase_h_corporate_action_adapters import (
    normalize_tpex_exright_daily,
    normalize_tpex_exright_prepost,
)


TARGET = {
    "canonical_target_id": "TPEX:6488",
    "market": "TPEX",
    "security_code": "6488",
}
PRE_SOURCE_ID = "H2-TPEX-EXRIGHT-PRE-OPENAPI"
FINAL_SOURCE_ID = "H2-TPEX-EXRIGHT-FINAL-OPENAPI"
PRE_URL = "https://www.tpex.org.tw/openapi/v1/tpex_exright_prepost"
FINAL_URL = "https://www.tpex.org.tw/openapi/v1/tpex_exright_daily"
OWNER_AUTHORIZATION_REFERENCE = "OWNER_CHAT_2026-09-23_H_SB1_H2_SOURCE_LIVE"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _decode_rows(payload: bytes, source_id: str) -> list[dict[str, Any]]:
    try:
        value = json.loads(payload.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{source_id}:invalid_json_payload") from exc
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise RuntimeError(f"{source_id}:unexpected_payload_shape")
    return value


def _summary(source_id: str, fragment: dict[str, Any]) -> dict[str, Any]:
    source = fragment["source"]
    events = fragment.get("events", [])
    return {
        "source_id": source_id,
        "source_family": source["source_family"],
        "source_contract_id": source["source_contract_id"],
        "source_role": source["source_role"],
        "activation_state": source["activation_state"],
        "license_authority": source["license_authority"],
        "status": fragment["status"],
        "covered_event_subtypes": sorted(fragment.get("covered", [])),
        "matched_event_count": len(events),
        "events": events,
        "caveats": sorted(fragment.get("caveats", [])),
        "citation_ids": sorted(fragment.get("citation_ids", [])),
    }


def run(output_dir: Path) -> dict[str, Any]:
    if os.environ.get("H_SB1_H2_OWNER_AUTHORIZED") != "YES":
        raise RuntimeError("owner_authorization_environment_missing")

    output_dir.mkdir(parents=True, exist_ok=True)
    observed_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

    calls: list[dict[str, Any]] = []

    def fetch_once(url: str, *, timeout: int = 15) -> bytes:
        if len(calls) >= 2:
            raise RuntimeError("bounded_live_call_limit_exceeded")
        if url not in {PRE_URL, FINAL_URL}:
            raise RuntimeError("unexpected_live_endpoint")
        if any(item["url"] == url for item in calls):
            raise RuntimeError("duplicate_live_endpoint_call")
        calls.append({"url": url, "timeout_seconds": timeout})
        return production._fetch_official_payload(url, timeout=timeout)

    pre_rows = _decode_rows(fetch_once(PRE_URL), PRE_SOURCE_ID)
    final_rows = _decode_rows(fetch_once(FINAL_URL), FINAL_SOURCE_ID)

    pre = normalize_tpex_exright_prepost(
        pre_rows,
        TARGET,
        observed_at=observed_at,
        citation_id="live-h2-tpex-pre",
    )
    final = normalize_tpex_exright_daily(
        final_rows,
        TARGET,
        observed_at=observed_at,
        citation_id="live-h2-tpex-final",
    )

    if len(calls) != 2:
        raise RuntimeError(f"unexpected_live_call_count:{len(calls)}")
    if {item["url"] for item in calls} != {PRE_URL, FINAL_URL}:
        raise RuntimeError("live_endpoint_set_mismatch")

    accepted_statuses = {"available", "no_evidence_in_covered_scope"}
    if pre["status"] not in accepted_statuses or final["status"] not in accepted_statuses:
        raise RuntimeError("live_source_normalization_not_accepted")

    summaries = [
        _summary(PRE_SOURCE_ID, pre),
        _summary(FINAL_SOURCE_ID, final),
    ]
    for item in summaries:
        if item["activation_state"] != "eligible":
            raise RuntimeError("source_must_remain_eligible_not_active")

    report = {
        "schema_version": "phase_h_h_sb1_a0_h2_source_live_acceptance.v1",
        "status": "PASS",
        "tranche": "H-SB1-A0",
        "capability_id": "corporate_action_context",
        "target": dict(TARGET),
        "owner_authorization_reference": OWNER_AUTHORIZATION_REFERENCE,
        "observed_at": observed_at,
        "network": {
            "authorized": True,
            "call_bound": 2,
            "actual_call_count": len(calls),
            "calls": calls,
            "retry_count": 0,
            "polling": False,
            "scheduler": False,
            "background_collection": False,
            "raw_full_market_payload_persisted": False,
        },
        "source_results": summaries,
        "production_claims": {
            "corporate_action_context_materialized": False,
            "requested_window_bound": False,
            "production_executor_registered": False,
            "route_activation_effective": False,
            "catalog_or_routing_changed": False,
            "h3_implementation_started": False,
        },
        "notes": [
            "This is source-contract evidence only, not production H2 evidence.",
            "No H2 requested_window is invented; production window binding remains governed by H-SB1A.",
            "No-row is valid only for the exact source slice and never proves complete corporate-action absence.",
        ],
    }

    report_path = output_dir / "H_SB1_A0_H2_SOURCE_LIVE_REPORT.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report["report_sha256"] = _sha256(report_path)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm-bounded-live", action="store_true")
    parser.add_argument("--output-dir")
    args = parser.parse_args()

    if not args.confirm_bounded_live:
        raise SystemExit("H-SB1-A0 requires --confirm-bounded-live")

    output = (
        Path(args.output_dir)
        if args.output_dir
        else Path(tempfile.mkdtemp(prefix="h-sb1-a0-h2-"))
    )
    report = run(output)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
