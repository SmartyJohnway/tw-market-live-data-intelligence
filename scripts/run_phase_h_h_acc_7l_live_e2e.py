"""Owner-authorized H-ACC-7L selected-product bounded-live E2E.

Runs the complete governed product chain for the already-active
H1-TPEX-ATTENTION-OPENAPI route:

Request -> Mode A -> B1 preview -> B2 authorization -> execute-once child
-> live TPEx transport -> Result V3 -> Audit V3 -> AI handoff.

The installation-local Security Master is bootstrapped in an ephemeral CI root
from the tracked deterministic identity fixture. Market evidence is NOT a
fixture: execution must use production_transport and the fixed official TPEx
OpenAPI route. No H2/H3 route, promotion, scheduler, polling, or retry loop is
allowed.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "tests" / "fixtures" / "m8r_05a_f3"
TARGET = "TPEX:6488"
TARGET_CODE = "6488"
OWNER_AUTHORIZATION_REFERENCE = "USER_CHAT_2026-09-23_H_ACC_7L_AUTHORIZED"
OUTPUT_VERSION = "unified_market_evidence_result.v3"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return _sha256(path)


def _bootstrap_identity_release(security_root: Path) -> dict[str, Any]:
    from scripts.m8r_05a_f3.security_master_loader import load_f3_verified_security_master
    from scripts.m8r_08g_security_master_releases import (
        activate_qualified_release,
        build_candidate_release,
        qualify_candidate_release,
        release_id_for_now,
    )

    snapshot_path = FIXTURE_ROOT / "verified_security_master_snapshot.json"
    manifest_path = FIXTURE_ROOT / "verified_security_master_snapshot_manifest.json"
    verified = load_f3_verified_security_master(
        snapshot_path, manifest_path, allow_fixture_snapshot=True,
    )
    records = copy.deepcopy(verified.snapshot["records"])
    matched = 0
    for record in records:
        if record.get("canonical_target_id") == TARGET:
            record["execution_eligibility"] = {"status": "allowed", "reason_codes": []}
            matched += 1
    if matched != 1:
        raise RuntimeError("acceptance_identity_target_not_unique")

    release_id = release_id_for_now()
    build_candidate_release(
        root=security_root,
        release_id=release_id,
        records=records,
        source_provenance={
            "source_type": "h_acc_7l_ephemeral_identity_fixture",
            "snapshot_id": verified.snapshot.get("snapshot_id", "m8r_05a_f3_fixture"),
            "producer_skill": {
                "name": "tw-security-master-classifier",
                "skill_version": "h-acc-7l-fixture",
                "skill_contract_hash": hashlib.sha256(
                    (ROOT / "skills/tw-security-master-classifier/SKILL.md").read_bytes()
                ).hexdigest(),
            },
            "source_content_hashes": {
                "fixture_snapshot": hashlib.sha256(snapshot_path.read_bytes()).hexdigest(),
                "fixture_manifest": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
            },
        },
    )
    qualified, diagnostic = qualify_candidate_release(root=security_root, release_id=release_id)
    if qualified is None:
        raise RuntimeError(f"acceptance_identity_qualification_failed:{diagnostic}")
    pointer = activate_qualified_release(root=security_root, release_id=release_id)
    return {"release_id": release_id, "pointer": pointer, "target": TARGET}


def _request() -> dict[str, Any]:
    return {
        "schema_version": "unified_market_evidence_request.v3",
        "request_id": "h-acc-7l-tpex-6488-live",
        "targets": [{
            "input": TARGET_CODE,
            "market_hint": "TPEX",
            "resolution_requirement": "exact",
            "client_target_reference": "h-acc-7l-live-target",
        }],
        "data_needs": [{
            "type": "trading_status_context",
            "priority": "required",
            "parameters": {},
            "client_need_reference": "h-acc-7l-live-h1",
        }],
        "execution_mode": "execute",
        "response_preferences": {
            "include_citations": True,
            "include_currentness": True,
            "include_caveats": True,
            "include_audit_reference": True,
        },
    }


def _json_files(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)).replace("\\", "/"): _sha256(path)
        for path in sorted(root.rglob("*.json"))
        if path.is_file()
    }


def run(output_dir: Path) -> dict[str, Any]:
    if os.environ.get("H_ACC_7L_OWNER_AUTHORIZED") != "YES":
        raise RuntimeError("owner_authorization_environment_missing")
    active_test_seams = sorted(key for key in os.environ if key.startswith("M8R_06_03_TEST_"))
    if active_test_seams:
        raise RuntimeError("live_e2e_test_transport_seam_present:" + ",".join(active_test_seams))

    output_dir.mkdir(parents=True, exist_ok=True)
    installation_root = output_dir / "installation"
    security_root = installation_root / "security_master"
    control_root = installation_root / "control"
    security_root.mkdir(parents=True, exist_ok=True)
    control_root.mkdir(parents=True, exist_ok=True)

    os.environ["TW_MARKET_SECURITY_MASTER_ROOT"] = str(security_root)
    os.environ["M8R_06_03_CONTROL_ROOT"] = str(control_root)

    identity = _bootstrap_identity_release(security_root)

    # Imports occur only after installation-local roots are fixed.
    from server.services.unified_mode_a import validate_mode_a_request
    from server.services.unified_mode_b1 import build_mode_b1_preview
    import server.services.unified_mode_b2 as mode_b2
    import server.services.unified_mode_c as mode_c
    from server.services.unified_mode_b2 import ModeB2Error
    from server.services.unified_mode_b2_execution import execute_mode_b2_once
    from server.services.unified_local_operator_action import LocalOperatorActionError, fetch_market_evidence
    from scripts.m8r_06_01c2_mode_a_security_master_loader import reset_production_mode_a_security_master_for_tests
    from server.unified_mcp.tool_contracts import PREFERRED_REQUEST_SCHEMA_VERSION, build_tool_specs

    # The runner owns a fresh process-local installation root.
    reset_production_mode_a_security_master_for_tests()
    mode_b2.CONTROL_ROOT = control_root
    mode_c.CONTROL_ROOT = control_root

    request = _request()
    validation = validate_mode_a_request(request)
    if validation.get("validation_status") != "valid":
        raise RuntimeError("live_e2e_request_validation_failed")
    resolved = [
        item for item in validation.get("target_results", [])
        if item.get("resolution_status") == "resolved"
    ]
    if len(resolved) != 1 or (resolved[0].get("canonical_identity") or {}).get("canonical_target_id") != TARGET:
        raise RuntimeError("live_e2e_identity_binding_failed")

    preview_package = build_mode_b1_preview(request)
    preview = preview_package.get("preview") or {}
    plan = preview_package.get("orchestration_plan") or {}
    operations = plan.get("operations") or []
    if preview.get("status") != "ready_for_confirmation":
        raise RuntimeError("live_e2e_preview_not_ready")
    if preview.get("bounds", {}).get("estimated_network_calls") != 1:
        raise RuntimeError("live_e2e_call_bound_not_one")
    if plan.get("accounting", {}).get("network_request_estimate") != 1:
        raise RuntimeError("live_e2e_plan_call_bound_not_one")
    if len(operations) != 1:
        raise RuntimeError("live_e2e_operation_count_not_one")
    operation = operations[0]
    if (
        operation.get("capability_id") != "trading_status_context"
        or operation.get("market") != "TPEX"
        or operation.get("executor_id") != "phase_h_h1_tpex_attention_executor"
        or operation.get("operation_status") != "executable_pending_approval"
        or operation.get("network_required") is not True
    ):
        raise RuntimeError("live_e2e_selected_route_mismatch")

    # Negative authorization control: preview alone cannot authorize.
    try:
        mode_b2.build_mode_b2_authorization({"request": request, "confirm_authorization": False})
    except ModeB2Error as exc:
        if exc.code != "authorization_confirmation_required":
            raise
        authorization_denial = exc.code
    else:
        raise RuntimeError("live_e2e_missing_authorization_was_accepted")

    # V3 remains unavailable through the one-shot MCP/local-operator facade.
    try:
        fetch_market_evidence({"request": request})
    except LocalOperatorActionError as exc:
        if exc.code != "phase_h_v3_execution_inactive":
            raise
        mcp_v3_denial = exc.code
    else:
        raise RuntimeError("live_e2e_mcp_v3_unexpectedly_executable")

    authorization = mode_b2.build_mode_b2_authorization({
        "request": request,
        "expected_preview_id": preview["internal_execution_reference"]["preview_id"],
        "expected_plan_id": plan["plan_id"],
        "expected_plan_hash": plan["plan_hash"],
        "confirm_authorization": True,
        "approval_scope_mode": "whole_plan_executable_scope",
        "decision_reason": "H-ACC-7L Owner-authorized selected-product live E2E",
        "owner_review_reference": OWNER_AUTHORIZATION_REFERENCE,
    })
    package = control_root / authorization["control_package_id"]
    preflight = json.loads((package / "control/preflight.json").read_text(encoding="utf-8"))
    bounded_requests = preflight.get("bounded_execution_requests") or []
    if preflight.get("network_required") is not True or len(bounded_requests) != 1:
        raise RuntimeError("live_e2e_preflight_bound_invalid")
    bounded = bounded_requests[0]
    if (
        bounded.get("approved_security_identifiers") != [TARGET]
        or bounded.get("maximum_records") != 1
        or bounded.get("timeout_seconds") != 15
        or bounded.get("network_authorized") is not True
    ):
        raise RuntimeError("live_e2e_execution_request_bound_invalid")

    execution = execute_mode_b2_once({
        "control_package_id": authorization["control_package_id"],
        "confirm_execution": True,
        "operator_confirmation_reference": "h-acc-7l-owner-authorized-live",
        "confirm_network_execution": True,
    })
    if (
        execution.get("transport_mode") != "production_transport"
        or execution.get("test_transport_active") is not False
        or execution.get("external_market_network_attempted") is not True
        or execution.get("external_market_network_executed") is not True
        or execution.get("aggregation_status") != "succeeded"
        or execution.get("operation_statuses") != ["succeeded"]
        or execution.get("consumption_state") != "consumed_success"
    ):
        raise RuntimeError("live_e2e_execution_outcome_invalid")

    evidence_dir = package / "evidence"
    before_replay_hashes = _json_files(evidence_dir)
    if len(before_replay_hashes) != 2:
        raise RuntimeError("live_e2e_unexpected_evidence_artifact_count")

    # Execute-once negative control. The fixed child collapses internal replay
    # details to the public mode_b2_execution_unavailable code.
    try:
        execute_mode_b2_once({
            "control_package_id": authorization["control_package_id"],
            "confirm_execution": True,
            "operator_confirmation_reference": "h-acc-7l-replay-denial-check",
            "confirm_network_execution": True,
        })
    except ModeB2Error as exc:
        if exc.code != "mode_b2_execution_unavailable":
            raise
        replay_denial = exc.code
    else:
        raise RuntimeError("live_e2e_replay_was_not_denied")
    if before_replay_hashes != _json_files(evidence_dir):
        raise RuntimeError("live_e2e_replay_mutated_evidence")

    result_package = mode_c.build_mode_c_result_package(
        {"control_package_id": authorization["control_package_id"]},
        output_schema_version=OUTPUT_VERSION,
    )
    audit = mode_c.read_mode_c_audit(
        authorization["control_package_id"], output_schema_version=OUTPUT_VERSION,
    )
    handoff = mode_c.build_mode_c_ai_handoff(
        authorization["control_package_id"], output_schema_version=OUTPUT_VERSION,
    )
    result = result_package["canonical_result"]
    if result.get("schema_version") != OUTPUT_VERSION:
        raise RuntimeError("live_e2e_result_v3_missing")
    target = result.get("targets", [None])[0]
    typed = ((target or {}).get("evidence") or {}).get("trading_status_context")
    if not isinstance(typed, dict) or typed.get("schema_version") != "trading_status_context_evidence.v1":
        raise RuntimeError("live_e2e_typed_h1_result_missing")
    if (typed.get("target") or {}).get("canonical_target_id") != TARGET:
        raise RuntimeError("live_e2e_result_target_binding_failed")
    coverage = typed.get("coverage") or {}
    if coverage.get("covered_status_types") != ["attention"] or coverage.get("declared_scope_complete") is not False:
        raise RuntimeError("live_e2e_result_coverage_untruthful")

    if audit.get("schema_version") != "unified_market_evidence_audit_package.v3":
        raise RuntimeError("live_e2e_audit_v3_missing")
    if audit.get("authorization_identity", {}).get("authorization_id") != authorization["authorization_id"]:
        raise RuntimeError("live_e2e_audit_authorization_lineage_failed")
    if audit.get("plan_identity", {}).get("plan_id") != plan["plan_id"]:
        raise RuntimeError("live_e2e_audit_plan_lineage_failed")
    source_attempts = (audit.get("phase_h_governance") or {}).get("source_attempts") or []
    if len(source_attempts) != 1:
        raise RuntimeError("live_e2e_source_attempt_count_invalid")
    attempt = source_attempts[0]
    if (
        attempt.get("canonical_target_id") != TARGET
        or attempt.get("market") != "TPEX"
        or attempt.get("activation_state") != "active"
        or attempt.get("source_contract_id") != "tpex_trading_warning_information"
        or attempt.get("outcome") != "succeeded"
    ):
        raise RuntimeError("live_e2e_source_attempt_governance_invalid")
    if not audit.get("citation_to_operation_map"):
        raise RuntimeError("live_e2e_citation_lineage_missing")
    if handoff.get("canonical_result") != result or handoff.get("additional_market_network_executed") is not False:
        raise RuntimeError("live_e2e_handoff_invalid")
    if handoff.get("citation_references") != sorted(
        handoff.get("citation_references", []),
        key=lambda item: tuple(str(item[k]) for k in (
            "citation_id", "canonical_target_id", "capability_id",
            "executor_id", "artifact_relative_path", "artifact_hash",
        )),
    ):
        raise RuntimeError("live_e2e_handoff_citation_order_invalid")

    # Projection/readback must be deterministic and network-free.
    second_projection = mode_c.build_mode_c_result_package(
        {"control_package_id": authorization["control_package_id"]},
        output_schema_version=OUTPUT_VERSION,
    )
    if second_projection.get("materialization") != "existing_verified":
        raise RuntimeError("live_e2e_projection_reverification_failed")
    if second_projection.get("result_hash") != result_package.get("result_hash"):
        raise RuntimeError("live_e2e_projection_hash_changed")

    # Preferred product authority and public MCP surface must remain unchanged.
    if PREFERRED_REQUEST_SCHEMA_VERSION != "unified_market_evidence_request.v2":
        raise RuntimeError("live_e2e_v2_preference_changed")
    tools = [tool.name for tool in build_tool_specs()]
    if tools != [
        "market_describe_capabilities",
        "market_validate_request",
        "market_preview_request",
        "market_read_result",
        "market_export_ai_handoff",
        "market_fetch_evidence",
    ]:
        raise RuntimeError("live_e2e_mcp_surface_changed")

    copies = output_dir / "evidence"
    request_sha = _write_json(copies / "request.json", request)
    validation_sha = _write_json(copies / "validation.json", validation)
    preview_sha = _write_json(copies / "preview.json", preview_package)
    authorization_sha = _write_json(copies / "authorization-summary.json", authorization)
    execution_sha = _write_json(copies / "execution-summary.json", execution)
    result_sha = _write_json(copies / "result.v3.json", result)
    audit_sha = _write_json(copies / "audit.v3.json", audit)
    handoff_sha = _write_json(copies / "handoff.v3.json", handoff)

    claim_files = sorted((package / "claims").glob("*.json"))
    receipt_files = sorted((package / "receipts").glob("*.json"))
    bundle_files = sorted((package / "bundles").glob("*.json"))
    if len(claim_files) != 1 or len(receipt_files) != 1 or len(bundle_files) != 1:
        raise RuntimeError("live_e2e_execution_lineage_artifact_count_invalid")

    report = {
        "schema_version": "phase_h_h_acc_7l_selected_product_live_e2e.v1",
        "status": "PASS",
        "requirement_id": "H0H-E2E-LIVE-001",
        "owner_authorization_reference": OWNER_AUTHORIZATION_REFERENCE,
        "selected_product_slice": {
            "request_schema_version": request["schema_version"],
            "target": TARGET,
            "capabilities": ["trading_status_context"],
            "active_routes": ["H1-TPEX-ATTENTION-OPENAPI"],
            "executor_id": operation["executor_id"],
            "result_schema_version": result["schema_version"],
            "audit_schema_version": audit["schema_version"],
        },
        "identity": {
            "installation_local_release_id": identity["release_id"],
            "bootstrap": "tracked deterministic identity fixture; acceptance-only ephemeral root",
            "canonical_target_id": TARGET,
        },
        "network": {
            "authorized": True,
            "transport_mode": execution["transport_mode"],
            "declared_call_bound": 1,
            "planned_network_requests": plan["accounting"]["network_request_estimate"],
            "bounded_execution_request_count": len(bounded_requests),
            "external_market_network_attempted": execution["external_market_network_attempted"],
            "external_market_network_executed": execution["external_market_network_executed"],
            "route_level_actual_call_count_authority": "H0H-LIVE-001",
            "retry_count": 0,
            "polling": False,
            "scheduler": False,
            "broad_crawl": False,
            "full_market_payload_persisted": False,
        },
        "negative_controls": {
            "authorization_without_confirmation": authorization_denial,
            "mcp_v3_execution": mcp_v3_denial,
            "second_execution": replay_denial,
            "replay_evidence_immutable": True,
        },
        "lineage": {
            "plan_id": plan["plan_id"],
            "plan_hash": plan["plan_hash"],
            "authorization_id": authorization["authorization_id"],
            "authorization_hash": authorization["authorization_hash"],
            "execution_receipt_id": execution["execution_receipt_id"],
            "evidence_bundle_id": execution["evidence_bundle_id"],
            "claim_sha256": _sha256(claim_files[0]),
            "receipt_sha256": _sha256(receipt_files[0]),
            "bundle_sha256": _sha256(bundle_files[0]),
        },
        "output_hashes": {
            "request": request_sha,
            "validation": validation_sha,
            "preview": preview_sha,
            "authorization_summary": authorization_sha,
            "execution_summary": execution_sha,
            "result_v3": result_sha,
            "audit_v3": audit_sha,
            "handoff_v3": handoff_sha,
        },
        "phase_h_truth": {
            "result_status": result.get("status"),
            "coverage_status": typed.get("status"),
            "covered_status_types": coverage.get("covered_status_types"),
            "uncovered_status_types": coverage.get("uncovered_status_types"),
            "declared_scope_complete": coverage.get("declared_scope_complete"),
            "source_attempt": attempt,
        },
        "compatibility": {
            "preferred_request_schema_version": PREFERRED_REQUEST_SCHEMA_VERSION,
            "mcp_tool_count": len(tools),
            "mcp_tools": tools,
            "v3_promotion_performed": False,
            "additional_route_activation_performed": False,
        },
        "rollback": {
            "route_level_rollback_authority": "H0H-ROLL-001",
            "route_level_acceptance_ledger": "docs/governance/phase_h/PHASE_H_H_ACT_H1_TPEX_ATTENTION_ACCEPTANCE_LEDGER.json",
            "rollback_proof_retained": True,
        },
    }
    report_path = output_dir / "H_ACC_7L_SELECTED_PRODUCT_LIVE_E2E_REPORT.json"
    report_sha = _write_json(report_path, report)
    report["report_sha256"] = report_sha
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm-bounded-live", action="store_true")
    parser.add_argument("--output-dir")
    args = parser.parse_args()
    if not args.confirm_bounded_live:
        raise SystemExit("H-ACC-7L live E2E requires --confirm-bounded-live")
    output = Path(args.output_dir) if args.output_dir else Path(tempfile.mkdtemp(prefix="h-acc-7l-"))
    print(json.dumps(run(output), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
