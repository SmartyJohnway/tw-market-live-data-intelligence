"""One-shot A0 Attempt 3 runner. Invoke only under the exact Owner authority."""
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

from scripts import phase_i_i3_a0_attempt_authority as authority
from scripts import phase_i_i3_a0_source_transport as transport
from scripts.m8r_08g_security_master_releases import SECURITY_MASTER_ROOT, load_active_identity_service
from scripts.m8r_filesystem_safety import atomic_write_bytes
from scripts.run_phase_i_i3_a0_preflight import (
    BASELINE,
    BRANCH,
    ENDPOINTS,
    analyze_acquired_payloads,
    analyze_market,
    decode_payload,
    load_adjudication_authority,
    load_mapping,
    official_date,
    unpack,
)

OWNER_AUTHORITY = "USER_CHAT_2026-10-02_PHASE_I_I3_A0_FRESH_ATTEMPT_3_FINAL_SOURCE_TIMING_SYMMETRY_REPROBE"
STARTING_HEAD = "e3c44a0a49da3b92ee3254bc73d41831242ac275"
STARTING_TREE = "e3447f9c2ad17e80e6876d11af9c93299771d75a"
RESERVATION_REL = "docs/governance/phase_i/acceptance_runs/i3-a0-attempt3-authority-reservation.json"
CONSUMED_REL = "docs/governance/phase_i/acceptance_runs/i3-a0-attempt3-authority-consumed.json"
OUTCOME_REL = "docs/governance/phase_i/PHASE_I_I3_A0_ATTEMPT_3_SOURCE_TIMING_SYMMETRY_REPROBE_2026-10-02.json"
P2_REL = "docs/governance/phase_i/PHASE_I_I3_A0_P2_ATTEMPT_2_PROVENANCE_AND_TWSE_TRANSPORT_COMPATIBILITY_CLOSURE_2026-10-02.json"
ATTEMPT2_REL = "docs/governance/phase_i/PHASE_I_I3_A0_ATTEMPT_2_SOURCE_TIMING_SYMMETRY_REPROBE_2026-10-01.json"
ERRATUM_REL = "docs/governance/phase_i/PHASE_I_I3_A0_ATTEMPT_2_PROVENANCE_ERRATUM_2026-10-02.json"
EXPECTED_HISTORICAL = {
    ATTEMPT2_REL: "21cafa9ec4bd351454a47de76d0eba3f562ebeeef0233731d5b256a1052a8d1c",
    ERRATUM_REL: "27a871c177b99d762d244fd411b826896813455fb46900d3f7233261f5742ac4",
}
EXPECTED_P2_SHA = "9e2794ee796a98551ea1a1694f0f687853c04ba1209a192834b2a8d1e6a7ad27"


