"""Single-use, TPEx-only A0 Attempt 4 runner. Live use requires exact Owner reference."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import phase_i_i3_a0_attempt_authority as authority
from scripts import phase_i_i3_a0_future_evidence as future
from scripts import phase_i_i3_a0_source_transport as transport
from scripts.m8r_08g_security_master_releases import SECURITY_MASTER_ROOT, load_active_identity_service
from scripts.m8r_filesystem_safety import atomic_write_bytes
from scripts.run_phase_i_i3_a0_preflight import (
    analyze_market, decode_payload, load_adjudication_authority, load_mapping,
    official_date, unpack, validate_mapping,
)

BASELINE = "dafa5999c63d34d55a4665c6534aa77477448d79"
BRANCH = "phase-i/i3-a0-cash-institutional-flow-preflight"
STARTING_HEAD = "8be2cfe795b10591be564b441a17094df2884d1e"
STARTING_TREE = "24c188f0949008761470fe5d48af74c62fe83b7e"
OWNER = "USER_CHAT_2026-10-03_PHASE_I_I3_A0_FRESH_ATTEMPT_4_TPEX_ONLY_FINAL_COMPOSITE_CLOSURE_AUTHORIZATION"
V3_SHA = "14e1f6eebfbffda74883448895ec4a9ddb3ef54a983f39b9da3d6496a738f5d8"
PLAN_REL = "docs/governance/phase_i/PHASE_I_I3_A0_ATTEMPT_4_READINESS_PLAN_V2_2026-10-03.json"
ATTEMPT3_REL = "docs/governance/phase_i/PHASE_I_I3_A0_ATTEMPT_3_SOURCE_TIMING_SYMMETRY_REPROBE_2026-10-02.json"
ATTEMPT3_SHA = "01d4dffa06fc7a78ecc2b4a510badfac511b6f6078f3578af80bbe5abed9f7a1"
P3_ERRATUM_REL = "docs/governance/phase_i/PHASE_I_I3_A0_ATTEMPT_3_EVIDENCE_ERRATUM_2026-10-03.json"
P3_ERRATUM_SHA = "9f86216243fb4d9885e58d9dd7bb231373d4d222e6e277f6565533e942d37196"
RESERVATION_REL = "docs/governance/phase_i/acceptance_runs/i3-a0-attempt4-authority-reservation.json"
CONSUMED_REL = "docs/governance/phase_i/acceptance_runs/i3-a0-attempt4-authority-consumed.json"
OUTCOME_REL = "docs/governance/phase_i/PHASE_I_I3_A0_ATTEMPT_4_TPEX_ONLY_SOURCE_CLOSURE_2026-10-03.json"
COMPOSITE_REL = "docs/governance/phase_i/PHASE_I_I3_A0_FINAL_COMPOSITE_CLOSURE_2026-10-03.json"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def _json_bytes(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _identity(service, market: str, code: str) -> dict:
    canonical = f"{market}:{code}"
    result = service.resolve(canonical, market_hint=market)
    item = result.selected or {}
    identity = item.get("identity") or {}
    classification = item.get("classification") or {}
    eligibility = item.get("execution_eligibility") or {}
    if (result.status != "resolved" or result.reason_codes != ["exact_listing_id"]
            or identity.get("security_code") != code or classification.get("market") != market
            or classification.get("instrument_family") != "company_share"
            or classification.get("instrument_type") != "common_share"
            or eligibility.get("status") != "allowed"):
        raise RuntimeError(f"security_master_target_guard_failed:{canonical}")
    return {"canonical_target_id": canonical, "market": market, "security_code": code,
            "isin": identity.get("isin"), "instrument_family": classification["instrument_family"],
            "instrument_type": classification["instrument_type"],
            "execution_eligibility": eligibility["status"], "resolution_reason": result.reason_codes[0]}


def preflight() -> dict:
    """Zero-network hard gates, including canonical reconstruction before latch creation."""
    if _git("branch", "--show-current") != BRANCH:
        raise RuntimeError("branch_guard_failed")
    if _git("rev-parse", "HEAD") != STARTING_HEAD or _git("rev-parse", "HEAD^{tree}") != STARTING_TREE:
        raise RuntimeError("reviewed_head_guard_failed")
    if _git("rev-parse", "origin/main") != BASELINE:
        raise RuntimeError("main_guard_failed")
    chain = authority.load_reviewed_authority_chain(version="v3", attempt_number=4)
    if _sha(authority.AUTHORITY_V3_PATH) != V3_SHA:
        raise RuntimeError("authority_v3_hash_guard_failed")
    plan_path = ROOT / PLAN_REL
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    if (_sha(plan_path) != "68a36d26137e91068b881d21559d4981465ae39691545aac222a533b483082bf"
            or plan.get("status") != "NON_EXECUTABLE_CONFIGURATION_ONLY"
            or plan.get("authority_chain_version") != "v3" or plan.get("attempt_4_ready") is not True
            or plan.get("attempt_4_authorized") is not False
            or plan.get("markets") != {"TWSE": {"max_gets": 0}, "TPEx": {"max_gets": 1, "ssl_policy": "strict"}}
            or plan.get("retry") != 0 or plan.get("redirect_policy") != "reject"):
        raise RuntimeError("readiness_plan_guard_failed")
    attempt3_path = ROOT / ATTEMPT3_REL
    erratum_path = ROOT / P3_ERRATUM_REL
    if _sha(attempt3_path) != ATTEMPT3_SHA or _sha(erratum_path) != P3_ERRATUM_SHA:
        raise RuntimeError("attempt3_historical_hash_guard_failed")
    attempt3 = json.loads(attempt3_path.read_text(encoding="utf-8"))
    reconstructed = future.reconstruct_attempt3_twse_canonical_summary(attempt3)
    twse_findings = future.source_findings_from_analyzer_result(
        reconstructed, complete_body_received=True, whole_market_payload_observed=True)
    if (reconstructed["status"] != "PASS" or twse_findings["evaluation_status"] != "EVALUATED"
            or twse_findings["target_binding"] != 1 or twse_findings["unit_proof"] != "share"
            or twse_findings["semantic_status"] != "PASS"
            or twse_findings["batching_observation"] != "PROVEN"
            or twse_findings["normalized_observation"]["trade_date"] != "2026-09-30"):
        raise RuntimeError("twse_reconstruction_guard_failed")
    pinned = plan["twse_reuse"]
    if (pinned["response_sha256"] != transport_sha_from_attempt3(attempt3)
            or pinned["rows"] != reconstructed["row_count"] or pinned["fields"] != reconstructed["field_count"]):
        raise RuntimeError("twse_provenance_guard_failed")
    service, pointer, _release, _manifest = load_active_identity_service(root=SECURITY_MASTER_ROOT)
    targets = {m: _identity(service, m, c) for m, c in (("TWSE", "1101"), ("TPEX", "5347"))}
    reservation = ROOT / RESERVATION_REL
    consumed = ROOT / CONSUMED_REL
    outcome = ROOT / OUTCOME_REL
    composite = ROOT / COMPOSITE_REL
    if any(p.exists() for p in (reservation, consumed, outcome, composite)):
        raise RuntimeError("attempt4_artifact_already_exists")
    mapping = load_mapping()
    adjudication = load_adjudication_authority()
    return {"chain": chain, "plan": plan, "attempt3": attempt3, "twse_summary": reconstructed,
            "twse_findings": twse_findings, "security_master": {"release_id": service.release_id,
            "manifest_sha256": service.manifest_hash, "index_sha256": pointer["release_index_sha256"]},
            "targets": targets, "mapping": mapping, "adjudication_authority": adjudication}


def transport_sha_from_attempt3(record: dict) -> str:
    return record["source_telemetry"]["TWSE"]["response_sha256"]


def _candidate_mapping(mapping: dict, selected: str) -> dict:
    import copy
    resolved = copy.deepcopy(mapping)
    spec = resolved["markets"]["TPEX"]
    spec["required_common_core"]["dealer_total"]["sell_shares"] = [selected]
    spec["mapping_status"] = "RESOLVED_BY_P1_WHOLE_DATASET_ARITHMETIC"
    spec.pop("unresolved_fields", None)
    resolved["mapping_status"] = "RESOLVED_EPHEMERAL"
    return validate_mapping(resolved, require_resolved=True)


def _summarize_findings(value: dict) -> dict:
    return {"evaluation_status": value.get("evaluation_status"), "target_binding": value.get("target_binding"),
            "unit_proof": value.get("unit_proof"), "normalized_observation": value.get("normalized_observation"),
            "whole_dataset_arithmetic": value.get("whole_dataset_arithmetic"),
            "semantic_status": value.get("semantic_status"), "batching_observation": value.get("batching_observation")}


def execute(*, owner_authority: str, reader=transport.read_once) -> dict:
    if owner_authority != OWNER:
        raise RuntimeError("owner_authority_mismatch")
    checks = preflight()
    reservation = authority.build_reservation(owner_authority=OWNER, starting_main=BASELINE,
        branch=BRANCH, branch_head=STARTING_HEAD, tree=STARTING_TREE,
        max_gets={"TWSE": 0, "TPEx": 1, "retry": 0}, version="v3", attempt_number=4)
    atomic_write_bytes(ROOT, RESERVATION_REL, _json_bytes(reservation), allow_overwrite=False)
    reservation_path = ROOT / RESERVATION_REL
    consumed = authority.build_consumed_latch(reservation, consumed_at=transport.utc_now())
    atomic_write_bytes(ROOT, CONSUMED_REL, _json_bytes(consumed), allow_overwrite=False)
    consumed_path = ROOT / CONSUMED_REL

    # Exactly one delegate call; the reviewed transport owns fixed URL, strict TLS,
    # timeout, redirect rejection, response bounds, and zero retries.
    try:
        telemetry, body = reader("TPEx", policy="strict")
    except Exception as exc:
        telemetry = {"market": "TPEx", "endpoint": transport.URLS["TPEx"],
            "method": "GET", "timeout_seconds": 30, "retry_count": 0,
            "redirect_policy": "reject", "ssl_policy": "strict", "http_status": None,
            "base_mime": None, "complete_body_received": False,
            "response_byte_count": 0, "partial_response_byte_count": 0,
            "response_sha256": None, "failure_phase": "transport_dispatch_or_setup",
            **transport.classify_exception(exc)}
        body = None
    if not isinstance(telemetry, dict):
        telemetry = {"error_code": "invalid_transport_telemetry"}
        body = None
    attempted = 1
    tp_source = None
    dealer = None
    tp_summary = None
    binding = None
    final = "HOLD"
    hold_reason = telemetry.get("error_code") or "tpex_acquisition_or_semantic_gate_failed"
    semantic_state = "SOURCE_SEMANTICS_NOT_EVALUATED"
    if (body is not None and telemetry.get("complete_body_received") is True
            and telemetry.get("error_code") is None and telemetry.get("http_status") == 200
            and telemetry.get("base_mime") == "application/json" and telemetry.get("response_sha256")):
        payload = decode_payload(body)
        fields, rows = unpack("TPEX", payload)
        spec = checks["mapping"]["markets"]["TPEX"]
        dates = sorted({official_date(row[spec["date_field"]], spec["date_encoding"]) for row in rows})
        binding = future.binding_findings_from_payload("TPEX", payload, complete_body_received=True,
                                                       whole_market_payload_observed=True)
        if binding["target_binding"] == 1:
            from scripts.run_phase_i_i3_a0_preflight import adjudicate_tpex_dealer_sell
            dealer = adjudicate_tpex_dealer_sell(rows, checks["adjudication_authority"])
            if dealer["selection_status"] == "RESOLVED":
                resolved = _candidate_mapping(checks["mapping"], dealer["selected_candidate"])
                tp_source = analyze_market("TPEX", payload, resolved["markets"]["TPEX"])
                tp_summary = {"root_type": "array", "row_count": len(rows), "field_count": len(fields),
                              "field_names": fields, "raw_unique_date_values": sorted({r[spec["date_field"]] for r in rows}),
                              "normalized_trade_dates": dates,
                              "publication_timing_fields": [k for k in fields if any(x in k.casefold() for x in
                                  ("timestamp", "update_time", "publish_time", "時間", "更新時間", "發布時間", "公布時間"))]}
                semantic_state = "EVALUATED"
                hold_reason = "source_or_composite_gate_not_passed"
                if tp_source["status"] == "PASS":
                    composite = future.compose_analyzer_evidence(checks["twse_summary"], tp_source, dealer,
                        whole_market_observations={"TWSE": True, "TPEx": True},
                        prior_evidence_refs=[ATTEMPT3_REL, P3_ERRATUM_REL])
                    final = "GO_PASS" if composite["semantic_status"] == "PASS" else "HOLD"
                    if final == "GO_PASS":
                        hold_reason = None
                else:
                    hold_reason = "tpex_whole_dataset_arithmetic_failed"
            else:
                semantic_state = "DEALER_ADJUDICATION_FAILED"
                hold_reason = dealer["selection_status"]
        else:
            semantic_state = "TARGET_BINDING_FAILED"
            hold_reason = "tpex_exact_target_binding_not_one"
        payload = None
        body = None
    else:
        body = None

    attempt3 = checks["attempt3"]
    result = {
        "schema_version": "phase_i_i3_a0_attempt_4_tpex_only_source_closure.v1",
        "owner_authority": OWNER, "baseline_main": BASELINE,
        "starting_branch_head": STARTING_HEAD, "starting_tree": STARTING_TREE,
        "authority_v3": {"path": authority.AUTHORITY_V3_PATH.relative_to(ROOT).as_posix(), "sha256": V3_SHA},
        "readiness_plan_v2": {"path": PLAN_REL, "sha256": _sha(ROOT / PLAN_REL)},
        "pre_network_twse_reconstruction": {"source_record_sha256": ATTEMPT3_SHA,
            "source_response_sha256": transport_sha_from_attempt3(attempt3), "status": "PASS",
            "canonical_summary": checks["twse_summary"], "adapter_validation": checks["twse_findings"]},
        "security_master": checks["security_master"], "targets": checks["targets"],
        "reservation": {"path": RESERVATION_REL, "sha256": _sha(reservation_path)},
        "consumed_latch": {"path": CONSUMED_REL, "sha256": _sha(consumed_path)},
        "network_budget": {"TWSE_max_get": 0, "TPEx_max_get": 1, "total_max_get": 1, "retry_count": 0},
        "actual_get_counts": {"TWSE": 0, "TPEx": attempted, "TAIFEX": 0, "other_market_data": 0},
        "tpex_transport": {k: telemetry.get(k) for k in (
            "market", "endpoint", "method", "timeout_seconds", "retry_count", "redirect_policy", "ssl_policy",
            "http_status", "content_type", "base_mime", "retrieved_at", "response_byte_count", "partial_response_byte_count",
            "response_sha256", "complete_body_received", "declared_content_length", "failure_phase", "error_code",
            "reason_type", "reason_classification", "errno", "verify_code", "verify_message") if k in telemetry},
        "tpex_payload_summary": tp_summary,
        "target_binding": binding["target_binding"] if binding else None,
        "target_binding_status": binding["evaluation_status"] if binding else "NOT_EVALUATED",
        "dealer_sell_adjudication": dealer,
        "canonical_tpex_analyzer_result": tp_source,
        "tpex_future_evidence_projection": _summarize_findings(future.source_findings_from_analyzer_result(
            tp_source, complete_body_received=True, whole_market_payload_observed=True)) if tp_source else None,
        "source_semantics_state": semantic_state, "hold_reason": hold_reason,
        "raw_payload_persistence": "NONE", "raw_body_written": False,
        "attempt4_decision": final, "A1_authorized": False,
        "implementation_authorized": False, "production_activation_authorized": False,
        "merge_authorized": False,
    }
    atomic_write_bytes(ROOT, OUTCOME_REL, _json_bytes(result), allow_overwrite=False)
    if body is not None or "payload" in locals():
        body = None
        if "payload" in locals():
            payload = None
    if semantic_state in {"EVALUATED", "TARGET_BINDING_FAILED", "DEALER_ADJUDICATION_FAILED"}:
        composite_record = {"schema_version": "phase_i_i3_a0_final_composite_closure.v1",
            "attempt3_twse_source_sha256": ATTEMPT3_SHA, "attempt3_p3_erratum_sha256": P3_ERRATUM_SHA,
            "attempt4_tpex_source_sha256": _sha(ROOT / OUTCOME_REL), "authority_v3_sha256": V3_SHA,
            "twse_evidence": checks["twse_findings"],
            "tpex_evidence": result["tpex_future_evidence_projection"],
            "target_binding": binding["target_binding"] if binding else None,
            "dealer_sell_adjudication": dealer,
            "trade_date_symmetry": ({"TWSE": "2026-09-30", "TPEx": tp_source["normalized_trade_dates"][0],
                "classification": "same_trade_date" if tp_source["normalized_trade_dates"][0] == "2026-09-30" else "different_trade_date"} if tp_source else "NOT_EVALUATED"),
            "unit_symmetry": "PASS" if tp_source and tp_source["selected_observation"]["unit"] == "share" else "HOLD",
            "participant_semantic_symmetry": "PASS" if final == "GO_PASS" else "HOLD",
            "field_grain_symmetry": "per_security_trade_date" if tp_source else "HOLD",
            "publication_currentness": {"TWSE_payload_phase": "absent", "TPEx_same_day_finality": "UNRESOLVED",
                "publication_finality_representation": "unknown"},
            "batching": ({"TWSE": "PROVEN_BY_ATTEMPT_3", "TPEx": "PROVEN_BY_ATTEMPT_4",
                "mixed_market_observation": composite["mixed_market_observation"],
                "max_unique_acquisitions": 2, "per_target_network_request_required": False}
                if tp_source else {"TWSE": "PROVEN_BY_ATTEMPT_3", "TPEx": "NOT_EVALUATED"}),
            "final_A0_decision": final}
        atomic_write_bytes(ROOT, COMPOSITE_REL, _json_bytes(composite_record), allow_overwrite=False)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-authorization-reference", required=True)
    args = parser.parse_args()
    result = execute(owner_authority=args.owner_authorization_reference)
    print(json.dumps({"attempt4_decision": result["attempt4_decision"],
        "actual_get_counts": result["actual_get_counts"], "failure": result["hold_reason"],
        "outcome_path": OUTCOME_REL}, ensure_ascii=False))
    return 0 if result["attempt4_decision"] == "GO_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
