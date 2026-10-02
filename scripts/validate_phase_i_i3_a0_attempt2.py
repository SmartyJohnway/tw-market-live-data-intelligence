"""Offline validator for the single-use A0 Attempt 2 record."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import run_phase_i_i3_a0_attempt2 as attempt2
from scripts import run_phase_i_i3_a0_preflight as p0

HISTORICAL = {
    p0.RECORD: p0.HISTORICAL_SHA,
    "docs/governance/phase_i/PHASE_I_I3_A0_CASH_INSTITUTIONAL_FLOW_PROBE_MAPPING_V1.json": p0.MAPPING_SHA,
    "docs/governance/phase_i/PHASE_I_I3_A0_P0_OFFLINE_PROBE_HARNESS_CLOSURE_2026-10-01.json": "8d58c1eb22941099f28e72e884c4686ddab1a66de752dfd343892e959fca118a",
    p0.ADJUDICATION_AUTHORITY_PATH.relative_to(p0.ROOT).as_posix(): p0.ADJUDICATION_AUTHORITY_SHA,
    "docs/governance/phase_i/PHASE_I_I3_A0_P1_TPEX_DEALER_SELL_ADJUDICATION_HARNESS_2026-10-01.json": "541b62d45d248d28e114d04628aac379dbd2f5b6d66d6ad07ae8cd4ee661a70c",
}
ERRATUM_REL = "docs/governance/phase_i/PHASE_I_I3_A0_ATTEMPT_2_PROVENANCE_ERRATUM_2026-10-02.json"
ATTEMPT_1_SHA = "43ef038ffd33a455ae52eff18a8f08e52436164b6d27d6140090b368810df5e0"
P0_RECORD_SHA = "8d58c1eb22941099f28e72e884c4686ddab1a66de752dfd343892e959fca118a"


def validate_provenance(root: Path = ROOT) -> None:
    """Validate observed historical latch bytes separately from corrected authority."""
    reservation = json.loads((root / attempt2.RESERVATION_REL).read_text(encoding="utf-8"))
    consumed = json.loads((root / attempt2.CONSUMED_REL).read_text(encoding="utf-8"))
    # These are deliberately the bytes actually recorded in 2026-10-02. Do not
    # rewrite history to make them look like the corrected P0 anchor.
    assert reservation.get("p0_record_sha256") == ATTEMPT_1_SHA
    assert consumed.get("p0_record_sha256") == ATTEMPT_1_SHA
    erratum = json.loads((root / ERRATUM_REL).read_text(encoding="utf-8"))
    assert erratum["schema_version"] == "phase_i_i3_a0_attempt_2_provenance_erratum.v1"
    assert erratum["historical_recorded_value"] == ATTEMPT_1_SHA
    assert erratum["correct_authority_value"] == P0_RECORD_SHA
    assert erratum["classification"] == "PROVENANCE_METADATA_DEFECT_ONLY"
    assert erratum["historical_files_mutated"] is False
    assert erratum["network_count_affected"] is False
    assert erratum["single_use_consumption_affected"] is False
    assert erratum["attempt_2_hold_decision_affected"] is False
    assert erratum["raw_persistence_finding_affected"] is False
    assert erratum["correct_immutable_authority_chain"] == {
        "attempt_1_record_sha256": ATTEMPT_1_SHA,
        "p0_mapping_sha256": "e3af3d8b5ce11fe88f0c32efa45400126fe1991ec0c0725fbc3f480e2888638c",
        "p0_record_sha256": P0_RECORD_SHA,
        "p1_authority_sha256": "666108fdd187f3ec753acc2a258e3ea7bd9415cc371346b5f32dc231ea665240",
        "p1_record_sha256": "541b62d45d248d28e114d04628aac379dbd2f5b6d66d6ad07ae8cd4ee661a70c",
    }


def assert_go_evidence(record: dict) -> None:
    counts = record["actual_network_counts"]
    assert counts["TWSE"] == counts["TPEx"] == 1
    assert counts["TAIFEX"] == counts["other_market_data"] == 0
    assert record["network_budget"] == {"TWSE_max_gets": 1, "TPEx_max_gets": 1, "total_max_gets": 2,
                                          "TAIFEX_gets": 0, "other_market_gets": 0, "retry_count": 0}
    assert record["analysis_status"] == "PASS"
    assert record["tpex_dealer_sell_adjudication"]["selection_status"] == "RESOLVED"
    adjudication = record["tpex_dealer_sell_adjudication"]
    assert adjudication["selected_candidate"] in p0.DEALER_SELL_CANDIDATES
    assert len([c for c, s in adjudication["candidate_statistics"].items()
                if s["rows_checked"] > 0 and s["rows_failed"] == 0 and s["missing_rows"] == 0]) == 1
    invariant = adjudication["institutional_total_invariant"]
    assert invariant["rows_checked"] > 0 and invariant["rows_failed"] == invariant["missing_rows"] == 0
    for market in ("TWSE", "TPEX"):
        telemetry = record["source_telemetry"][market]
        assert telemetry["http_status"] == 200 and telemetry["error_code"] is None
        assert telemetry["response_byte_count"] <= attempt2.MAX_BYTES
        assert re.fullmatch(r"[0-9a-f]{64}", telemetry["response_sha256"])
        payload = record["source_payload_metadata"][market]
        assert payload["row_count"] > 0 and payload["field_count"] > 0
        assert len(payload["normalized_official_dates"]) == 1
        source = record["whole_dataset_arithmetic"][market]
        for name, result in source.items():
            assert result["status"] in {"PASS", p0.NOT_APPLICABLE}, (market, name)
            assert result["rows_failed"] == 0, (market, name)
        observation = record["normalized_target_observations"][market]
        assert observation["unit"] == "share"
        assert observation["trade_date"] == payload["normalized_official_dates"][0]
        for group in p0.CORE:
            values = observation["common_core"][group]
            assert values["net_shares"] == values["buy_shares"] - values["sell_shares"]
        assert observation["common_core"]["institutional_total_net_shares"] == sum(
            observation["common_core"][group]["net_shares"] for group in p0.CORE)
    assert record["normalized_target_observations"]["TWSE"]["security_code"] == "1101"
    assert record["normalized_target_observations"]["TPEX"]["security_code"] == "5347"
    assert record["same_source_batching"]["per_target_network_request_required"] is False
    assert record["raw_persistence"]["result"] == "NONE"


def validate(record: dict | None = None, *, root: Path = ROOT, verify_runtime: bool = True) -> dict:
    if not __debug__:
        raise RuntimeError("optimized_governance_validation_not_supported")

    def deny(*args, **kwargs):
        raise AssertionError("Attempt 2 record validation must not use network")

    with patch("socket.socket.connect", deny), patch("socket.create_connection", deny):
        validate_provenance(root)
        value = record if record is not None else json.loads((root / attempt2.RESULT_REL).read_text(encoding="utf-8"))
        assert value["schema_version"] == "phase_i_i3_a0_attempt_2_source_timing_symmetry_reprobe.v1"
        assert value["owner_authority"] == attempt2.AUTHORITY
        assert value["baseline_main"] == attempt2.STARTING_MAIN
        assert (value["starting_branch"], value["starting_branch_head"], value["starting_tree"]) == (
            p0.BRANCH, attempt2.STARTING_HEAD, attempt2.STARTING_TREE)
        sm = value["security_master"]
        assert sm["release_id"] == "security-master-20260926T151841Z"
        assert sm["index_sha256"] == attempt2.SM_INDEX_SHA
        assert sm["qualification_sha256"] == attempt2.SM_QUALIFICATION_SHA
        assert sm["qualification_status"] == "PASS"
        assert set(sm["targets"]) == {"TWSE:1101", "TPEX:5347"}
        for target, item in sm["targets"].items():
            expected_market, expected_code = target.split(":", 1)
            assert item["canonical_target_id"] == target and item["market"] == expected_market
            assert item["security_code"] == expected_code
            assert item["instrument_family"] == "company_share" and item["instrument_type"] == "common_share"
            assert item["execution_eligibility"] == "allowed" and item["record_hash"]
        reservation = value["reservation"]
        assert reservation["reserved"] is True and reservation["consumed"] is True
        assert reservation["path"] == attempt2.RESERVATION_REL
        assert reservation["consumed_record_path"] == attempt2.CONSUMED_REL
        if root == ROOT:
            reserved = json.loads((root / attempt2.RESERVATION_REL).read_text(encoding="utf-8"))
            consumed = json.loads((root / attempt2.CONSUMED_REL).read_text(encoding="utf-8"))
            assert reserved["consumed"] is False and reserved["reserved"] is True
            assert consumed["consumed"] is True and consumed["consumed_before_first_http_attempt"] is True
            assert consumed["owner_authority"] == attempt2.AUTHORITY
        counts = value["actual_network_counts"]
        assert set(counts) == {"TWSE", "TPEx", "TAIFEX", "other_market_data"}
        assert 0 <= counts["TWSE"] <= 1 and 0 <= counts["TPEx"] <= 1
        assert counts["TAIFEX"] == counts["other_market_data"] == 0
        assert sum(counts.values()) <= 2
        budget = value["network_budget"]
        assert budget["retry_count"] == 0
        telemetry = value["source_telemetry"]
        assert set(telemetry) <= {"TWSE", "TPEX"}
        assert counts["TWSE"] == (1 if "TWSE" in telemetry else 0)
        assert counts["TPEx"] == (1 if "TPEX" in telemetry else 0)
        for market, source in telemetry.items():
            expected = attempt2.URLS[market]
            assert source["endpoint"] == expected and source["method"] == "GET"
            assert source["timeout_seconds"] == 30 and source["retry_count"] == 0
            assert source["redirect_policy"] == "reject"
            size = source["response_byte_count"]
            assert type(size) is int and 0 <= size <= attempt2.MAX_BYTES + 1
            digest = source["response_sha256"]
            if digest is not None:
                assert re.fullmatch(r"[0-9a-f]{64}", digest)
            if source["http_status"] == 200 and source["error_code"] is None:
                assert 0 < size <= attempt2.MAX_BYTES and digest is not None
                assert source["base_mime"] == "application/json"
        assert value["raw_persistence"] == {
            "result": "NONE", "raw_bodies_written": False, "temporary_raw_files_written": False,
            "source_payload_references_released_after_analysis": True,
        }
        assert value["A1_authorized"] is False and value["implementation_authorized"] is False
        assert value["production_activation_authorized"] is False and value["merge_authorized"] is False
        if value["final_decision"] == "GO_PASS":
            assert_go_evidence(value)
            assert value["accepted_pure_analyzer_status"] == "PASS"
        else:
            assert value["final_decision"] in {"HOLD", "NO_GO", "PRE_NETWORK_STOP"}
            # A conservative HOLD is always valid, but a recorded GO may not be
            # downgraded by inconsistent telemetry/evidence fields.
        for path, digest in HISTORICAL.items():
            if root == ROOT:
                assert hashlib.sha256((root / path).read_bytes()).hexdigest() == digest
        if verify_runtime:
            for path in p0.PROTECTED:
                current = (ROOT / path).read_bytes()
                baseline = subprocess.check_output(["git", "show", attempt2.STARTING_MAIN + ":" + path], cwd=ROOT)
                assert current == baseline, f"production_authority_changed:{path}"
            from server.unified_mcp.tool_contracts import build_tool_specs
            from scripts.m8r_06_03_production_adapter import build_production_runtime_adapter_registry
            assert len(build_tool_specs()) == 6
            registry = build_production_runtime_adapter_registry()
            assert len(registry.routes_for_executor("phase_i_i1_market_state_executor")) == 2
            assert len(registry.routes_for_executor("phase_i_i2_index_futures_context_executor")) == 1
            catalog = json.loads((ROOT / p0.PROTECTED[0]).read_text(encoding="utf-8"))
            assert all(item.get("capability_id") != "cash_institutional_flow_context"
                       for item in catalog["data_need_capabilities"])
    print(f"Attempt 2 record integrity PASS; decision={value['final_decision']}; market GETs <=2; network=0")
    return value


if __name__ == "__main__":
    validate()
