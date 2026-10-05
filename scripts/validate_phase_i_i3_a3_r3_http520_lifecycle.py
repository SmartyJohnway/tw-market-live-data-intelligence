"""Socket-denied R3 validation for observed HTTP 520 retry and Attempt 3 lifecycle."""
from __future__ import annotations

import json
import hashlib
import socket
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# R3 sealed Attempt 4's runner bytes at this reviewed pre-network commit.
# Later authorized A4 work adds a production-containment projection to one
# shared helper; historical R3 validation must compare its seal to the sealed
# commit, not mistake that later additive change for historical tampering.
SEALED_ATTEMPT_4_COMMIT = "bff6ee179115bb9c78b183f2cd8c5b7f4afcfb8c"

from scripts import run_phase_i_i3_a3_attempt_4_bounded_live_acceptance as attempt4
from scripts import run_phase_i_i3_a3_bounded_live_acceptance as a3
from scripts.phase_i_i3_a3_retry_policy_v2 import (
    MAX_HTTP_DISPATCHES_PER_MARKET,
    MAX_RETRIES_PER_MARKET,
    RETRYABLE_HTTP_STATUS,
    retryable_transport_failure,
)


def require(condition: bool, code: str) -> None:
    if not condition:
        raise ValueError(code)


def read_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def sealed_code_hashes() -> dict[str, str]:
    return {
        path: hashlib.sha256(subprocess.check_output(
            ["git", "show", f"{SEALED_ATTEMPT_4_COMMIT}:{path}"], cwd=ROOT
        )).hexdigest()
        for path in attempt4.HASHED_CODE
    }


def validate(*, pre_network_only: bool = False) -> dict:
    def deny(*args, **kwargs):
        raise AssertionError("r3_validator_market_socket_forbidden")

    with patch("socket.socket.connect", deny), patch("socket.create_connection", deny):
        attempt4.historical_attempts_intact()
        a3.production_containment()
        require(MAX_HTTP_DISPATCHES_PER_MARKET == 10 and MAX_RETRIES_PER_MARKET == 9,
                "r3_retry_budget_invalid")
        require(520 in RETRYABLE_HTTP_STATUS, "r3_observed_520_not_retryable")
        require(retryable_transport_failure({
            "complete_body_received": False,
            "error_code": "http_status_not_200",
            "http_status": 520,
            "reason_classification": None,
            "failure_phase": "http_response_headers",
        }), "r3_520_retry_contract_invalid")
        require(not retryable_transport_failure({
            "complete_body_received": False,
            "error_code": "http_status_not_200",
            "http_status": 404,
            "reason_classification": None,
            "failure_phase": "http_response_headers",
        }), "r3_nontransient_http_must_not_retry")

        closure = read_json(attempt4.R3_RECORD)
        require(
            closure["schema_version"] == "phase_i_i3_a3_r3_http_520_retry_and_attempt_3_lifecycle_closure.v1"
            and closure["status"] == "OFFLINE_PASS_READY_FOR_FRESH_OWNER_AUTHORIZATION"
            and closure["max_http_dispatches_per_market"] == 10
            and closure["max_retries_per_market"] == 9
            and 520 in closure["retryable_http_status"]
            and closure["attempt_3_status"] == "HOLD_VALID_HISTORICAL_OUTCOME"
            and closure["attempt_3_authority"] == "CONSUMED_NOT_REUSABLE"
            and closure["attempt_3_http_dispatch_count"] == {"TPEX": 8, "TWSE": 0, "TAIFEX": 0, "other": 0}
            and closure["attempt_3_terminal_http_status"] == 520
            and closure["sealed_code_hashes"] == sealed_code_hashes()
            and closure["candidate_file_hashes"] == a3.candidate_hashes()
            and closure["immutable_hashes"] == a3.HASHES
            and closure["I3_production"] == {"active_sources": 0, "routes": 0}
            and closure["mcp_tool_count"] == 6
            and closure["production_activation_authorized"] is False
            and closure["A4_authorized"] is False
            and closure["merge_authorized"] is False,
            "r3_closure_invalid",
        )
        targets, security_master = a3.load_targets()
        require(closure["targets"] == targets and closure["security_master"] == security_master,
                "r3_identity_drift")

        if pre_network_only:
            attempt4.attempt4_artifacts_absent()
            print("I3-A3-R3 offline PASS; Attempt 4 authority not granted; market GETs=0")
            return closure

        require((ROOT / attempt4.RESERVATION).is_file() and (ROOT / attempt4.CONSUMED).is_file(),
                "attempt_4_authority_latch_missing")
        require((ROOT / attempt4.OUTCOME).exists() != (ROOT / attempt4.HOLD).exists(),
                "attempt_4_pass_hold_ambiguous")
        record = read_json(attempt4.OUTCOME if (ROOT / attempt4.OUTCOME).exists() else attempt4.HOLD)
        for market in ("TPEX", "TWSE"):
            require(
                0 <= record["http_dispatch_count"][market] <= 10
                and 0 <= record["transport_attempt_count"][market] <= 10
                and record["retry_count_by_market"][market]
                == max(0, record["transport_attempt_count"][market] - 1),
                "attempt_4_retry_accounting_invalid",
            )
        require(
            record["http_dispatch_count"]["TAIFEX"] == 0
            and record["http_dispatch_count"]["other"] == 0
            and record["fallback_endpoint_allowed"] is False
            and record["A3_independently_accepted"] is False
            and record["production_activation_authorized"] is False
            and record["public_v3_integration_authorized"] is False
            and record["A4_authorized"] is False
            and record["merge_authorized"] is False,
            "attempt_4_outcome_boundary_invalid",
        )
        print(f"I3-A3 Attempt 4 evidence integrity PASS; decision={record['A3_decision']}; validator market GETs=0")
        return record


if __name__ == "__main__":
    validate(pre_network_only="--pre-network-only" in sys.argv)
