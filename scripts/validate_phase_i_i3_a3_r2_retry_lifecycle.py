"""Socket-denied R2 validation for bounded retry and lifecycle closure."""
from __future__ import annotations

import json
import socket
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import run_phase_i_i3_a3_attempt_3_bounded_live_acceptance as attempt3
from scripts import run_phase_i_i3_a3_bounded_live_acceptance as a3
from scripts.phase_i_i3_a3_retry_policy import (
    MAX_HTTP_DISPATCHES_PER_MARKET,
    MAX_RETRIES_PER_MARKET,
    retry_delay_seconds,
    retryable_transport_failure,
)


def require(condition: bool, code: str) -> None:
    if not condition:
        raise ValueError(code)


def read_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def validate(*, pre_network_only: bool = False) -> dict:
    def deny(*args, **kwargs):
        raise AssertionError("r2_validator_market_socket_forbidden")

    with patch("socket.socket.connect", deny), patch("socket.create_connection", deny):
        attempt3.attempt2_history_intact()
        a3.production_containment()
        require(MAX_HTTP_DISPATCHES_PER_MARKET == 10 and MAX_RETRIES_PER_MARKET == 9,
                "r2_retry_budget_invalid")
        require(tuple(retry_delay_seconds(n) for n in range(2, 11))
                == (1, 2, 4, 8, 10, 10, 10, 10, 10), "r2_backoff_invalid")
        require(retryable_transport_failure({
                    "complete_body_received": False,
                    "error_code": "URLError",
                    "reason_classification": "connection_reset",
                    "failure_phase": "response_body_read",
                    "http_status": 200,
                }), "r2_connection_reset_must_retry")
        require(not retryable_transport_failure({
                    "complete_body_received": False,
                    "error_code": "unsupported_content_type",
                    "reason_classification": None,
                    "http_status": 200,
                }), "r2_semantic_failure_must_not_retry")
        closure = read_json(attempt3.R2_RECORD)
        require(closure["schema_version"] == "phase_i_i3_a3_r2_bounded_multi_dispatch_retry_lifecycle_closure.v1"
                and closure["status"] == "OFFLINE_PASS_READY_FOR_FRESH_OWNER_AUTHORIZATION"
                and closure["max_http_dispatches_per_market"] == 10
                and closure["max_retries_per_market"] == 9
                and closure["fallback_endpoint_allowed"] is False
                and closure["acquisition_order"] == ["TPEX", "TWSE"]
                and closure["attempt_2_status"] == "HOLD_VALID_HISTORICAL_OUTCOME"
                and closure["attempt_2_authority"] == "CONSUMED_NOT_REUSABLE"
                and closure["sealed_code_hashes"] == attempt3.sealed_hashes()
                and closure["candidate_file_hashes"] == a3.candidate_hashes()
                and closure["immutable_hashes"] == a3.HASHES
                and closure["I3_production"] == {"active_sources": 0, "routes": 0}
                and closure["mcp_tool_count"] == 6
                and closure["production_activation_authorized"] is False
                and closure["A4_authorized"] is False
                and closure["merge_authorized"] is False,
                "r2_closure_invalid")
        targets, security_master = a3.load_targets()
        require(closure["targets"] == targets and closure["security_master"] == security_master,
                "r2_identity_drift")
        if pre_network_only:
            attempt3.attempt3_artifacts_absent()
            print("I3-A3-R2 offline PASS; Attempt 3 authority not granted; market GETs=0")
            return closure

        require((ROOT / attempt3.RESERVATION).is_file() and (ROOT / attempt3.CONSUMED).is_file(),
                "attempt_3_authority_latch_missing")
        require((ROOT / attempt3.OUTCOME).exists() != (ROOT / attempt3.HOLD).exists(),
                "attempt_3_pass_hold_ambiguous")
        record = read_json(attempt3.OUTCOME if (ROOT / attempt3.OUTCOME).exists() else attempt3.HOLD)
        for market in ("TPEX", "TWSE"):
            require(0 <= record["http_dispatch_count"][market] <= 10
                    and 0 <= record["transport_attempt_count"][market] <= 10
                    and record["retry_count_by_market"][market]
                    == max(0, record["transport_attempt_count"][market] - 1),
                    "attempt_3_retry_accounting_invalid")
        require(record["http_dispatch_count"]["TAIFEX"] == 0
                and record["http_dispatch_count"]["other"] == 0
                and record["fallback_endpoint_allowed"] is False
                and record["A3_independently_accepted"] is False
                and record["production_activation_authorized"] is False
                and record["public_v3_integration_authorized"] is False
                and record["A4_authorized"] is False
                and record["merge_authorized"] is False,
                "attempt_3_outcome_boundary_invalid")
        print(f"I3-A3 Attempt 3 evidence integrity PASS; decision={record['A3_decision']}; validator market GETs=0")
        return record


if __name__ == "__main__":
    validate(pre_network_only="--pre-network-only" in sys.argv)