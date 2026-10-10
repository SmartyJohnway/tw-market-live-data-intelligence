#!/usr/bin/env python3
"""Network-free verifier for A6 H2 activation and bounded session evidence."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BASE = "8a56fcd3204fa852a7444363485bfc8af264e74c"
MAIN = "6daf6e2dcc6fd34e00e7e3831c25e98bb4d2399a"
H2 = "phase_h_h2_twse_exright_pre_executor"
H3 = "phase_h_h3_twse_recent_performance_executor"
ALLOWED_SOURCES = {
    "H3-TWSE-DEFAULT-BOUNDED": ("H3", "www.twse.com.tw", "/exchangeReport/STOCK_DAY"),
    "H2-TWSE-EXRIGHT-PRE-OPENAPI": ("H2", "openapi.twse.com.tw", "/v1/exchangeReport/TWT48U_ALL"),
}


def validate_transport_events(events: list[dict], *, expected_dispatches: int | None = None) -> dict:
    """Validate reservation/completion pairs, including frozen legacy completions.

    Historical completions may omit ``method``; their paired reservation is the
    only permitted source for that value. New completion events must preserve it.
    """
    reservations: dict[str, dict] = {}
    completions: dict[str, dict] = {}
    for event in events:
        kind = event.get("event")
        reservation_id = event.get("reservation_id")
        if not isinstance(reservation_id, str) or not reservation_id:
            raise AssertionError("transport_event_missing_reservation_id")
        destination = reservations if kind == "reserved" else completions if kind == "completed" else None
        if destination is None:
            raise AssertionError("transport_event_kind_invalid")
        if reservation_id in destination:
            raise AssertionError("transport_event_duplicate")
        destination[reservation_id] = event

    if set(reservations) != set(completions):
        raise AssertionError("transport_reservation_completion_pair_mismatch")
    if expected_dispatches is not None and len(reservations) != expected_dispatches:
        raise AssertionError("transport_dispatch_count_mismatch")

    dispatch_numbers: set[int] = set()
    for reservation_id, reserved in reservations.items():
        completed = completions[reservation_id]
        required = ("attempt", "operation", "source_id", "target", "operation_id",
                    "dispatch_number", "url", "redirects", "retry_count", "timestamp")
        if any(key not in reserved for key in required):
            raise AssertionError("transport_reservation_schema_invalid")
        if any(key not in completed for key in required if key != "timestamp"):
            raise AssertionError("transport_completion_schema_invalid")
        source_id = reserved["source_id"]
        contract = ALLOWED_SOURCES.get(source_id)
        if contract is None:
            raise AssertionError("transport_source_not_allowed")
        operation, host, path = contract
        if reserved.get("method") != "GET" or completed.get("method", reserved["method"]) != reserved["method"]:
            raise AssertionError("transport_method_pair_mismatch")
        if (reserved["operation"] != operation or completed["operation"] != operation
                or reserved["target"] != "TWSE:2330" or completed["target"] != "TWSE:2330"):
            raise AssertionError("transport_operation_or_target_mismatch")
        if reserved["attempt"] not in (1, 2) or completed["attempt"] != reserved["attempt"]:
            raise AssertionError("transport_attempt_mismatch")
        for key in ("source_id", "operation_id", "dispatch_number", "url"):
            if completed.get(key) != reserved.get(key):
                raise AssertionError(f"transport_pair_mismatch:{key}")
        parsed = urlsplit(reserved["url"])
        if parsed.scheme != "https" or parsed.hostname != host or parsed.path != path:
            raise AssertionError("transport_url_not_allowed")
        number = reserved["dispatch_number"]
        if not isinstance(number, int) or number < 1 or number in dispatch_numbers:
            raise AssertionError("transport_dispatch_number_invalid")
        dispatch_numbers.add(number)
        for event in (reserved, completed):
            if (event.get("redirects") != 0 or event.get("retry_count") != 0
                    or event.get("retries", 0) != 0):
                raise AssertionError("transport_retry_or_redirect_forbidden")
    if dispatch_numbers != set(range(1, len(dispatch_numbers) + 1)):
        raise AssertionError("transport_dispatch_numbers_not_contiguous")
    if len(reservations) > 8 or len(reservations) > 10:
        raise AssertionError("transport_session_budget_exceeded")
    per_attempt: dict[int, dict[str, int]] = {}
    for item in reservations.values():
        counts = per_attempt.setdefault(item["attempt"], {"total": 0, "H3": 0, "H2": 0})
        counts["total"] += 1
        counts[item["operation"]] += 1
    if any(v["total"] > 4 or v["H3"] > 3 or v["H2"] > 1 for v in per_attempt.values()):
        raise AssertionError("transport_attempt_budget_exceeded")
    return {"reservations": len(reservations), "completions": len(completions),
            "legacy_completions_without_method": sum("method" not in x for x in completions.values())}


def strict(path: Path):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise AssertionError(f"duplicate_json_key:{key}")
            out[key] = value
        return out
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs)


def validate() -> dict:
    catalog = strict(ROOT / "docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json")
    routing = strict(ROOT / "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json")
    inventory = strict(ROOT / "docs/data_capabilities/m8r_05b_existing_orchestrator_disposition.json")
    registry = strict(ROOT / "config/m8r_06_03_executor_registry_metadata.json")
    capability = next(x for x in catalog["data_need_capabilities"] if x["capability_id"] == "corporate_action_context")
    route = next(x for x in routing["routes"] if x["capability_id"] == "corporate_action_context")
    assert capability["runtime_executable"] is True
    assert capability["phase_h_activation_state"] == "selected_route_active"
    assert capability["supported_markets"] == ["TWSE"]
    assert (route["runtime_executable"], route["routing_status"], route["selected_executor_id"], route["candidate_executor_ids"], route["supported_markets"]) == (True, "resolved", H2, [H2], ["TWSE"])
    assert route["network_required"] is True and route["output_evidence_contract"] == "corporate_action_context_evidence.v1"
    assert route["supported_instrument_families"] == ["company_share"]
    assert route["supported_instrument_types"] == ["common_share"]
    assert "one TWT48U_ALL GET maximum" in route["estimated_operation_rule"]
    h2_records = [x for x in routing["phase_h_source_authority"]["records"] if x["source_id"].startswith("H2-")]
    active_h2 = [x for x in h2_records if x["activation_state"] == "active" and x["runtime_executable"] is True]
    assert [(x["source_id"], x["source_contract"]) for x in active_h2] == [("H2-TWSE-EXRIGHT-PRE-OPENAPI", "TWT48U_ALL")]
    assert all(x["activation_state"] != "active" and x["runtime_executable"] is False for x in h2_records if x not in active_h2)
    assert catalog["phase_h_contract"]["active_phase_h_source_count"] == routing["phase_h_source_authority"]["active_source_count"] == 5
    assert next(x for x in routing["routes"] if x["capability_id"] == "recent_performance")["selected_executor_id"] == H3
    h2_inventory = next(x for x in inventory["surfaces"] if x["surface_id"] == H2)
    assert h2_inventory["reusable_for_05b"] is True
    assert "one official TWSE TWT48U_ALL GET maximum" in h2_inventory["network_behavior"]
    registration = [x for x in registry["executors"] if x["executor_id"] == H2]
    assert len(registration) == 1 and registration[0]["market"] == "TWSE"
    assert registration[0]["expected_evidence_contract"] == "corporate_action_context_evidence.v1"
    assert registration[0]["timeout_seconds"] == 15 and registration[0]["maximum_result_items"] == 1
    from server.unified_mcp.tool_contracts import build_tool_specs
    assert len(build_tool_specs()) == 6

    from scripts.phase_j_b04_a6_integrated_acceptance import run_preflight
    preflight = run_preflight()
    assert preflight["disposition"] == "J_B04_A6_READY_FOR_BOUNDED_LIVE_ACCEPTANCE"
    assert preflight["authorized_release_verified"] is True
    assert preflight["production_identity_verified"] is True
    assert preflight["identity_resolution"]["resolution_reason"] == "exact_listing_id"
    assert preflight["identity_resolution"]["target_binding"] == {
        "canonical_target_id": "TWSE:2330", "market": "TWSE", "security_code": "2330",
        "isin": "TW0002330008", "instrument_family": "company_share", "instrument_type": "common_share",
        "execution_eligibility": "allowed",
    }
    assert preflight["network_counts"] == {"market_GET": 0, "market_HEAD": 0, "market_POST": 0, "Security_Master_live_acquisition": 0}
    assert subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=ROOT, text=True).strip() == MAIN

    session_root = Path(os.environ.get("A6_SESSION_ROOT", "/tmp/j-b04-a6"))
    session_path = session_root / "session.json"
    if session_path.is_file():
        session = strict(session_path)
        assert session["actual_dispatches"] <= 8 and session["actual_dispatches"] <= 10
        assert session.get("network_enabled") is False
        ledger_path = session_root / "transport-ledger.jsonl"
        events = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines()] if ledger_path.exists() else []
        validate_transport_events(events, expected_dispatches=session["actual_dispatches"])
        assert session.get("network_enabled") is False
        assert hashlib.sha256((session_root / "acceptance-result.json").read_bytes()).hexdigest() == session["terminal_output_sha256"]
    return {"status": "PASS", "H2_executor": H2, "H3_executor": H3,
            "authorized_release_verified": True, "production_identity_verified": True,
            "market_network_before_live": 0, "MCP": 6}


def main() -> int:
    print(json.dumps(validate(), sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