def _json_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def validate_preflight() -> dict[str, Any]:
    """Fail closed before creating a reservation or doing source I/O."""
    if _git("branch", "--show-current") != BRANCH:
        raise RuntimeError("branch_guard_failed")
    if _git("rev-parse", "HEAD") != STARTING_HEAD or _git("rev-parse", "HEAD^{tree}") != STARTING_TREE:
        raise RuntimeError("reviewed_head_guard_failed")
    if _git("rev-parse", "origin/main") != BASELINE:
        raise RuntimeError("main_guard_failed")
    if _git("diff", "--name-only", "HEAD"):
        raise RuntimeError("tracked_worktree_guard_failed")
    chain = authority.load_reviewed_authority_chain()
    p2_path = ROOT / P2_REL
    p2 = json.loads(p2_path.read_text(encoding="utf-8"))
    if (_sha(p2_path) != EXPECTED_P2_SHA or p2.get("decision") != "P2_PASS"
            or p2.get("attempt_3_ready") is not True):
        raise RuntimeError("p2_readiness_guard_failed")
    for rel, expected in EXPECTED_HISTORICAL.items():
        if _sha(ROOT / rel) != expected:
            raise RuntimeError("historical_evidence_hash_guard_failed")
    mapping = load_mapping()
    adjudication = load_adjudication_authority()
    identity_service, pointer, _release, _manifest = load_active_identity_service(root=SECURITY_MASTER_ROOT)
    targets: dict[str, Any] = {}
    for market, code in (("TWSE", "1101"), ("TPEX", "5347")):
        canonical = f"{market}:{code}"
        resolved = identity_service.resolve(canonical, market_hint=market)
        item = resolved.selected
        classification = (item or {}).get("classification") or {}
        identity = (item or {}).get("identity") or {}
        eligibility = (item or {}).get("execution_eligibility") or {}
        if (resolved.status != "resolved" or resolved.reason_codes != ["exact_listing_id"]
                or classification.get("market") != market
                or classification.get("instrument_family") != "company_share"
                or classification.get("instrument_type") != "common_share"
                or identity.get("security_code") != code
                or eligibility.get("status") != "allowed"):
            raise RuntimeError(f"security_master_target_guard_failed:{canonical}")
        targets[market] = {
            "canonical_target_id": canonical,
            "isin": identity.get("isin"),
            "security_code": code,
            "market": market,
            "instrument_family": classification["instrument_family"],
            "instrument_type": classification["instrument_type"],
            "execution_eligibility": eligibility["status"],
            "resolution_reason": resolved.reason_codes[0],
        }
    return {
        "authority_chain": chain,
        "mapping": mapping,
        "adjudication": adjudication,
        "security_master": {
            "release_id": identity_service.release_id,
            "manifest_sha256": identity_service.manifest_hash,
            "index_sha256": pointer["release_index_sha256"],
        },
        "targets": targets,
        "p2_record_sha256": _sha(p2_path),
    }


def _assert_twse_source_shape(body: bytes, mapping: dict[str, Any]) -> dict[str, Any]:
    root = decode_payload(body)
    fields, rows = unpack("TWSE", root)
    if len(rows) > 5000:
        raise ValueError("root_row_limit_exceeded")
    spec = mapping["markets"]["TWSE"]
    if spec["code_field"] not in fields or spec["date_field"] not in root:
        raise ValueError("required_twse_source_field_absent")
    if root[spec["date_field"]] != "20260930":
        raise ValueError("unexpected_twse_official_date")
    phase_keys = [key for key in [*root.keys(), *fields]
                  if any(marker in key.casefold() for marker in ("phase", "階段", "發布階段", "公布階段"))]
    timing_keys = [key for key in [*root.keys(), *fields]
                   if any(marker in key.casefold() for marker in ("timestamp", "update_time", "publish_time", "時間", "更新時間", "發布時間", "公布時間"))]
    return {"root_type": "object", "top_level_keys": sorted(root), "field_count": len(fields),
            "row_count": len(rows), "source_date": root[spec["date_field"]],
            "publication_phase_fields": phase_keys, "publication_timing_fields": timing_keys}


def _tpex_source_shape(body: bytes, mapping: dict[str, Any]) -> dict[str, Any]:
    root = decode_payload(body)
    fields, rows = unpack("TPEX", root)
    if len(rows) > 5000:
        raise ValueError("root_row_limit_exceeded")
    spec = mapping["markets"]["TPEX"]
    if spec["code_field"] not in fields or spec["date_field"] not in fields:
        raise ValueError("required_tpex_source_field_absent")
    raw_dates = sorted({row[spec["date_field"]] for row in rows})
    normalized_dates = sorted({official_date(value, spec["date_encoding"])
                               for value in raw_dates})
    timing_fields = [key for key in fields
                     if any(marker in key.casefold() for marker in ("timestamp", "update_time", "publish_time", "時間", "更新時間", "發布時間", "公布時間"))]
    return {"root_type": "array", "field_names": fields, "row_count": len(rows),
            "raw_unique_date_values": raw_dates, "normalized_trade_dates": normalized_dates,
            "publication_timing_fields": timing_fields}


