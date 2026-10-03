"""Offline integrity validator for the durable I3-A0 Attempt 3 outcome."""
from __future__ import annotations

import hashlib
import json
import socket
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import phase_i_i3_a0_attempt_authority as authority
from scripts.run_phase_i_i3_a0_attempt3 import (
    BASELINE, BRANCH, CONSUMED_REL, EXPECTED_HISTORICAL, EXPECTED_P2_SHA, OWNER_AUTHORITY, OUTCOME_REL,
    P2_REL, RESERVATION_REL, ROOT, STARTING_HEAD, STARTING_TREE,
)
from scripts.run_phase_i_i3_a0_preflight import ENDPOINTS, PROTECTED

MAX_BYTES = 4 * 1024 * 1024


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError("expected_object")
    return value


def validate_go_proofs(record: dict) -> None:
    """GO requires measured whole-dataset proofs, not just a decision label."""
    assert record["actual_get_counts"] == {"TWSE": 1, "TPEx": 1, "TAIFEX": 0, "other_market_data": 0}
    assert record["source_semantics_state"] == "EVALUATED"
    assert record["failure_stage"] is None
    adjudication = record["dealer_sell_adjudication"]
    candidates = {"Dealers-TotalSell", "Dealers -TotalSell"}
    assert adjudication["selection_status"] == "RESOLVED"
    assert set(adjudication["candidate_statistics"]) == candidates
    row_count = record["source_payload_summaries"]["TPEX"]["row_count"]
    qualifying = []
    for key, statistics in adjudication["candidate_statistics"].items():
        if (statistics["rows_checked"] == statistics["rows_passed"] == row_count > 0
                and statistics["rows_failed"] == statistics["missing_rows"] == 0):
            qualifying.append(key)
    assert qualifying == [adjudication["selected_candidate"]]
    independent = adjudication["institutional_total_invariant"]
    assert independent["rows_checked"] == independent["rows_passed"] == row_count > 0
    assert independent["rows_failed"] == independent["missing_rows"] == 0
    assert record["institutional_total_invariant"] == independent
    assert record["target_binding"] == {"TWSE:1101": 1, "TPEX:5347": 1}
    for market, source_key, target, code in (("TWSE", "TWSE", "TWSE:1101", "1101"),
                                            ("TPEx", "TPEX", "TPEX:5347", "5347")):
        source = record["source_telemetry"][source_key]
        assert source["http_status"] == 200 and source["error_code"] is None
        assert source["base_mime"] == "application/json"
        assert 0 < source["response_byte_count"] <= MAX_BYTES
        observation = record["normalized_observations"][target]
        assert observation["market"] == source_key and observation["security_code"] == code
        assert observation["unit"] == record["unit_proof"][market] == "share"
        summary = record["source_payload_summaries"][source_key]
        assert 0 < summary["row_count"] <= 5000
        expected_dates = ["2026-09-30"] if market == "TWSE" else summary["normalized_trade_dates"]
        assert len(expected_dates) == 1 and observation["trade_date"] == expected_dates[0]
        arithmetic = record["whole_dataset_arithmetic"][market]
        for group in ("foreign_and_mainland_excluding_foreign_dealer", "investment_trust",
                      "dealer_total", "institutional_total_net"):
            check = arithmetic[group]
            assert check["status"] == "PASS"
            assert check["rows_checked"] == check["rows_passed"] == summary["row_count"]
            assert check["rows_failed"] == check["missing_field_rows"] == 0
        split = arithmetic["dealer_component_net"]
        if market == "TWSE":
            assert split["status"] == "PASS"
            assert split["rows_checked"] == split["rows_passed"] == summary["row_count"]
            assert split["rows_failed"] == split["missing_field_rows"] == 0
        else:
            assert split["status"] == "NOT_APPLICABLE_SOURCE_DOES_NOT_EXPOSE_COMPONENT_SPLIT"
    assert record["symmetry_matrix"]["unit_symmetry"] == "PASS"
    assert record["symmetry_matrix"]["participant_semantic_symmetry"] == "PASS"
    assert record["symmetry_matrix"]["publication_timing_symmetry"] == "asymmetric_but_representable"


