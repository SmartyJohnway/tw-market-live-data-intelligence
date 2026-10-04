"""Single-use I3-A3 acceptance runner; never registers or activates I3.

The official transport acquires bytes; the unchanged A2-R1 candidate receives
those bytes by injection. Live provenance and candidate transport describe
different layers and are deliberately kept separate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import phase_i_i3_a0_source_transport as transport
from scripts.phase_i_i3_transport_mapping import transport_market_key
from scripts.m8r_08g_security_master_releases import SECURITY_MASTER_ROOT, load_active_identity_service
from scripts.m8r_filesystem_safety import atomic_write_bytes
from scripts.run_phase_i_i3_a0_preflight import PROTECTED
from server.services.phase_i_i3_cash_institutional_flow_offline_candidate import (
    EXECUTOR_ID, run_i3_candidate_offline_batch,
)

OWNER = "USER_CHAT_2026-10-04_PHASE_I_I3_A3_BOUNDED_LIVE_ADAPTER_ACCEPTANCE_AUTHORIZATION"
BASELINE = "dafa5999c63d34d55a4665c6534aa77477448d79"
BRANCH = "phase-i/i3-a0-cash-institutional-flow-preflight"
START_HEAD = "80f6a4d3732562bc7060d512fdb0f533441e1f98"
START_TREE = "992aace0902021a44f5368425a7a735674071459"
PREFIX = "docs/governance/phase_i/"
PRE_NETWORK = PREFIX + "PHASE_I_I3_A3_PRE_NETWORK_RUNNER_CLOSURE_2026-10-04.json"
RESERVATION = PREFIX + "acceptance_runs/i3-a3-live-authority-reservation.json"
CONSUMED = PREFIX + "acceptance_runs/i3-a3-live-authority-consumed.json"
OUTCOME = PREFIX + "PHASE_I_I3_A3_BOUNDED_LIVE_ADAPTER_ACCEPTANCE_2026-10-04.json"
ATTEMPT = PREFIX + "PHASE_I_I3_A3_BOUNDED_LIVE_ADAPTER_ACCEPTANCE_ATTEMPT_2026-10-04.json"
ARTIFACT_ROOT = PREFIX + "acceptance_runs/i3-a3-live"
HASHES = {
    PREFIX + "PHASE_I_I3_A1_CASH_INSTITUTIONAL_FLOW_SOURCE_EVIDENCE_CONTRACT_2026-10-03_FROZEN.json": "4f6c00f8c0ef61bd7c5c55daa81e23cf25ec6335c4fe99ef4c539572419f5428",
    PREFIX + "PHASE_I_I3_A2_DORMANT_OFFLINE_IMPLEMENTATION_CANDIDATE_2026-10-03.json": "122d3317d098bc602fe753b02837bf9b1b7133ba287c45cd8de73383d97300e1",
    PREFIX + "PHASE_I_I3_A2_R1_OPTIONAL_SOURCE_NATIVE_FAILURE_SEMANTICS_CLOSURE_2026-10-03.json": "d4962eddf90fe2cf6e1ed3c231f66dc7e1332d9597c5e8fc886ca85e926b9b12",
    "schemas/cash_institutional_flow_context_evidence.v1.schema.json": "3be9a0ca3cf0e0bb5badb427231d47ce86fdb604ae28cb31582b0f9612c76f7c",
}
CANDIDATE_FILES = (
    "server/services/phase_i_i3_cash_institutional_flow_adapters.py",
    "server/services/phase_i_i3_cash_institutional_flow_offline_candidate.py",
    "schemas/cash_institutional_flow_context_evidence.v1.schema.json",
)
HISTORICAL_RESPONSE_SHA = {
    "TWSE": "b292ec02ee89e3aa951337e0504662fee7ee2d7509628199e6752fa36860453e",
    "TPEX": "2d058996bf67a375e152f381dda1a8610c32cf3ecd1ed31240c89ac7fd020402",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_bytes(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def require(condition: bool, code: str) -> None:
    if not condition:
        raise RuntimeError(code)


def immutable_hashes() -> dict[str, str]:
    actual = {path: sha(ROOT / path) for path in HASHES}
    require(actual == HASHES, "immutable_authority_hash_drift")
    r1 = json.loads((ROOT / list(HASHES)[2]).read_text(encoding="utf-8"))
    require(r1["status"] == "A2_R1_PASS" and r1["A3_ready_for_separate_owner_decision"] is True
            and r1["A3_authorized"] is False, "r1_gate_not_ready")
    return actual


def candidate_hashes() -> dict[str, str]:
    return {path: sha(ROOT / path) for path in CANDIDATE_FILES}


def identity(service, market: str, code: str) -> dict:
    canonical = f"{market}:{code}"
    resolved = service.resolve(canonical, market_hint=market)
    item = resolved.selected or {}
    ident = item.get("identity") or {}
    kind = item.get("classification") or {}
    eligibility = item.get("execution_eligibility") or {}
    require(resolved.status == "resolved" and resolved.reason_codes == ["exact_listing_id"]
            and ident.get("security_code") == code and kind.get("market") == market
            and kind.get("instrument_family") == "company_share"
            and kind.get("instrument_type") == "common_share"
            and eligibility.get("status") == "allowed", f"security_master_target_guard_failed:{canonical}")
    return {"canonical_target_id": canonical, "market": market, "security_code": code,
            "isin": ident.get("isin"), "instrument_family": kind["instrument_family"],
            "instrument_type": kind["instrument_type"], "execution_eligibility": eligibility["status"],
            "resolution_reason": resolved.reason_codes[0]}


def load_targets() -> tuple[dict[str, dict], dict]:
    service, pointer, _release, _manifest = load_active_identity_service(root=SECURITY_MASTER_ROOT)
    targets = {market: identity(service, market, code) for market, code in (("TWSE", "1101"), ("TPEX", "5347"))}
    return targets, {"release_id": service.release_id, "manifest_sha256": service.manifest_hash,
                     "index_sha256": pointer["release_index_sha256"]}


def production_containment() -> None:
    for rel in PROTECTED:
        require((ROOT / rel).read_bytes() == subprocess.check_output(["git", "show", f"{BASELINE}:{rel}"], cwd=ROOT),
                f"production_authority_drift:{rel}")
    from scripts.m8r_06_03_production_adapter import build_production_runtime_adapter_registry
    from server.unified_mcp.tool_contracts import build_tool_specs
    registry = build_production_runtime_adapter_registry()
    require(not registry.routes_for_executor(EXECUTOR_ID)
            and len(registry.routes_for_executor("phase_i_i1_market_state_executor")) == 2
            and len(registry.routes_for_executor("phase_i_i2_index_futures_context_executor")) == 1,
            "production_registry_drift")
    require(len(build_tool_specs()) == 6, "mcp_count_drift")


def original_start_guard() -> None:
    require(git("branch", "--show-current") == BRANCH
            and git("rev-parse", "HEAD") == START_HEAD
            and git("show", "-s", "--format=%T", "HEAD") == START_TREE
            and git("rev-parse", "origin/main") == BASELINE, "reviewed_start_guard_failed")
    require(git("status", "--porcelain") in ("", "?? data/"), "unexpected_worktree_changes")
    pr = json.loads(subprocess.check_output(["gh", "pr", "view", "300", "--json", "state,isDraft,headRefOid"], cwd=ROOT))
    require(pr == {"state": "OPEN", "isDraft": True, "headRefOid": START_HEAD}, "draft_pr_guard_failed")
    require(not any((ROOT / rel).exists() for rel in (RESERVATION, CONSUMED, OUTCOME, ATTEMPT)), "a3_prior_execution_exists")
    immutable_hashes()
    production_containment()
    load_targets()


def target_request(item: dict, number: int) -> dict:
    result = dict(item)
    market = item["market"]
    result["operation_id"] = f"i3a3-{market.lower()}-{item['security_code']}"
    digest = hashlib.sha256(f"{OWNER}:{result['operation_id']}:{number}".encode()).hexdigest()
    result["execution_request_id"] = "umereq-v2-" + digest[:20]
    result["execution_request_hash"] = digest
    return result


def qualified(telemetry: dict, body: bytes | None) -> bool:
    return (body is not None and 0 < len(body) <= transport.MAX_BYTES
            and telemetry.get("http_status") == 200 and telemetry.get("base_mime") == "application/json"
            and telemetry.get("complete_body_received") is True and telemetry.get("error_code") is None
            and telemetry.get("response_byte_count") == len(body)
            and telemetry.get("response_sha256") == hashlib.sha256(body).hexdigest()
            and telemetry.get("retry_count") == 0 and telemetry.get("redirect_policy") == "reject")


def execute_with_acquirer(acquire: Callable[[str], tuple[dict, bytes | None]], targets: dict[str, dict],
                          *, http_dispatch_count: dict[str, int] | None = None) -> tuple[dict, dict[str, bytes]]:
    """One sequential attempt; neither this function nor its return stores raw bodies."""
    attempts = {"TWSE": 0, "TPEX": 0, "TAIFEX": 0, "other": 0}
    telemetry: dict[str, dict] = {}
    bodies: dict[str, bytes] = {}
    dispatches = http_dispatch_count if http_dispatch_count is not None else {key: 0 for key in attempts}
    result: dict[str, Any] = {"acquisition_callback_attempts": attempts,
                              "http_dispatch_count": dispatches, "retry_count": 0, "source_telemetry": telemetry,
                              "candidate": None, "evidence": {}, "A3_decision": "HOLD", "failure_code": None}
    artifacts: dict[str, bytes] = {}
    for market in ("TWSE", "TPEX"):
        attempts[market] += 1
        try:
            observation, body = acquire(market)
        except Exception as exc:
            result["failure_code"] = "acquisition_exception:" + type(exc).__name__
            break
        telemetry[market] = observation
        if not qualified(observation, body):
            result["failure_code"] = "unqualified_acquisition:" + str(observation.get("error_code") or "body_or_telemetry_invalid")[:80]
            break
        bodies[market] = body
    if len(bodies) == 2:
        try:
            inputs = [target_request(targets[market], n) for n, market in enumerate(("TWSE", "TPEX"), 1)]
            candidate = run_i3_candidate_offline_batch(inputs, source_payloads=bodies,
                retrieved_at_by_market={m: telemetry[m]["retrieved_at"] for m in bodies},
                twse_governed_source_date="20260930")
            result["candidate"] = {key: candidate[key] for key in (
                "executor_id", "capability_id", "simulated_source_acquisition_count", "network_calls",
                "retry_count", "market_metrics", "alignment", "artifact_inventory", "operation_results")}
            artifacts = candidate["artifact_bytes"]
            result["evidence"] = {market: json.loads(artifacts[f"evidence/phase_i/i3/i3a3-{market.lower()}-{targets[market]['security_code']}.json"])
                                  for market in ("TWSE", "TPEX")}
            for market in ("TWSE", "TPEX"):
                ev = result["evidence"][market]
                live = telemetry[market]
                require(ev["transport"]["response_sha256"] == live["response_sha256"]
                        and ev["transport"]["response_byte_count"] == live["response_byte_count"],
                        "live_candidate_body_lineage_mismatch")
                require(ev["transport"]["mode"] == "offline_injected_fixture"
                        and ev["transport"]["network_get_count"] == 0
                        and ev["transport"]["retry_count"] == 0
                        and ev["transport"]["raw_payload_persisted"] is False, "candidate_transport_boundary")
            require(candidate["network_calls"] == 0 and candidate["retry_count"] == 0
                    and candidate["simulated_source_acquisition_count"] == 2
                    and all(candidate["market_metrics"][market]["decode_count"] == 1
                            and candidate["market_metrics"][market]["source_prepare_count"] == 1
                            for market in ("TWSE", "TPEX")), "candidate_acquisition_count")
            passes = all(result["evidence"][m]["status"] == "complete"
                         and result["evidence"][m]["unit"] == "share"
                         and result["evidence"][m]["canonical_target_id"] == targets[m]["canonical_target_id"]
                         and result["evidence"][m]["publication_finality"] == "unknown"
                         and result["evidence"][m]["currentness_status"] == "unknown"
                         for m in ("TWSE", "TPEX"))
            passes = passes and result["evidence"]["TWSE"].get("trade_date") == "2026-09-30"
            passes = passes and all(r["status"] == "succeeded" for r in candidate["operation_results"])
            passes = passes and candidate["alignment"]["status"] in ("same_trade_date", "different_trade_date")
            passes = passes and candidate["alignment"]["same_date_implies_simultaneous_publication"] is False
            passes = passes and candidate["alignment"]["numeric_same_session_interpretation_allowed"] is False
            result["A3_decision"] = "PASS" if passes else "HOLD"
            if not passes:
                result["failure_code"] = "candidate_evidence_not_complete_or_invariant_failed"
        except Exception as exc:
            result["failure_code"] = "candidate_exception:" + type(exc).__name__
    serialized = json_bytes(result) + b"".join(artifacts.values())
    require(not any(body in serialized for body in bodies.values()), "raw_source_body_persistence_detected")
    result["raw_payload_persistence"] = "NONE"
    result["historical_response_sha_comparison"] = {
        market: telemetry[market]["response_sha256"] == historical
        for market, historical in HISTORICAL_RESPONSE_SHA.items() if market in telemetry and telemetry[market].get("response_sha256")
    }
    bodies.clear()
    return result, artifacts


def acquire_reviewed_source(canonical_market: str, *, on_http_dispatch: Callable[[], None] | None = None,
                            opener_factory: Callable | None = None) -> tuple[dict, bytes | None]:
    """Translate only at the reviewed fixed-endpoint transport interface."""
    market_key = transport_market_key(canonical_market)
    policy = "compatibility" if canonical_market == "TWSE" else "strict"
    kwargs: dict[str, Any] = {"policy": policy, "on_http_dispatch": on_http_dispatch}
    if opener_factory is not None:
        kwargs["opener_factory"] = opener_factory
    return transport.read_once(market_key, **kwargs)


def final_pre_network_guard(sealed_head: str) -> tuple[dict, dict]:
    require(len(sealed_head) == 40 and git("rev-parse", "HEAD") == sealed_head,
            "sealed_pre_network_head_guard")
    require(git("branch", "--show-current") == BRANCH and git("rev-parse", "origin/main") == BASELINE,
            "branch_or_main_drift")
    require(git("status", "--porcelain") in ("", "?? data/"), "unexpected_worktree_changes")
    require(not any((ROOT / rel).exists() for rel in (RESERVATION, CONSUMED, OUTCOME, ATTEMPT)),
            "single_use_latch_or_outcome_exists")
    pr = json.loads(subprocess.check_output(["gh", "pr", "view", "300", "--json", "state,isDraft"], cwd=ROOT))
    require(pr == {"state": "OPEN", "isDraft": True}, "draft_pr_guard_failed")
    immutable_hashes()
    production_containment()
    closure = json.loads((ROOT / PRE_NETWORK).read_text(encoding="utf-8"))
    require(closure["status"] == "PASS_READY_TO_CONSUME_OWNER_AUTHORITY"
            and closure["owner_authority"] == OWNER
            and closure["candidate_file_hashes"] == candidate_hashes()
            and closure["source_transport_sha256"] == sha(ROOT / "scripts/phase_i_i3_a0_source_transport.py")
            and closure["runner_sha256"] == sha(ROOT / "scripts/run_phase_i_i3_a3_bounded_live_acceptance.py")
            and closure["validator_sha256"] == sha(ROOT / "scripts/validate_phase_i_i3_a3_live_acceptance.py"),
            "pre_network_closure_or_candidate_drift")
    targets, security_master = load_targets()
    require(closure["security_master"] == security_master
            and closure["targets"] == targets and closure["twse_governed_source_date"] == "20260930",
            "pre_network_identity_drift")
    return targets, security_master


def write_once(relative: str, value: dict | bytes) -> str:
    body = json_bytes(value) if isinstance(value, dict) else value
    atomic_write_bytes(ROOT, relative, body, allow_overwrite=False)
    return hashlib.sha256(body).hexdigest()


def live(sealed_head: str, owner_reference: str) -> dict:
    require(owner_reference == OWNER, "fresh_owner_authority_required")
    targets, security_master = final_pre_network_guard(sealed_head)
    sealed_tree = git("show", "-s", "--format=%T", "HEAD")
    reservation = {"schema_version": "phase_i_i3_a3_live_authority_reservation.v1", "gate": "I3-A3",
        "owner_authority": OWNER, "starting_main": BASELINE, "pre_network_commit": sealed_head,
        "pre_network_tree": sealed_tree, "immutable_hashes": HASHES, "candidate_file_hashes": candidate_hashes(),
        "targets": targets, "security_master": security_master,
        "network_budget": {"TWSE": 1, "TPEX": 1, "TAIFEX": 0, "other": 0, "retry": 0},
        "reserved": True, "consumed": False}
    reservation_sha = write_once(RESERVATION, reservation)
    consumed = {"schema_version": "phase_i_i3_a3_live_authority_consumed.v1", "owner_authority": OWNER,
        "reservation_sha256": reservation_sha, "consumed": True, "consumed_before_first_http_attempt": True}
    consumed_sha = write_once(CONSUMED, consumed)
    dispatches = {"TWSE": 0, "TPEX": 0, "TAIFEX": 0, "other": 0}

    def acquire(market: str):
        def observed_dispatch() -> None:
            dispatches[market] += 1
        return acquire_reviewed_source(market, on_http_dispatch=observed_dispatch)

    try:
        result, artifacts = execute_with_acquirer(acquire, targets, http_dispatch_count=dispatches)
    except Exception as exc:
        result, artifacts = ({"A3_decision": "HOLD", "failure_code": "runner_exception:" + type(exc).__name__,
                              "acquisition_callback_attempts": None, "http_dispatch_count": dispatches,
                              "retry_count": 0, "source_telemetry": {},
                              "raw_payload_persistence": "NONE_UNVERIFIED_AFTER_EXCEPTION"}, {})
    result.update({"schema_version": "phase_i_i3_a3_bounded_live_adapter_acceptance.v1",
                   "status": "PASS_READY_FOR_INDEPENDENT_REVIEW" if result["A3_decision"] == "PASS" else "HOLD",
                   "owner_authority": OWNER, "starting_main": BASELINE,
                   "pre_network_commit": sealed_head, "pre_network_tree": sealed_tree,
                   "reservation": {"path": RESERVATION, "sha256": reservation_sha},
                   "consumed_latch": {"path": CONSUMED, "sha256": consumed_sha},
                   "immutable_hashes": HASHES, "candidate_file_hashes": candidate_hashes(),
                   "security_master": security_master, "targets": targets,
                   "A3_independently_accepted": False, "production_activation_authorized": False,
                   "public_v3_integration_authorized": False, "merge_authorized": False})
    if result["A3_decision"] == "PASS":
        for relative, body in artifacts.items():
            write_once(f"{ARTIFACT_ROOT}/{relative}", body)
        result["normalized_artifact_root"] = ARTIFACT_ROOT
    path = OUTCOME if result["A3_decision"] == "PASS" else ATTEMPT
    write_once(path, result)
    require(candidate_hashes() == reservation["candidate_file_hashes"] and immutable_hashes() == HASHES,
            "post_live_immutable_hash_drift")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--confirm-single-use-two-market-gets", action="store_true")
    parser.add_argument("--owner-authorization-reference")
    parser.add_argument("--sealed-pre-network-head")
    args = parser.parse_args()
    require(args.live and args.confirm_single_use_two_market_gets and args.sealed_pre_network_head,
            "live_execution_requires_explicit_confirmation_and_sealed_head")
    result = live(args.sealed_pre_network_head, args.owner_authorization_reference or "")
    print(json.dumps({"A3_decision": result["A3_decision"],
                      "acquisition_callback_attempts": result["acquisition_callback_attempts"],
                      "http_dispatch_count": result["http_dispatch_count"],
                      "failure_code": result.get("failure_code")}, sort_keys=True))


if __name__ == "__main__":
    main()