def _transport_summary(telemetry: dict[str, Any]) -> dict[str, Any]:
    keys = ("market", "endpoint", "method", "timeout_seconds", "retry_count", "redirect_policy",
            "ssl_policy", "http_status", "content_type", "base_mime", "retrieved_at",
            "response_byte_count", "response_sha256", "error_code", "reason_type",
            "reason_classification", "verify_code", "verify_message", "errno",
            "request_dispatched", "tls_verification_mode")
    return {key: telemetry.get(key) for key in keys if key in telemetry}


def _selected_observation(source: dict[str, Any] | None) -> dict[str, Any] | None:
    if source is None:
        return None
    observation = source["selected_observation"]
    return {"market": source["market"], "security_code": observation["security_code"],
            "trade_date": observation["trade_date"], "unit": observation["unit"],
            **observation["common_core"],
            "source_native_optional": observation["source_native_optional"]}


def run_attempt3(*, reader: Callable = transport.read_once) -> dict[str, Any]:
    preflight = validate_preflight()
    reservation_path = ROOT / RESERVATION_REL
    consumed_path = ROOT / CONSUMED_REL
    outcome_path = ROOT / OUTCOME_REL
    if reservation_path.exists() or consumed_path.exists() or outcome_path.exists():
        raise RuntimeError("attempt3_latch_or_outcome_already_exists")

    reservation = authority.build_reservation(
        owner_authority=OWNER_AUTHORITY, starting_main=BASELINE, branch=BRANCH,
        branch_head=STARTING_HEAD, tree=STARTING_TREE,
        max_gets={"TWSE": 1, "TPEx": 1, "retry": 0},
    )
    reservation["attempt_number"] = 3
    reservation["authority_chain_sha256"] = _sha(authority.AUTHORITY_PATH)
    reservation["p2_record_sha256"] = preflight["p2_record_sha256"]
    reservation["security_master_release_id"] = preflight["security_master"]["release_id"]
    reservation["targets"] = preflight["targets"]
    atomic_write_bytes(ROOT, RESERVATION_REL, _json_bytes(reservation), allow_overwrite=False)

    execution_reference = transport.utc_now()
    consumed = authority.build_consumed_latch(reservation, consumed_at=execution_reference)
    atomic_write_bytes(ROOT, CONSUMED_REL, _json_bytes(consumed), allow_overwrite=False)

    get_counts = {"TWSE": 0, "TPEx": 0, "TAIFEX": 0, "other_market_data": 0}
    telemetry: dict[str, dict[str, Any]] = {}
    summaries: dict[str, Any] = {}
    bodies: dict[str, bytes] = {}
    final_decision = "HOLD"
    semantic_state = "SOURCE_SEMANTICS_NOT_EVALUATED"
    analysis: dict[str, Any] | None = None
    twse_payload_meta: dict[str, Any] | None = None
    tpex_payload_meta: dict[str, Any] | None = None
    twse_result: dict[str, Any] | None = None
    tpex_result: dict[str, Any] | None = None
    failure_stage: str | None = None
    failure_code: str | None = None

    for market, policy in (("TWSE", "compatibility"), ("TPEx", "strict")):
        if market == "TPEx" and ("TWSE" not in bodies or failure_stage is not None):
            break
        source_key = "TWSE" if market == "TWSE" else "TPEX"
        try:
            observation, body = reader(market, policy=policy)
            # The accepted transport catches opener.open failures and returns
            # bounded telemetry; a propagating exception therefore means
            # transport setup failed before an HTTP dispatch.
            get_counts[market] += 1
            observation["request_dispatched"] = True
        except Exception as exc:
            observation, body = ({"market": source_key, "endpoint": ENDPOINTS[source_key],
                                 "method": "GET", "timeout_seconds": 30, "retry_count": 0,
                                 "redirect_policy": "reject", "ssl_policy": policy,
                                 "http_status": None, "content_type": None, "base_mime": None,
                                 "response_byte_count": 0, "response_sha256": None,
                                 "retrieved_at": transport.utc_now(), "request_dispatched": False,
                                 **transport.classify_exception(exc)}, None)
        telemetry[source_key] = _transport_summary(observation)
        if body is None or observation.get("error_code") is not None:
            failure_stage = (("TWSE_TRANSPORT_FAILED" if observation.get("request_dispatched") else "TWSE_TRANSPORT_SETUP_FAILED")
                             if market == "TWSE" else
                             ("TPEX_TRANSPORT_FAILED" if observation.get("request_dispatched") else "TPEX_TRANSPORT_SETUP_FAILED"))
            failure_code = observation.get("error_code") or "source_acquisition_failed"
            if failure_code in {"invalid_json_payload", "unexpected_json_root"}:
                semantic_state = "SOURCE_SCHEMA_FAILED"
                failure_stage = f"{source_key}_SOURCE_SCHEMA_FAILED"
            continue
        try:
            summary = (_assert_twse_source_shape(body, preflight["mapping"]) if market == "TWSE"
                       else _tpex_source_shape(body, preflight["mapping"]))
        except Exception as exc:
            semantic_state = "SOURCE_SCHEMA_FAILED"
            failure_stage = f"{source_key}_SOURCE_SCHEMA_FAILED"
            failure_code = str(exc)[:128]
            telemetry[source_key]["source_shape_error"] = failure_code
            continue
        bodies[source_key] = body
        summaries[source_key] = summary
        if market == "TWSE":
            twse_payload_meta = summary
        else:
            tpex_payload_meta = summary

    # Preserve TWSE analysis even when TPEx acquisition/adjudication cannot pass.
    if "TWSE" in bodies:
        try:
            twse_result = analyze_market("TWSE", bodies["TWSE"], preflight["mapping"]["markets"]["TWSE"])
        except (ValueError, KeyError) as exc:
            semantic_state = "SOURCE_SCHEMA_FAILED"
            failure_stage = failure_stage or "TWSE_SOURCE_SCHEMA_FAILED"
            failure_code = failure_code or str(exc)[:128]

    if len(bodies) == 2:
        try:
            analysis = analyze_acquired_payloads(
                bodies["TWSE"], bodies["TPEX"], preflight["mapping"], preflight["adjudication"]
            )
            semantic_state = "EVALUATED"
            twse_result = analysis.get("sources", {}).get("TWSE", twse_result)
            tpex_result = analysis.get("sources", {}).get("TPEX")
            final_decision = "GO_PASS" if analysis.get("status") == "PASS" else "HOLD"
            if final_decision != "GO_PASS":
                failure_stage = "SOURCE_SEMANTICS_HOLD"
                failure_code = "source_or_semantic_gate_not_passed"
        except Exception as exc:
            semantic_state = "SOURCE_SCHEMA_FAILED"
            failure_stage = "SOURCE_SCHEMA_FAILED"
            failure_code = str(exc)[:128]

    decision_analysis = (analysis or {}).get("dealer_sell_adjudication") or {}
    symmetry = {
        "identity_symmetry": "PASS" if len(preflight["targets"]) == 2 else "FAIL",
        "trade_date_symmetry": {"same": "same_trade_date", "different": "different_trade_date"}.get(
            (analysis or {}).get("trade_date_symmetry"), "NOT_EVALUATED"),
        "unit_symmetry": "PASS" if all((item or {}).get("selected_observation", {}).get("unit") == "share"
                                        for item in (twse_result, tpex_result) if item) and twse_result and tpex_result else "NOT_EVALUATED",
        "participant_semantic_symmetry": "PASS" if final_decision == "GO_PASS" else "NOT_EVALUATED",
        "field_grain_symmetry": "per_security_trade_date" if final_decision == "GO_PASS" else "NOT_EVALUATED",
        "publication_timing_symmetry": "asymmetric_but_representable" if final_decision == "GO_PASS" else "NOT_EVALUATED",
        "transport_symmetry": "not_required_different_governed_tls_policies",
    }
    outcome = {
        "schema_version": "phase_i_i3_a0_attempt_3_source_timing_symmetry_reprobe.v1",
        "owner_authority": OWNER_AUTHORITY,
        "baseline_main": BASELINE,
        "starting_branch_head": STARTING_HEAD,
        "starting_tree": STARTING_TREE,
        "authority_chain_sha256": _sha(authority.AUTHORITY_PATH),
        "reservation": {"path": RESERVATION_REL, "sha256": _sha(reservation_path)},
        "consumed_latch": {"path": CONSUMED_REL, "sha256": _sha(consumed_path)},
        "execution_reference_timestamp": execution_reference,
        "security_master": preflight["security_master"],
        "targets": preflight["targets"],
        "network_budget": {"TWSE_max_get": 1, "TPEx_max_get": 1, "total_max_get": 2, "retry_count": 0},
        "actual_get_counts": get_counts,
        "source_telemetry": telemetry,
        "source_payload_summaries": summaries,
        "source_semantics_state": semantic_state,
        "dealer_sell_adjudication": decision_analysis,
        "institutional_total_invariant": decision_analysis.get("institutional_total_invariant"),
        "whole_dataset_arithmetic": {"TWSE": (twse_result or {}).get("arithmetic"),
                                     "TPEx": (tpex_result or {}).get("arithmetic")},
        "normalized_observations": {
            "TWSE:1101": _selected_observation(twse_result),
            "TPEX:5347": _selected_observation(tpex_result),
        },
        "target_binding": {"TWSE:1101": (twse_result or {}).get("exact_matches", 0),
                           "TPEX:5347": (tpex_result or {}).get("exact_matches", 0)},
        "unit_proof": {"TWSE": (twse_result or {}).get("selected_observation", {}).get("unit"),
                       "TPEx": (tpex_result or {}).get("selected_observation", {}).get("unit")},
        "symmetry_matrix": symmetry,
        "publication_timing": {
            "TWSE_daily_product_1800": "excluding_block_trades",
            "TWSE_daily_product_2000": "including_block_trades",
            "TWSE_publication_phase_in_payload": ("present" if (twse_payload_meta or {}).get("publication_phase_fields") else "absent") if twse_payload_meta else "NOT_EVALUATED",
            "TWSE_publication_timing_fields": (twse_payload_meta or {}).get("publication_timing_fields", []),
            "TPEx_publication_metadata": ("timestamp_fields_present" if (tpex_payload_meta or {}).get("publication_timing_fields") else "only_Date") if tpex_payload_meta else "NOT_EVALUATED",
            "TPEx_publication_timing_fields": (tpex_payload_meta or {}).get("publication_timing_fields", []),
            "TPEx_same_day_finality": "UNRESOLVED",
        },
        "batching": {"TWSE_targets_per_whole_market_get": True,
                     "TPEx_targets_per_whole_market_get": True,
                     "mixed_market_max_unique_gets": 2,
                     "per_target_network_request_required": False},
        "raw_persistence": {"result": "NONE", "raw_bodies_written": False,
                             "temporary_raw_files_written": False,
                             "raw_payload_references_released_after_analysis": True},
        "failure_stage": failure_stage,
        "failure_code": failure_code,
        "final_decision": final_decision,
        "A1_authorized": False,
        "implementation_authorized": False,
        "production_activation_authorized": False,
        "merge_authorized": False,
    }
    bodies.clear()
    body = None
    atomic_write_bytes(ROOT, OUTCOME_REL, _json_bytes(outcome), allow_overwrite=False)
    return outcome


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-authorization-reference", required=True)
    args = parser.parse_args()
    if args.owner_authorization_reference != OWNER_AUTHORITY:
        raise SystemExit("owner_authority_mismatch")
    try:
        result = run_attempt3()
    except Exception as exc:
        # Once the consumed latch exists, a failure is terminal. It is never safe
        # to infer whether a request reached the source after a process error.
        consumed = ROOT / CONSUMED_REL
        if consumed.exists():
            raise SystemExit(f"attempt3_consumed_stop:{type(exc).__name__}") from exc
        raise
    print(json.dumps({"final_decision": result["final_decision"],
                      "actual_get_counts": result["actual_get_counts"],
                      "failure_stage": result["failure_stage"],
                      "outcome_path": OUTCOME_REL}, ensure_ascii=False))
    return 0 if result["final_decision"] == "GO_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