def validate() -> dict:
    def deny(*args, **kwargs):
        raise AssertionError("Attempt 3 validation must not use network")

    with patch("socket.socket.connect", deny), patch("socket.create_connection", deny):
        chain = authority.load_reviewed_authority_chain()
        record = _json(ROOT / OUTCOME_REL)
        reservation_path = ROOT / RESERVATION_REL
        consumed_path = ROOT / CONSUMED_REL
        reservation, consumed = _json(reservation_path), _json(consumed_path)
        authority.validate_reservation(reservation, chain)
        authority.validate_consumed_latch(consumed, chain)

        assert record["schema_version"] == "phase_i_i3_a0_attempt_3_source_timing_symmetry_reprobe.v1"
        assert record["owner_authority"] == OWNER_AUTHORITY
        assert record["baseline_main"] == BASELINE
        assert record["starting_branch_head"] == STARTING_HEAD
        assert record["starting_tree"] == STARTING_TREE
        assert record["authority_chain_sha256"] == digest(authority.AUTHORITY_PATH)
        assert reservation["authority_chain_sha256"] == record["authority_chain_sha256"]
        assert reservation["p2_record_sha256"] == EXPECTED_P2_SHA
        assert reservation["owner_authority"] == consumed["owner_authority"] == OWNER_AUTHORITY
        assert reservation["starting_main"] == consumed["starting_main"] == BASELINE
        assert reservation["starting_branch_head"] == consumed["starting_branch_head"] == STARTING_HEAD
        assert reservation["starting_tree"] == consumed["starting_tree"] == STARTING_TREE
        assert reservation["starting_branch"] == consumed["starting_branch"] == BRANCH
        assert reservation["network_budget"] == consumed["network_budget"] == {"TWSE": 1, "TPEx": 1, "retry": 0}
        assert reservation["attempt_number"] == 3
        assert reservation["reserved"] is True and reservation["consumed"] is False
        assert consumed["consumed"] is True and consumed["consumed_before_first_http_attempt"] is True
        for key in authority.ANCHOR_FIELDS:
            assert reservation[key] == consumed[key] == chain[key]
        assert record["reservation"] == {"path": RESERVATION_REL, "sha256": digest(reservation_path)}
        assert record["consumed_latch"] == {"path": CONSUMED_REL, "sha256": digest(consumed_path)}
        assert reservation["targets"] == record["targets"]
        for market, code in (("TWSE", "1101"), ("TPEX", "5347")):
            target = record["targets"][market]
            assert target["canonical_target_id"] == f"{market}:{code}"
            assert target["market"] == market and target["security_code"] == code
            assert target["instrument_family"] == "company_share"
            assert target["instrument_type"] == "common_share"
            assert target["execution_eligibility"] == "allowed"
            assert target["resolution_reason"] == "exact_listing_id"

        counts = record["actual_get_counts"]
        assert set(counts) == {"TWSE", "TPEx", "TAIFEX", "other_market_data"}
        assert counts["TWSE"] in (0, 1) and counts["TPEx"] in (0, 1)
        assert counts["TAIFEX"] == counts["other_market_data"] == 0
        assert sum(counts.values()) <= 2
        budget = record["network_budget"]
        assert budget == {"TWSE_max_get": 1, "TPEx_max_get": 1, "total_max_get": 2, "retry_count": 0}
        telemetry = record["source_telemetry"]
        assert set(telemetry) <= {"TWSE", "TPEX"}
        assert counts["TWSE"] == sum(bool(v.get("request_dispatched")) for k, v in telemetry.items() if k == "TWSE")
        assert counts["TPEx"] == sum(bool(v.get("request_dispatched")) for k, v in telemetry.items() if k == "TPEX")
        assert counts["TPEx"] == 0 or counts["TWSE"] == 1
        for source_key, source in telemetry.items():
            market = source_key
            endpoint = "TWSE" if market == "TWSE" else "TPEX"
            expected_policy = "compatibility" if market == "TWSE" else "strict"
            assert source["endpoint"] == ENDPOINTS[endpoint]
            assert source["method"] == "GET" and source["timeout_seconds"] == 30
            assert source["retry_count"] == 0 and source["redirect_policy"] == "reject"
            assert source["ssl_policy"] == expected_policy
            assert type(source["request_dispatched"]) is bool
            count = source["response_byte_count"]
            assert type(count) is int and 0 <= count <= MAX_BYTES + 1
            response_hash = source["response_sha256"]
            assert response_hash is None or (len(response_hash) == 64 and all(ch in "0123456789abcdef" for ch in response_hash))
            if source["http_status"] == 200 and source["error_code"] is None:
                assert 0 < count <= MAX_BYTES and response_hash is not None
                assert source["base_mime"] == "application/json"
            if source["http_status"] is None or source["error_code"] == "URLError":
                assert source["error_code"] and source["reason_classification"] in {
                    "ssl_certificate_verification_failed", "dns_resolution_failed", "connection_refused",
                    "connection_reset", "timeout", "os_network_error", "tls_error", "unknown_transport_error",
                }
                if source.get("verify_message") is not None:
                    assert len(source["verify_message"]) <= 256

        assert record["raw_persistence"] == {
            "result": "NONE", "raw_bodies_written": False,
            "temporary_raw_files_written": False,
            "raw_payload_references_released_after_analysis": True,
        }
        assert record["A1_authorized"] is False
        assert record["implementation_authorized"] is False
        assert record["production_activation_authorized"] is False
        assert record["merge_authorized"] is False
        assert record["symmetry_matrix"]["transport_symmetry"] == "not_required_different_governed_tls_policies"
        assert record["batching"]["per_target_network_request_required"] is False

        if record["final_decision"] == "GO_PASS":
            validate_go_proofs(record)
        else:
            assert record["final_decision"] in {"HOLD", "NO_GO", "PRE_NETWORK_STOP"}
            if record["source_semantics_state"] == "SOURCE_SEMANTICS_NOT_EVALUATED":
                assert record["dealer_sell_adjudication"] == {}
            if record["failure_stage"] == "TWSE_TRANSPORT_FAILED":
                assert counts["TWSE"] == 1 and counts["TPEx"] == 0
                assert "TPEX" not in telemetry
            if record["failure_stage"] == "TPEX_TRANSPORT_FAILED":
                assert counts["TWSE"] == counts["TPEx"] == 1
                assert telemetry["TPEX"]["error_code"] is not None
                assert record["normalized_observations"]["TPEX:5347"] is None
                assert "TPEX" not in record["source_payload_summaries"]

        # Historical evidence is compared both to its digest and to the accepted
        # starting Git bytes. The P2 error is metadata only; none is rewritten.
        for rel, expected in EXPECTED_HISTORICAL.items():
            assert digest(ROOT / rel) == expected
        assert digest(ROOT / P2_REL) == EXPECTED_P2_SHA
        for rel in ("docs/governance/phase_i/acceptance_runs/i3-a0-attempt2-authority-reservation.json",
                    "docs/governance/phase_i/acceptance_runs/i3-a0-attempt2-authority-consumed.json"):
            assert (ROOT / rel).read_bytes() == subprocess.check_output(["git", "show", STARTING_HEAD + ":" + rel], cwd=ROOT)
        for rel, expected in authority.HASHED_PATHS.items():
            path = ROOT / expected
            assert digest(path) == chain[rel]

        for relative in PROTECTED:
            current = (ROOT / relative).read_bytes()
            baseline = subprocess.check_output(["git", "show", BASELINE + ":" + relative], cwd=ROOT)
            assert current == baseline, f"production_authority_changed:{relative}"
        from scripts.m8r_06_03_production_adapter import build_production_runtime_adapter_registry
        from server.unified_mcp.tool_contracts import build_tool_specs
        registry = build_production_runtime_adapter_registry()
        assert len(build_tool_specs()) == 6
        assert len(registry.routes_for_executor("phase_i_i1_market_state_executor")) == 2
        assert len(registry.routes_for_executor("phase_i_i2_index_futures_context_executor")) == 1
        catalog = _json(ROOT / PROTECTED[0])
        assert all(item.get("capability_id") != "cash_institutional_flow_context" for item in catalog["data_need_capabilities"])

    print(f"Attempt 3 evidence validation PASS; decision={record['final_decision']}; market calls={sum(counts.values())}; network=0")
    return record


if __name__ == "__main__":
    validate()
