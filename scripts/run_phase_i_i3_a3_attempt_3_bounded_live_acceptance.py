"""Attempt 3 runner with one authorization and bounded multi-dispatch retry.

This module is offline until a fresh Owner authority is supplied after sealing.
It never changes production registration, public V3 integration, or MCP tools.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import run_phase_i_i3_a3_bounded_live_acceptance as a3
from scripts import validate_phase_i_i3_a3_r1 as r1
from scripts.phase_i_i3_a3_retry_policy import (
    MAX_HTTP_DISPATCHES_PER_MARKET,
    MAX_RETRIES_PER_MARKET,
    retry_delay_seconds,
    retryable_transport_failure,
)
from scripts.phase_i_i3_transport_mapping import CANONICAL_TO_TRANSPORT_MARKET

START_HEAD = "70c29f314f678e2f1e566a30d0f0ea44275e3b24"
START_TREE = "1d82ceb6c36471d54b742b450c9f1dd44e326389"
ATTEMPT2_OWNER = "USER_CHAT_2026-10-04_PHASE_I_I3_A3_ATTEMPT_2_TPEX_FIRST_SINGLE_USE_LIVE_AUTHORIZATION"
PREFIX = "docs/governance/phase_i/"
R2_RECORD = PREFIX + "PHASE_I_I3_A3_R2_BOUNDED_MULTI_DISPATCH_RETRY_LIFECYCLE_CLOSURE_2026-10-04.json"
RESERVATION = PREFIX + "acceptance_runs/i3-a3-attempt-3-live-authority-reservation.json"
CONSUMED = PREFIX + "acceptance_runs/i3-a3-attempt-3-live-authority-consumed.json"
OUTCOME = PREFIX + "PHASE_I_I3_A3_ATTEMPT_3_BOUNDED_LIVE_ADAPTER_ACCEPTANCE_2026-10-04.json"
HOLD = PREFIX + "PHASE_I_I3_A3_ATTEMPT_3_BOUNDED_LIVE_ADAPTER_ACCEPTANCE_HOLD_2026-10-04.json"
ARTIFACT_ROOT = PREFIX + "acceptance_runs/i3-a3-attempt-3-live"
ACQUISITION_ORDER = ("TPEX", "TWSE")
OFFLINE_REQUEST_NAMESPACE = "phase-i-i3-a3-attempt-3-offline-proof"
ATTEMPT2_IMMUTABLE = {
    PREFIX + "PHASE_I_I3_A3_ATTEMPT_2_PRE_NETWORK_RUNNER_CLOSURE_2026-10-04.json":
        "2ae57eb21660bf03601403d74a0498a6d65a27367e15b2a2cb53f996fb0d4e7f",
    PREFIX + "PHASE_I_I3_A3_ATTEMPT_2_BOUNDED_LIVE_ADAPTER_ACCEPTANCE_HOLD_2026-10-04.json":
        "c5dd0380c19799294eb2ee163cd217f43cc79091de8e31694aa31b19c7773c73",
    PREFIX + "acceptance_runs/i3-a3-attempt-2-live-authority-reservation.json":
        "97c2af3ce62c9664f650837a2a164f4e1b138b9ae7f354ce0d4638efd57e082e",
    PREFIX + "acceptance_runs/i3-a3-attempt-2-live-authority-consumed.json":
        "b586726d691c199f5a0bda0445ce884f36641f707e2f751f462469722bee6f85",
}
HASHED_CODE = (
    "scripts/run_phase_i_i3_a3_attempt_3_bounded_live_acceptance.py",
    "scripts/validate_phase_i_i3_a3_r2_retry_lifecycle.py",
    "scripts/phase_i_i3_a3_retry_policy.py",
    "scripts/run_phase_i_i3_a3_bounded_live_acceptance.py",
    "scripts/phase_i_i3_transport_mapping.py",
    "scripts/phase_i_i3_a0_source_transport.py",
)


def require(condition: bool, code: str) -> None:
    if not condition:
        raise RuntimeError(code)


def fresh_owner_reference(value: str) -> str:
    require(isinstance(value, str) and value.startswith("USER_CHAT_")
            and value not in {a3.OWNER, ATTEMPT2_OWNER}
            and len(value) > len("USER_CHAT_"), "fresh_separate_owner_authority_required")
    return value


def attempt3_artifacts_absent() -> None:
    require(not any((ROOT / path).exists() for path in (RESERVATION, CONSUMED, OUTCOME, HOLD)),
            "attempt_3_single_use_latch_or_outcome_exists")


def sealed_hashes() -> dict[str, str]:
    return {path: a3.sha(ROOT / path) for path in HASHED_CODE}


def attempt2_history_intact() -> None:
    actual = {path: a3.sha(ROOT / path) for path in ATTEMPT2_IMMUTABLE}
    require(actual == ATTEMPT2_IMMUTABLE, "attempt_2_history_drift")


def acquire_with_retry(
    market: str,
    *,
    on_http_dispatch: Callable[[], None],
    attempt_history: dict[str, list[dict]],
    sleeper: Callable[[float], None] = time.sleep,
    opener_factory: Callable | None = None,
) -> tuple[dict, bytes | None]:
    """Retry one reviewed endpoint up to ten dispatches for transient failures."""
    history = attempt_history.setdefault(market, [])
    for attempt_number in range(1, MAX_HTTP_DISPATCHES_PER_MARKET + 1):
        kwargs: dict[str, Any] = {"on_http_dispatch": on_http_dispatch}
        if opener_factory is not None:
            kwargs["opener_factory"] = opener_factory
        observation, body = a3.acquire_reviewed_source(market, **kwargs)
        bounded_observation = dict(observation)
        bounded_observation["attempt_number"] = attempt_number
        history.append(bounded_observation)
        if a3.qualified(observation, body):
            return observation, body
        if not retryable_transport_failure(observation):
            return observation, None
        if attempt_number == MAX_HTTP_DISPATCHES_PER_MARKET:
            return observation, None
        sleeper(retry_delay_seconds(attempt_number + 1))
    raise RuntimeError("retry_loop_unreachable")


def final_pre_network_guard(sealed_head: str) -> tuple[dict, dict, str]:
    require(len(sealed_head) == 40 and a3.git("rev-parse", "HEAD") == sealed_head,
            "attempt_3_sealed_head_drift")
    sealed_tree = a3.git("show", "-s", "--format=%T", "HEAD")
    require(a3.git("branch", "--show-current") == a3.BRANCH
            and a3.git("rev-parse", "origin/main") == a3.BASELINE
            and a3.git("status", "--porcelain") in ("", "?? data/"),
            "attempt_3_branch_main_or_worktree_drift")
    pr = json.loads(subprocess.check_output(
        ["gh", "pr", "view", "300", "--json", "state,isDraft,headRefOid"], cwd=ROOT))
    require(pr == {"state": "OPEN", "isDraft": True, "headRefOid": sealed_head},
            "attempt_3_draft_pr_drift")
    attempt3_artifacts_absent()
    attempt2_history_intact()
    r1.validate()
    a3.production_containment()
    require(CANONICAL_TO_TRANSPORT_MARKET == {"TWSE": "TWSE", "TPEX": "TPEx"}
            and ACQUISITION_ORDER == ("TPEX", "TWSE"), "attempt_3_mapping_or_order_drift")
    closure = json.loads((ROOT / R2_RECORD).read_text(encoding="utf-8"))
    require(closure["status"] == "OFFLINE_PASS_READY_FOR_FRESH_OWNER_AUTHORIZATION"
            and closure["max_http_dispatches_per_market"] == MAX_HTTP_DISPATCHES_PER_MARKET
            and closure["max_retries_per_market"] == MAX_RETRIES_PER_MARKET
            and closure["sealed_code_hashes"] == sealed_hashes()
            and closure["candidate_file_hashes"] == a3.candidate_hashes()
            and closure["immutable_hashes"] == a3.HASHES,
            "attempt_3_r2_seal_invalid")
    targets, security_master = a3.load_targets()
    require(closure["targets"] == targets and closure["security_master"] == security_master,
            "attempt_3_identity_drift")
    return targets, security_master, sealed_tree


def live(sealed_head: str, owner_reference: str) -> dict:
    fresh_owner_reference(owner_reference)
    targets, security_master, sealed_tree = final_pre_network_guard(sealed_head)
    reservation = {
        "schema_version": "phase_i_i3_a3_attempt_3_live_authority_reservation.v1",
        "gate": "I3-A3 Attempt 3",
        "owner_authority": owner_reference,
        "starting_main": a3.BASELINE,
        "pre_network_commit": sealed_head,
        "pre_network_tree": sealed_tree,
        "acquisition_order": list(ACQUISITION_ORDER),
        "max_http_dispatches_per_market": MAX_HTTP_DISPATCHES_PER_MARKET,
        "max_retries_per_market": MAX_RETRIES_PER_MARKET,
        "fallback_endpoint_allowed": False,
        "candidate_file_hashes": a3.candidate_hashes(),
        "immutable_hashes": a3.HASHES,
        "sealed_code_hashes": sealed_hashes(),
        "targets": targets,
        "security_master": security_master,
        "reserved": True,
        "consumed": False,
    }
    reservation_sha = a3.write_once(RESERVATION, reservation)
    consumed = {
        "schema_version": "phase_i_i3_a3_attempt_3_live_authority_consumed.v1",
        "owner_authority": owner_reference,
        "reservation_sha256": reservation_sha,
        "consumed": True,
        "consumed_before_first_http_attempt": True,
    }
    consumed_sha = a3.write_once(CONSUMED, consumed)

    dispatches = {"TWSE": 0, "TPEX": 0, "TAIFEX": 0, "other": 0}
    fallback_callbacks = {"TWSE": 0, "TPEX": 0, "TAIFEX": 0, "other": 0}
    histories: dict[str, list[dict]] = {}

    def acquire(market: str):
        fallback_callbacks[market] += 1

        def observed_dispatch() -> None:
            dispatches[market] += 1
            require(dispatches[market] <= MAX_HTTP_DISPATCHES_PER_MARKET,
                    "attempt_3_http_dispatch_budget_exceeded")

        return acquire_with_retry(
            market,
            on_http_dispatch=observed_dispatch,
            attempt_history=histories,
        )

    try:
        result, artifacts = a3.execute_with_acquirer(
            acquire,
            targets,
            http_dispatch_count=dispatches,
            acquisition_order=ACQUISITION_ORDER,
            operation_authority=owner_reference,
        )
    except Exception as exc:
        result, artifacts = ({
            "A3_decision": "HOLD",
            "failure_code": "runner_exception:" + type(exc).__name__,
            "acquisition_callback_attempts": fallback_callbacks,
            "http_dispatch_count": dispatches,
            "source_telemetry": {},
            "candidate": None,
            "evidence": {},
            "raw_payload_persistence": "NONE_UNVERIFIED_AFTER_EXCEPTION",
        }, {})

    attempts = {m: len(histories.get(m, [])) for m in ("TWSE", "TPEX", "TAIFEX", "other")}
    retries = {m: max(0, attempts[m] - 1) for m in attempts}
    result["transport_attempt_count"] = attempts
    result["retry_count_by_market"] = retries
    result["retry_count"] = sum(retries.values())
    result["transport_attempt_history"] = histories
    result.update({
        "schema_version": "phase_i_i3_a3_attempt_3_bounded_live_adapter_acceptance.v1",
        "status": "PASS_READY_FOR_INDEPENDENT_REVIEW" if result["A3_decision"] == "PASS" else "HOLD",
        "owner_authority": owner_reference,
        "starting_main": a3.BASELINE,
        "pre_network_commit": sealed_head,
        "pre_network_tree": sealed_tree,
        "acquisition_order": list(ACQUISITION_ORDER),
        "max_http_dispatches_per_market": MAX_HTTP_DISPATCHES_PER_MARKET,
        "max_retries_per_market": MAX_RETRIES_PER_MARKET,
        "fallback_endpoint_allowed": False,
        "reservation": {"path": RESERVATION, "sha256": reservation_sha},
        "consumed_latch": {"path": CONSUMED, "sha256": consumed_sha},
        "candidate_file_hashes": a3.candidate_hashes(),
        "immutable_hashes": a3.HASHES,
        "sealed_code_hashes": sealed_hashes(),
        "security_master": security_master,
        "targets": targets,
        "candidate_reached": result.get("candidate") is not None,
        "A3_independently_accepted": False,
        "production_activation_authorized": False,
        "public_v3_integration_authorized": False,
        "A4_authorized": False,
        "merge_authorized": False,
    })
    if result["A3_decision"] == "PASS":
        for relative, body in artifacts.items():
            a3.write_once(f"{ARTIFACT_ROOT}/{relative}", body)
        result["normalized_artifact_root"] = ARTIFACT_ROOT
    a3.write_once(OUTCOME if result["A3_decision"] == "PASS" else HOLD, result)
    require(a3.candidate_hashes() == reservation["candidate_file_hashes"]
            and a3.immutable_hashes() == a3.HASHES, "post_attempt_3_immutable_hash_drift")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--confirm-single-authorization-bounded-multi-dispatch", action="store_true")
    parser.add_argument("--owner-authorization-reference", required=True)
    parser.add_argument("--sealed-pre-network-head", required=True)
    args = parser.parse_args()
    require(args.live and args.confirm_single_authorization_bounded_multi_dispatch,
            "attempt_3_live_confirmation_required")
    result = live(args.sealed_pre_network_head, args.owner_authorization_reference)
    print(json.dumps({
        "A3_decision": result["A3_decision"],
        "acquisition_callback_attempts": result["acquisition_callback_attempts"],
        "transport_attempt_count": result["transport_attempt_count"],
        "http_dispatch_count": result["http_dispatch_count"],
        "retry_count_by_market": result["retry_count_by_market"],
        "failure_code": result.get("failure_code"),
    }, sort_keys=True))


if __name__ == "__main__":
    main()