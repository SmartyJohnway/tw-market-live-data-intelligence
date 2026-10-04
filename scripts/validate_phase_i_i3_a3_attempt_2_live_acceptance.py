"""Socket-denied validation of the distinct TPEx-first Attempt 2 gate."""
from __future__ import annotations

import json
import socket
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import run_phase_i_i3_a3_attempt_2_bounded_live_acceptance as attempt2
from scripts import run_phase_i_i3_a3_bounded_live_acceptance as a3
from scripts import validate_phase_i_i3_a3_r1 as r1
from scripts.phase_i_i3_transport_mapping import CANONICAL_TO_TRANSPORT_MARKET


def require(condition: bool, code: str) -> None:
    if not condition:
        raise ValueError(code)


def read_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def validate(*, pre_network_only: bool = False) -> dict:
    def deny(*args, **kwargs):
        raise AssertionError("attempt_2_validator_market_socket_forbidden")
    with patch("socket.socket.connect", deny), patch("socket.create_connection", deny):
        r1.validate()
        require(a3.sha(ROOT / r1.RECORD) == attempt2.R1_SHA256, "r1_record_hash_drift")
        require(CANONICAL_TO_TRANSPORT_MARKET == {"TWSE": "TWSE", "TPEX": "TPEx"}
                and attempt2.ACQUISITION_ORDER == ("TPEX", "TWSE")
                and attempt2.NETWORK_BUDGET == {"TPEX": 1, "TWSE": 1, "TAIFEX": 0, "other": 0, "retry": 0},
                "attempt_2_order_mapping_or_budget_invalid")
        closure = read_json(attempt2.PRE_NETWORK)
        require(closure["schema_version"] == "phase_i_i3_a3_attempt_2_pre_network_runner_closure.v1"
                and closure["status"] == "PASS_READY_FOR_FRESH_OWNER_AUTHORIZATION"
                and closure["gate"] == "I3-A3 Attempt 2"
                and closure["mode"] == "TPEx-first"
                and closure["starting_main"] == a3.BASELINE
                and closure["starting_head"] == attempt2.START_HEAD
                and closure["starting_tree"] == attempt2.START_TREE
                and closure["branch"] == a3.BRANCH
                and closure["pr"] == {"number": 300, "state": "OPEN", "draft": True}
                and closure["acquisition_order"] == list(attempt2.ACQUISITION_ORDER)
                and closure["canonical_transport_mapping"] == CANONICAL_TO_TRANSPORT_MARKET
                and closure["request_identity"] == {"offline_proof_namespace": attempt2.OFFLINE_REQUEST_NAMESPACE,
                    "future_live_hash_authority": "fresh_owner_literal_only", "attempt_1_owner_literal_reused": False}
                and closure["network_budget"] == attempt2.NETWORK_BUDGET
                and closure["authority_status"] == "NOT_YET_GRANTED"
                and closure["live_authority_consumed"] is False
                and closure["sealed_code_hashes"] == attempt2.sealed_hashes()
                and closure["candidate_file_hashes"] == a3.candidate_hashes()
                and closure["immutable_hashes"] == a3.HASHES
                and closure["r1_record_sha256"] == attempt2.R1_SHA256
                and closure["historical_attempt_1_status"] == "HOLD"
                and closure["historical_attempt_1_authority"] == "CONSUMED_NOT_REUSABLE"
                and closure["actual_market_gets_during_preparation"] == {"TPEX": 0, "TWSE": 0, "TAIFEX": 0, "other": 0}
                and closure["I3_production"] == {"active_sources": 0, "routes": 0}
                and closure["mcp_tool_count"] == 6
                and closure["production_activation_authorized"] is False
                and closure["A4_authorized"] is False
                and closure["merge_authorized"] is False,
                "attempt_2_pre_network_closure_invalid")
        targets, security_master = a3.load_targets()
        require(closure["targets"] == targets and closure["security_master"] == security_master,
                "attempt_2_target_authority_invalid")
        a3.production_containment()
        if pre_network_only:
            attempt2.attempt2_artifacts_absent()
            print("I3-A3 Attempt 2 pre-network PASS; fresh Owner authority not granted; market GETs=0")
            return closure
        require((ROOT / attempt2.RESERVATION).is_file() and (ROOT / attempt2.CONSUMED).is_file(),
                "attempt_2_authority_latch_missing")
        reservation = read_json(attempt2.RESERVATION)
        consumed = read_json(attempt2.CONSUMED)
        require(reservation["gate"] == "I3-A3 Attempt 2"
                and reservation["owner_authority"] != a3.OWNER
                and attempt2.fresh_owner_reference(reservation["owner_authority"])
                and reservation["pre_network_tree"] == subprocess.check_output(
                    ["git", "show", "-s", "--format=%T", reservation["pre_network_commit"]],
                    cwd=ROOT, text=True).strip()
                and reservation["acquisition_order"] == list(attempt2.ACQUISITION_ORDER)
                and reservation["network_budget"] == attempt2.NETWORK_BUDGET
                and reservation["sealed_code_hashes"] == attempt2.sealed_hashes()
                and reservation["reserved"] is True and reservation["consumed"] is False,
                "attempt_2_reservation_invalid")
        require(consumed["owner_authority"] == reservation["owner_authority"]
                and consumed["reservation_sha256"] == a3.sha(ROOT / attempt2.RESERVATION)
                and consumed["consumed"] is True
                and consumed["consumed_before_first_http_attempt"] is True,
                "attempt_2_consumed_latch_invalid")
        require((ROOT / attempt2.OUTCOME).exists() != (ROOT / attempt2.HOLD).exists(),
                "attempt_2_pass_hold_ambiguous")
        record = read_json(attempt2.OUTCOME if (ROOT / attempt2.OUTCOME).exists() else attempt2.HOLD)
        callbacks, dispatches = record["acquisition_callback_attempts"], record["http_dispatch_count"]
        for counter in (callbacks, dispatches):
            require(isinstance(counter, dict) and set(counter) == {"TWSE", "TPEX", "TAIFEX", "other"}
                    and all(type(value) is int and 0 <= value <= 1 for value in counter.values())
                    and counter["TAIFEX"] == counter["other"] == 0,
                    "attempt_2_counter_invalid")
        require(all(dispatches[key] <= callbacks[key] for key in callbacks)
                and callbacks["TPEX"] == 1
                and callbacks["TWSE"] <= int(record["source_telemetry"].get("TPEX", {}).get("complete_body_received") is True)
                and record["retry_count"] == 0
                and record["raw_payload_persistence"] in ("NONE", "NONE_UNVERIFIED_AFTER_EXCEPTION")
                and record["owner_authority"] == reservation["owner_authority"]
                and record["A3_independently_accepted"] is False
                and record["production_activation_authorized"] is False
                and record["public_v3_integration_authorized"] is False
                and record["A4_authorized"] is False
                and record["merge_authorized"] is False,
                "attempt_2_outcome_boundary_invalid")
        if record["A3_decision"] == "PASS":
            require((ROOT / attempt2.OUTCOME).exists()
                    and callbacks == dispatches == {"TWSE": 1, "TPEX": 1, "TAIFEX": 0, "other": 0}
                    and record["raw_payload_persistence"] == "NONE"
                    and record["candidate_reached"] is True
                    and record["candidate"]["network_calls"] == 0
                    and all(record["source_telemetry"][key]["complete_body_received"] is True
                            and record["evidence"][key]["status"] == "complete"
                            and record["evidence"][key]["unit"] == "share"
                            and record["evidence"][key]["transport"]["response_sha256"] == record["source_telemetry"][key]["response_sha256"]
                            and record["evidence"][key]["transport"]["response_byte_count"] == record["source_telemetry"][key]["response_byte_count"]
                            for key in ("TPEX", "TWSE")), "attempt_2_pass_not_proven")
        else:
            require(record["A3_decision"] == "HOLD" and (ROOT / attempt2.HOLD).exists()
                    and bool(record.get("failure_code")), "attempt_2_hold_invalid")
        print(f"I3-A3 Attempt 2 evidence integrity PASS; decision={record['A3_decision']}; validator market GETs=0")
        return record


if __name__ == "__main__":
    validate(pre_network_only="--pre-network-only" in sys.argv)
