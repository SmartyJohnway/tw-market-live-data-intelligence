"""Distinct, TPEx-first I3-A3 Attempt 2 runner; offline until fresh Owner authority.

Never invoke ``--live`` using the consumed Attempt 1 authority. Importing this
module has no source-acquisition side effects.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import phase_i_i3_a0_source_transport as transport
from scripts import run_phase_i_i3_a3_bounded_live_acceptance as a3
from scripts import validate_phase_i_i3_a3_r1 as r1
from scripts.phase_i_i3_transport_mapping import CANONICAL_TO_TRANSPORT_MARKET

START_HEAD = "b2539d3e4f560d6c3e424e0dbff9e645433d29af"
START_TREE = "b98b0264694519a510f653a202a4eb76bf51bc80"
R1_SHA256 = "b34d2d7509b2819904d8d9c29f50f68dd69c9b26d60aff1292ee15677f362b75"
OLD_OWNER = a3.OWNER
PREFIX = "docs/governance/phase_i/"
PRE_NETWORK = PREFIX + "PHASE_I_I3_A3_ATTEMPT_2_PRE_NETWORK_RUNNER_CLOSURE_2026-10-04.json"
RESERVATION = PREFIX + "acceptance_runs/i3-a3-attempt-2-live-authority-reservation.json"
CONSUMED = PREFIX + "acceptance_runs/i3-a3-attempt-2-live-authority-consumed.json"
OUTCOME = PREFIX + "PHASE_I_I3_A3_ATTEMPT_2_BOUNDED_LIVE_ADAPTER_ACCEPTANCE_2026-10-04.json"
HOLD = PREFIX + "PHASE_I_I3_A3_ATTEMPT_2_BOUNDED_LIVE_ADAPTER_ACCEPTANCE_HOLD_2026-10-04.json"
ARTIFACT_ROOT = PREFIX + "acceptance_runs/i3-a3-attempt-2-live"
ACQUISITION_ORDER = ("TPEX", "TWSE")
OFFLINE_REQUEST_NAMESPACE = "phase-i-i3-a3-attempt-2-offline-proof"
NETWORK_BUDGET = {"TPEX": 1, "TWSE": 1, "TAIFEX": 0, "other": 0, "retry": 0}
HASHED_CODE = {
    "scripts/run_phase_i_i3_a3_attempt_2_bounded_live_acceptance.py": "runner_sha256",
    "scripts/validate_phase_i_i3_a3_attempt_2_live_acceptance.py": "validator_sha256",
    "scripts/run_phase_i_i3_a3_bounded_live_acceptance.py": "shared_runner_sha256",
    "scripts/phase_i_i3_transport_mapping.py": "mapping_sha256",
    "scripts/phase_i_i3_a0_source_transport.py": "source_transport_sha256",
}


def require(condition: bool, code: str) -> None:
    if not condition:
        raise RuntimeError(code)


def fresh_owner_reference(value: str) -> str:
    require(isinstance(value, str) and value.startswith("USER_CHAT_")
            and value != OLD_OWNER and len(value) > len("USER_CHAT_"),
            "fresh_separate_owner_authority_required")
    return value


def attempt2_artifacts_absent() -> None:
    require(not any((ROOT / path).exists() for path in (RESERVATION, CONSUMED, OUTCOME, HOLD)),
            "attempt_2_single_use_latch_or_outcome_exists")


def sealed_hashes() -> dict[str, str]:
    return {field: a3.sha(ROOT / path) for path, field in HASHED_CODE.items()}


def execute_with_acquirer(acquire: Callable[[str], tuple[dict, bytes | None]], targets: dict[str, dict],
                          *, http_dispatch_count: dict[str, int] | None = None,
                          operation_authority: str = OFFLINE_REQUEST_NAMESPACE) -> tuple[dict, dict[str, bytes]]:
    return a3.execute_with_acquirer(acquire, targets, http_dispatch_count=http_dispatch_count,
                                    acquisition_order=ACQUISITION_ORDER,
                                    operation_authority=operation_authority)


def final_pre_network_guard(sealed_head: str) -> tuple[dict, dict, str]:
    require(len(sealed_head) == 40 and a3.git("rev-parse", "HEAD") == sealed_head,
            "attempt_2_sealed_head_drift")
    sealed_tree = a3.git("show", "-s", "--format=%T", "HEAD")
    require(a3.git("branch", "--show-current") == a3.BRANCH
            and a3.git("rev-parse", "origin/main") == a3.BASELINE
            and a3.git("status", "--porcelain") in ("", "?? data/"),
            "attempt_2_branch_main_or_worktree_drift")
    pr = json.loads(subprocess.check_output(["gh", "pr", "view", "300", "--json",
                    "state,isDraft,headRefOid"], cwd=ROOT))
    require(pr == {"state": "OPEN", "isDraft": True, "headRefOid": sealed_head},
            "attempt_2_draft_pr_drift")
    attempt2_artifacts_absent()
    r1.validate()
    require(a3.sha(ROOT / r1.RECORD) == R1_SHA256, "r1_closure_hash_drift")
    require(CANONICAL_TO_TRANSPORT_MARKET == {"TWSE": "TWSE", "TPEX": "TPEx"}
            and ACQUISITION_ORDER == ("TPEX", "TWSE") and transport.RETRY_COUNT == 0,
            "attempt_2_mapping_order_or_retry_drift")
    closure = json.loads((ROOT / PRE_NETWORK).read_text(encoding="utf-8"))
    require(closure["status"] == "PASS_READY_FOR_FRESH_OWNER_AUTHORIZATION"
            and closure["starting_main"] == a3.BASELINE
            and closure["starting_head"] == START_HEAD
            and closure["starting_tree"] == START_TREE
            and closure["acquisition_order"] == list(ACQUISITION_ORDER)
            and closure["network_budget"] == NETWORK_BUDGET
            and closure["authority_status"] == "NOT_YET_GRANTED"
            and closure["live_authority_consumed"] is False
            and closure["sealed_code_hashes"] == sealed_hashes()
            and closure["candidate_file_hashes"] == a3.candidate_hashes()
            and closure["immutable_hashes"] == a3.HASHES
            and closure["r1_record_sha256"] == R1_SHA256,
            "attempt_2_pre_network_seal_invalid")
    targets, security_master = a3.load_targets()
    require(closure["targets"] == targets and closure["security_master"] == security_master,
            "attempt_2_identity_drift")
    return targets, security_master, sealed_tree


def live(sealed_head: str, owner_reference: str) -> dict:
    fresh_owner_reference(owner_reference)
    targets, security_master, sealed_tree = final_pre_network_guard(sealed_head)
    reservation = {
        "schema_version": "phase_i_i3_a3_attempt_2_live_authority_reservation.v1",
        "gate": "I3-A3 Attempt 2", "owner_authority": owner_reference,
        "starting_main": a3.BASELINE, "pre_network_commit": sealed_head,
        "pre_network_tree": sealed_tree, "acquisition_order": list(ACQUISITION_ORDER),
        "network_budget": NETWORK_BUDGET, "immutable_hashes": a3.HASHES,
        "candidate_file_hashes": a3.candidate_hashes(),
        "sealed_code_hashes": sealed_hashes(), "targets": targets,
        "security_master": security_master, "reserved": True, "consumed": False,
    }
    reservation_sha = a3.write_once(RESERVATION, reservation)
    consumed = {"schema_version": "phase_i_i3_a3_attempt_2_live_authority_consumed.v1",
                "owner_authority": owner_reference, "reservation_sha256": reservation_sha,
                "consumed": True, "consumed_before_first_http_attempt": True}
    consumed_sha = a3.write_once(CONSUMED, consumed)
    dispatches = {"TWSE": 0, "TPEX": 0, "TAIFEX": 0, "other": 0}
    fallback_callbacks = {"TWSE": 0, "TPEX": 0, "TAIFEX": 0, "other": 0}

    def acquire(market: str):
        fallback_callbacks[market] += 1
        def observed_dispatch() -> None:
            dispatches[market] += 1
        return a3.acquire_reviewed_source(market, on_http_dispatch=observed_dispatch)

    try:
        result, artifacts = execute_with_acquirer(acquire, targets, http_dispatch_count=dispatches,
                                                 operation_authority=owner_reference)
    except Exception as exc:
        result, artifacts = ({"A3_decision": "HOLD", "failure_code": "runner_exception:" + type(exc).__name__,
                              "acquisition_callback_attempts": fallback_callbacks,
                              "http_dispatch_count": dispatches, "retry_count": 0,
                              "source_telemetry": {}, "candidate": None,
                              "raw_payload_persistence": "NONE_UNVERIFIED_AFTER_EXCEPTION"}, {})
    result.update({"schema_version": "phase_i_i3_a3_attempt_2_bounded_live_adapter_acceptance.v1",
                   "status": "PASS_READY_FOR_INDEPENDENT_REVIEW" if result["A3_decision"] == "PASS" else "HOLD",
                   "owner_authority": owner_reference, "starting_main": a3.BASELINE,
                   "pre_network_commit": sealed_head, "pre_network_tree": sealed_tree,
                   "acquisition_order": list(ACQUISITION_ORDER), "network_budget": NETWORK_BUDGET,
                   "reservation": {"path": RESERVATION, "sha256": reservation_sha},
                   "consumed_latch": {"path": CONSUMED, "sha256": consumed_sha},
                   "immutable_hashes": a3.HASHES, "candidate_file_hashes": a3.candidate_hashes(),
                   "sealed_code_hashes": sealed_hashes(), "security_master": security_master,
                   "targets": targets, "candidate_reached": result.get("candidate") is not None,
                   "A3_independently_accepted": False, "production_activation_authorized": False,
                   "public_v3_integration_authorized": False, "A4_authorized": False,
                   "merge_authorized": False})
    if result["A3_decision"] == "PASS":
        for relative, body in artifacts.items():
            a3.write_once(f"{ARTIFACT_ROOT}/{relative}", body)
        result["normalized_artifact_root"] = ARTIFACT_ROOT
    a3.write_once(OUTCOME if result["A3_decision"] == "PASS" else HOLD, result)
    require(a3.candidate_hashes() == reservation["candidate_file_hashes"]
            and a3.immutable_hashes() == a3.HASHES, "post_attempt_2_immutable_hash_drift")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--confirm-single-use-tpex-first-two-market-budget", action="store_true")
    parser.add_argument("--owner-authorization-reference", required=True)
    parser.add_argument("--sealed-pre-network-head", required=True)
    args = parser.parse_args()
    require(args.live and args.confirm_single_use_tpex_first_two_market_budget,
            "attempt_2_live_confirmation_required")
    result = live(args.sealed_pre_network_head, args.owner_authorization_reference)
    print(json.dumps({"A3_decision": result["A3_decision"],
                      "acquisition_callback_attempts": result["acquisition_callback_attempts"],
                      "http_dispatch_count": result["http_dispatch_count"],
                      "failure_code": result.get("failure_code")}, sort_keys=True))


if __name__ == "__main__":
    main()
