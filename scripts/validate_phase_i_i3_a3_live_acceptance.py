"""Offline validation of sealed I3-A3 pre-network and single-use live evidence."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import run_phase_i_i3_a3_bounded_live_acceptance as a3
from scripts import validate_phase_i_i3_a2_r1 as r1
from server.services.phase_i_i3_cash_institutional_flow_adapters import validate_evidence


def require(condition: bool, code: str) -> None:
    if not condition:
        raise ValueError(code)


def read_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def validate(*, pre_network_only: bool = False) -> dict | None:
    def deny(*args, **kwargs):
        raise AssertionError("a3_validator_external_network_forbidden")
    with patch("socket.socket.connect", deny), patch("socket.create_connection", deny):
        r1.validate()
        a3.immutable_hashes()
        a3.production_containment()
        closure = read_json(a3.PRE_NETWORK)
        require(closure["schema_version"] == "phase_i_i3_a3_pre_network_runner_closure.v1"
                and closure["status"] == "PASS_READY_TO_CONSUME_OWNER_AUTHORITY"
                and closure["owner_authority"] == a3.OWNER
                and closure["starting_main"] == a3.BASELINE
                and closure["starting_head"] == a3.START_HEAD
                and closure["starting_tree"] == a3.START_TREE
                and closure["immutable_hashes"] == a3.HASHES
                and closure["candidate_file_hashes"] == a3.candidate_hashes()
                and closure["source_transport_sha256"] == a3.sha(ROOT / "scripts/phase_i_i3_a0_source_transport.py")
                and closure["runner_sha256"] == a3.sha(ROOT / "scripts/run_phase_i_i3_a3_bounded_live_acceptance.py")
                and closure["validator_sha256"] == a3.sha(ROOT / "scripts/validate_phase_i_i3_a3_live_acceptance.py")
                and closure["twse_governed_source_date"] == "20260930"
                and closure["actual_market_gets"] == 0
                and closure["live_authority_consumed"] is False, "pre_network_closure_invalid")
        require(closure["fake_run"]["A3_decision"] == "PASS"
                and closure["fake_run"]["TWSE_status"] == "complete"
                and closure["fake_run"]["TPEX_status"] == "complete"
                and closure["fake_run"]["candidate_network_calls"] == 0
                and closure["fake_run"]["raw_payload_persistence"] == "NONE", "fake_runner_closure_invalid")
        if pre_network_only:
            require(not any((ROOT / rel).exists() for rel in (a3.RESERVATION, a3.CONSUMED, a3.OUTCOME, a3.ATTEMPT)),
                    "pre_network_live_artifact_exists")
            print("I3-A3 pre-network runner PASS; live authority unconsumed; market GETs=0")
            return None
        require((ROOT / a3.RESERVATION).exists() and (ROOT / a3.CONSUMED).exists(),
                "single_use_latch_missing")
        reservation = read_json(a3.RESERVATION)
        consumed = read_json(a3.CONSUMED)
        require(reservation["owner_authority"] == a3.OWNER and reservation["gate"] == "I3-A3"
                and reservation["starting_main"] == a3.BASELINE
                and reservation["immutable_hashes"] == a3.HASHES
                and reservation["candidate_file_hashes"] == a3.candidate_hashes()
                and reservation["network_budget"] == {"TWSE": 1, "TPEX": 1, "TAIFEX": 0, "other": 0, "retry": 0}
                and reservation["reserved"] is True and reservation["consumed"] is False,
                "reservation_invalid")
        commit = reservation["pre_network_commit"]
        tree = reservation["pre_network_tree"]
        require(subprocess.check_output(["git", "show", "-s", "--format=%T", commit], cwd=ROOT, text=True).strip() == tree
                and subprocess.check_output(["git", "show", f"{commit}:{a3.PRE_NETWORK}"], cwd=ROOT) == (ROOT / a3.PRE_NETWORK).read_bytes(),
                "pre_network_commit_or_tree_invalid")
        require(consumed == {"schema_version": "phase_i_i3_a3_live_authority_consumed.v1",
                "owner_authority": a3.OWNER, "reservation_sha256": a3.sha(ROOT / a3.RESERVATION),
                "consumed": True, "consumed_before_first_http_attempt": True}, "consumed_latch_invalid")
        require((ROOT / a3.OUTCOME).exists() != (ROOT / a3.ATTEMPT).exists(), "pass_hold_outcome_ambiguous")
        record = read_json(a3.OUTCOME if (ROOT / a3.OUTCOME).exists() else a3.ATTEMPT)
        counts = record["actual_gets"]
        require(0 <= counts["TWSE"] <= 1 and 0 <= counts["TPEX"] <= 1
                and counts["TAIFEX"] == counts["other"] == record["retry_count"] == 0,
                "network_budget_exceeded")
        require(record["owner_authority"] == a3.OWNER and record["reservation"] == {"path": a3.RESERVATION, "sha256": a3.sha(ROOT / a3.RESERVATION)}
                and record["consumed_latch"] == {"path": a3.CONSUMED, "sha256": a3.sha(ROOT / a3.CONSUMED)}
                and record["immutable_hashes"] == a3.HASHES
                and record["candidate_file_hashes"] == a3.candidate_hashes()
                and record["A3_independently_accepted"] is False
                and record["production_activation_authorized"] is False
                and record["public_v3_integration_authorized"] is False
                and record["merge_authorized"] is False, "outcome_authority_invalid")
        require(record["raw_payload_persistence"] == "NONE", "raw_payload_persistence_not_proven")
        telemetry = record["source_telemetry"]
        for market in telemetry:
            require(market in ("TWSE", "TPEX") and telemetry[market]["retry_count"] == 0
                    and telemetry[market]["redirect_policy"] == "reject"
                    and telemetry[market]["ssl_policy"] == ("compatibility" if market == "TWSE" else "strict"),
                    "transport_policy_invalid")
        if record["A3_decision"] == "PASS":
            require((ROOT / a3.OUTCOME).exists() and record["status"] == "PASS_READY_FOR_INDEPENDENT_REVIEW"
                    and counts == {"TWSE": 1, "TPEX": 1, "TAIFEX": 0, "other": 0}, "pass_network_or_record_invalid")
            require(set(telemetry) == {"TWSE", "TPEX"}, "pass_telemetry_missing")
            candidate = record["candidate"]
            require(candidate["executor_id"] == a3.EXECUTOR_ID and candidate["network_calls"] == 0
                    and candidate["retry_count"] == 0 and candidate["simulated_source_acquisition_count"] == 2,
                    "candidate_network_boundary_invalid")
            require(candidate["alignment"]["status"] in ("same_trade_date", "different_trade_date")
                    and candidate["alignment"]["same_date_implies_simultaneous_publication"] is False
                    and candidate["alignment"]["numeric_same_session_interpretation_allowed"] is False,
                    "alignment_invalid")
            for market, code in (("TWSE", "1101"), ("TPEX", "5347")):
                acquisition = telemetry[market]
                evidence = record["evidence"][market]
                validate_evidence(evidence)
                require(acquisition["http_status"] == 200 and acquisition["base_mime"] == "application/json"
                        and acquisition["complete_body_received"] is True and acquisition["error_code"] is None
                        and 0 < acquisition["response_byte_count"] <= 4 * 1024 * 1024
                        and evidence["status"] == "complete" and evidence["canonical_target_id"] == f"{market}:{code}"
                        and evidence["unit"] == "share" and evidence["publication_finality"] == "unknown"
                        and evidence["currentness_status"] == "unknown"
                        and evidence["transport"]["mode"] == "offline_injected_fixture"
                        and evidence["transport"]["network_get_count"] == 0
                        and evidence["transport"]["response_sha256"] == acquisition["response_sha256"]
                        and evidence["transport"]["response_byte_count"] == acquisition["response_byte_count"],
                        f"{market}_live_candidate_lineage_invalid")
                require(candidate["market_metrics"][market]["decode_count"] == 1
                        and candidate["market_metrics"][market]["source_prepare_count"] == 1,
                        f"{market}_candidate_reuse_invalid")
            require(record["evidence"]["TWSE"]["trade_date"] == "2026-09-30", "twse_fixed_date_invalid")
            for item in candidate["artifact_inventory"]:
                path = ROOT / record["normalized_artifact_root"] / item["relative_path"]
                require(path.is_file() and path.stat().st_size == item["byte_size"]
                        and a3.sha(path) == item["sha256"], "normalized_artifact_lineage_invalid")
        else:
            require(record["A3_decision"] == "HOLD" and (ROOT / a3.ATTEMPT).exists()
                    and record["status"] == "HOLD" and record.get("failure_code"), "hold_record_invalid")
        print(f"I3-A3 evidence integrity PASS; A3 decision={record['A3_decision']}; validator market GETs=0")
        return record


if __name__ == "__main__":
    validate(pre_network_only="--pre-network-only" in sys.argv)
