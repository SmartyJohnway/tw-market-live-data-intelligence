"""Owner-authorized, single-target H3 route-level live acceptance runner.

The runner uses the real Mode A -> B1 -> B2 -> fixed execute-once dispatcher
-> H3 production adapter -> Result V3/Audit V3 path.  Its transport observer
delegates each request to the accepted adapter and retains metadata only.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import uuid
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
TARGET = "TWSE:1423"
EXECUTOR_ID = "phase_h_h3_twse_recent_performance_executor"
SOURCE_ID = "H3-TWSE-DEFAULT-BOUNDED"
RESULT_V3 = "unified_market_evidence_result.v3"
AUDIT_V3 = "unified_market_evidence_audit_package.v3"
LOOKBACK = 20
MAX_UNIQUE_MONTH_GETS = 3
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
TIMEOUT_SECONDS = 15


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json_files(root: Path) -> list[tuple[Path, dict[str, Any]]]:
    found = []
    for path in sorted(root.rglob("*.json")):
        if not path.is_file():
            continue
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(value, dict):
            found.append((path, value))
    return found


def _unique_json(root: Path, predicate, code: str) -> tuple[Path, dict[str, Any]]:
    matches = [(path, value) for path, value in _json_files(root) if predicate(value)]
    if len(matches) != 1:
        raise RuntimeError(code)
    return matches[0]


def _verify_h3_durable_v2_bridge(
    package: Path,
    execution_request: dict[str, Any],
    receipt: dict[str, Any],
    bundle: dict[str, Any],
) -> dict[str, Any]:
    """Verify the accepted V2 -> Receipt V1/Bundle V1 durable bridge.

    Operation Result V2 is an in-process dispatch value. M8R-05B-03 persists
    its per-artifact contract declarations in Bundle V1's artifact inventory,
    while the frozen receipt and operation references retain their established
    contract-neutral shapes.
    """
    from scripts.m8r_05b_03.canonical import sha256_json

    if (
        execution_request.get("schema_version") != "unified_market_evidence_execution_request.v2"
        or not str(execution_request.get("execution_request_id", "")).startswith("umereq-v2-")
        or execution_request.get("operation_id") is None
    ):
        raise RuntimeError("h3_live_execution_request_v2_required")
    operation_id = execution_request["operation_id"]
    execution_request_id = execution_request["execution_request_id"]
    execution_request_hash = execution_request.get("execution_request_hash")
    if receipt.get("schema_version") != "unified_market_evidence_execution_receipt.v1" or receipt.get("overall_status") != "succeeded":
        raise RuntimeError("h3_live_receipt_contract_invalid")
    receipt_matches = [
        item for item in receipt.get("operation_receipts", [])
        if isinstance(item, dict) and item.get("operation_id") == operation_id
    ]
    if len(receipt_matches) != 1:
        raise RuntimeError("h3_live_receipt_operation_lineage_invalid")
    receipt_operation = receipt_matches[0]
    if (
        receipt_operation.get("execution_request_id") != execution_request_id
        or receipt_operation.get("execution_request_hash") != execution_request_hash
        or receipt_operation.get("status") != "succeeded"
    ):
        raise RuntimeError("h3_live_receipt_execution_request_lineage_invalid")
    if bundle.get("schema_version") != "unified_market_evidence_bundle.v1" or bundle.get("overall_status") != "succeeded":
        raise RuntimeError("h3_live_bundle_contract_invalid")
    bundle_matches = [
        item for item in bundle.get("operation_evidence_entries", [])
        if isinstance(item, dict) and item.get("operation_id") == operation_id
    ]
    if len(bundle_matches) != 1 or bundle_matches[0].get("status") != "succeeded":
        raise RuntimeError("h3_live_bundle_operation_lineage_invalid")

    expected_artifacts = {
        f"evidence/phase_h/h3/{operation_id}.json": "recent_performance_evidence.v1",
        f"evidence/phase_h/governance/{operation_id}.json": "phase_h_source_attempt_governance.v1",
    }
    bundle_operation_artifacts = bundle_matches[0].get("artifacts", [])
    receipt_artifacts = receipt_operation.get("evidence_artifacts", [])
    inventory = bundle.get("artifact_inventory", [])
    by_path = {item.get("relative_path"): item for item in inventory if isinstance(item, dict)}
    if (
        len(bundle_operation_artifacts) != 2
        or len(receipt_artifacts) != 2
        or len(inventory) != 2
        or len(by_path) != 2
        or set(by_path) != set(expected_artifacts)
    ):
        raise RuntimeError("h3_live_bundle_artifact_set_invalid")

    verified = {}
    for relative_path, expected_contract in expected_artifacts.items():
        inventory_item = by_path[relative_path]
        bundle_ref = [item for item in bundle_operation_artifacts if item.get("relative_path") == relative_path]
        receipt_ref = [item for item in receipt_artifacts if item.get("relative_path") == relative_path]
        if len(bundle_ref) != 1 or len(receipt_ref) != 1:
            raise RuntimeError("h3_live_artifact_reference_missing")
        if (
            inventory_item.get("schema_version") != expected_contract
            or inventory_item.get("evidence_contract") != expected_contract
        ):
            raise RuntimeError("h3_live_artifact_contract_mismatch")
        for reference in (bundle_ref[0], receipt_ref[0]):
            for field in ("sha256", "schema_version", "byte_size", "item_count"):
                if reference.get(field) != inventory_item.get(field):
                    raise RuntimeError("h3_live_artifact_reference_mismatch")
        artifact_path = package / relative_path
        if not artifact_path.is_file():
            raise RuntimeError("h3_live_artifact_file_missing")
        raw = artifact_path.read_bytes()
        if (
            hashlib.sha256(raw).hexdigest() != inventory_item.get("sha256")
            or len(raw) != inventory_item.get("byte_size")
        ):
            raise RuntimeError("h3_live_artifact_hash_or_size_mismatch")
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeError("h3_live_artifact_json_invalid") from exc
        if value.get("schema_version") != expected_contract:
            raise RuntimeError("h3_live_artifact_schema_mismatch")
        verified[relative_path] = {
            "schema_version": expected_contract,
            "evidence_contract": inventory_item["evidence_contract"],
            "sha256": inventory_item["sha256"],
            "byte_size": inventory_item["byte_size"],
            "item_count": inventory_item["item_count"],
            "content_sha256": hashlib.sha256(raw).hexdigest(),
            "payload_hash": sha256_json(value),
        }
    return verified


def verify_offline_h3_acceptance_package(package: Path) -> dict[str, Any]:
    """Re-evaluate a finalized H3 package without dispatch or network access."""
    from jsonschema import Draft202012Validator, FormatChecker
    from scripts.m8r_05c.artifact_loader import load_projection_inputs
    from scripts.m8r_05c.audit_package_builder import build_audit_package
    from scripts.m8r_05c.citation_builder import _build_citation_id, build_citation_index
    from scripts.m8r_05c.lineage_resolver import build_lineage_map
    from scripts.m8r_05c.result_builder import build_result

    def read(path: Path) -> dict[str, Any]:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError("h3_live_package_json_invalid") from exc
        if not isinstance(value, dict):
            raise RuntimeError("h3_live_package_json_invalid")
        return value

    control = package / "control"
    request = read(control / "request.json")
    preflight = read(control / "preflight.json")
    authorization = read(control / "authorization.json")
    claim_path = next((package / "claims").glob("*.json"), None)
    receipt_path = next((package / "receipts").glob("*.json"), None)
    bundle_path = next((package / "bundles").glob("*.json"), None)
    if claim_path is None or receipt_path is None or bundle_path is None:
        raise RuntimeError("h3_live_finalization_artifact_missing")
    claim, receipt, bundle = read(claim_path), read(receipt_path), read(bundle_path)
    bounded = preflight.get("bounded_execution_requests") or []
    if len(bounded) != 1:
        raise RuntimeError("h3_live_execution_request_count_invalid")
    execution_request = bounded[0]
    if (
        request.get("schema_version") != "unified_market_evidence_request.v3"
        or execution_request.get("parameters") != {"lookback_trading_days": LOOKBACK}
        or execution_request.get("approved_security_identifiers") != [TARGET]
        or execution_request.get("executor_id") != EXECUTOR_ID
        or authorization.get("owner_review_reference") is None
    ):
        raise RuntimeError("h3_live_request_authority_invalid")
    if claim.get("state") != "consumed_success" or claim.get("attempt_count") != 1:
        raise RuntimeError("h3_live_claim_not_successfully_consumed")

    bridge_artifacts = _verify_h3_durable_v2_bridge(package, execution_request, receipt, bundle)
    telemetry = read(package / "h3-live-transport-summary.json")
    month_attempts = telemetry.get("month_attempts") or []
    months = [item.get("month") for item in month_attempts]
    if (
        telemetry.get("schema_version") != "phase_h_h3_live_transport_observation.v1"
        or telemetry.get("canonical_target_id") != TARGET
        or telemetry.get("source_family") != "TWSE_STOCK_DAY_OFFICIAL_WEB"
        or telemetry.get("source_contract_id") != "TWSE_STOCK_DAY_HTML_MONTHLY_V1"
        or telemetry.get("network_request_count") != len(month_attempts)
        or telemetry.get("network_request_count", 0) < 1
        or telemetry.get("network_request_count", 0) > MAX_UNIQUE_MONTH_GETS
        or len(months) != len(set(months))
        or telemetry.get("requested_months") != months
        or telemetry.get("retry_count") != 0
        or any(
            item.get("http_status") != 200
            or item.get("response_byte_count", MAX_RESPONSE_BYTES + 1) > MAX_RESPONSE_BYTES
            or item.get("certificate_verification") is not True
            or item.get("hostname_verification") is not True
            or item.get("ssl_policy") != "compatibility"
            or not isinstance(item.get("response_sha256"), str)
            or len(item["response_sha256"]) != 64
            for item in month_attempts
        )
    ):
        raise RuntimeError("h3_live_transport_evidence_invalid")

    evidence_rel = f"evidence/phase_h/h3/{execution_request['operation_id']}.json"
    sidecar_rel = f"evidence/phase_h/governance/{execution_request['operation_id']}.json"
    evidence_path, sidecar_path = package / evidence_rel, package / sidecar_rel
    evidence, sidecar = read(evidence_path), read(sidecar_path)
    if evidence.get("coverage_status") not in {"complete", "insufficient", "unavailable"}:
        raise RuntimeError("h3_live_evidence_outcome_invalid")
    if (
        evidence.get("schema_version") != "recent_performance_evidence.v1"
        or evidence.get("target", {}).get("canonical_target_id") != TARGET
        or sidecar.get("schema_version") != "phase_h_source_attempt_governance.v1"
        or sidecar.get("evidence_artifact_reference") != evidence_rel
        or sidecar.get("canonical_target_id") != TARGET
        or sidecar.get("capability_id") != "recent_performance"
    ):
        raise RuntimeError("h3_live_evidence_or_sidecar_invalid")

    f3_path = package / "mode_c" / "f3_validation.json"
    if not f3_path.is_file():
        raise RuntimeError("h3_live_f3_validation_missing")
    inputs = load_projection_inputs(
        request_path=str(control / "request.json"), f3_validation_path=str(f3_path),
        plan_path=str(control / "plan.json"), authorization_path=str(control / "authorization.json"),
        consumption_binding_path=str(control / "consumption_binding.json"),
        claim_path=str(claim_path), receipt_path=str(receipt_path), bundle_path=str(bundle_path),
        artifact_root=str(package), calculated_at=receipt["finalized_at"],
        calculated_at_source="receipt.finalized_at",
    )
    lineage = build_lineage_map(inputs)
    citation_index = build_citation_index(lineage, bundle, RESULT_V3)
    binding = lineage.bindings.get(TARGET, {}).get("recent_performance")
    if binding is None or binding.operation_id != execution_request["operation_id"]:
        raise RuntimeError("h3_live_citation_lineage_binding_invalid")
    expected_citation = _build_citation_id(execution_request["operation_id"], evidence_rel)
    typed_ids = evidence.get("citation_ids")
    target_citations = citation_index.target_need_citations.get(f"{TARGET}::recent_performance", [])
    if (
        typed_ids != [expected_citation]
        or expected_citation not in target_citations
        or not set(typed_ids).issubset(citation_index.all_citations)
    ):
        raise RuntimeError("h3_live_citation_lineage_invalid")
    citation = citation_index.all_citations[expected_citation]
    inventory_item = next(item for item in bundle["artifact_inventory"] if item["relative_path"] == evidence_rel)
    if citation.artifact_reference != evidence_rel or citation.normalized_evidence_hash != inventory_item["sha256"]:
        raise RuntimeError("h3_live_primary_citation_reference_invalid")

    result = build_result(inputs, output_schema_version=RESULT_V3)
    audit = build_audit_package(
        result, inputs, citation_index, "ai_context/unified_market_evidence_result.v3.json",
        output_schema_version=AUDIT_V3,
    )
    result_path = package / "ai_context" / "unified_market_evidence_result.v3.json"
    audit_path = package / "audit" / "unified_market_evidence_audit_package.v3.json"
    persisted_result, persisted_audit = read(result_path), read(audit_path)
    for value, schema_name in ((result, RESULT_V3), (audit, AUDIT_V3)):
        schema_path = ROOT / "schemas" / f"{schema_name}.schema.json"
        validator = Draft202012Validator(json.loads(schema_path.read_text(encoding="utf-8")), format_checker=FormatChecker())
        if list(validator.iter_errors(value)):
            raise RuntimeError("h3_live_result_or_audit_schema_invalid")
    if result != persisted_result or audit != persisted_audit:
        raise RuntimeError("h3_live_result_or_audit_replay_mismatch")
    target = next((item for item in result.get("targets", []) if item.get("canonical_identity", {}).get("canonical_target_id") == TARGET), None)
    result_typed = (target or {}).get("evidence", {}).get("recent_performance")
    if not isinstance(result_typed, dict) or result_typed != evidence:
        raise RuntimeError("h3_live_result_typed_evidence_mismatch")
    result_citation = next((item for item in target.get("citations", []) if item.get("citation_id") == expected_citation), None) if target else None
    if (
        result_citation is None
        or result_citation.get("artifact_reference") != evidence_rel
        or result_citation.get("normalized_evidence_hash") != inventory_item["sha256"]
    ):
        raise RuntimeError("h3_live_result_citation_reference_invalid")
    audit_citations = audit.get("citation_to_operation_map", [])
    audit_citation = next((item for item in audit_citations if item.get("citation_id") == expected_citation), None)
    if (
        audit_citation is None
        or audit_citation.get("operation_id") != execution_request["operation_id"]
        or audit_citation.get("artifact_relative_path") != evidence_rel
        or audit_citation.get("artifact_hash") != inventory_item["sha256"]
        or audit_citation.get("canonical_target_id") != TARGET
        or audit_citation.get("requested_data_need") != "recent_performance"
    ):
        raise RuntimeError("h3_live_audit_citation_lineage_invalid")
    return {
        "execution_request_id": execution_request["execution_request_id"],
        "operation_id": execution_request["operation_id"],
        "receipt_id": receipt["execution_receipt_id"],
        "bundle_id": bundle["bundle_id"],
        "bridge_artifacts": bridge_artifacts,
        "transport": telemetry,
        "evidence": evidence,
        "result": result,
        "audit": audit,
        "citation_id": expected_citation,
    }


def _require_owner_authorization_reference(value: str | None) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError("OWNER_AUTHORIZATION_REFERENCE_REQUIRED")
    if value != value.strip() or len(value) > 240:
        # Mode B2 currently bounds this persisted reference to 240 characters.
        # Reject instead of allowing that downstream layer to normalize it.
        raise RuntimeError("OWNER_AUTHORIZATION_REFERENCE_INVALID")
    return value


def _authorization_payload(
    request: dict[str, Any],
    preview: dict[str, Any],
    plan: dict[str, Any],
    owner_authorization_reference: str,
) -> dict[str, Any]:
    reference = _require_owner_authorization_reference(owner_authorization_reference)
    return {
        "request": request,
        "expected_preview_id": preview["internal_execution_reference"]["preview_id"],
        "expected_plan_id": plan["plan_id"],
        "expected_plan_hash": plan["plan_hash"],
        "confirm_authorization": True,
        "approval_scope_mode": "whole_plan_executable_scope",
        "decision_reason": "Owner-authorized H0H-LIVE-003 bounded H3 acceptance",
        "owner_review_reference": reference,
    }


def run(owner_authorization_reference: str) -> dict[str, Any]:
    owner_authorization_reference = _require_owner_authorization_reference(
        owner_authorization_reference
    )
    if os.environ.get("H_ACT_H3_OWNER_AUTHORIZED") != "YES":
        raise RuntimeError("owner_authorization_environment_missing")
    test_seams = sorted(key for key in os.environ if key.startswith("M8R_06_03_TEST_"))
    if test_seams:
        raise RuntimeError("test_transport_seam_present:" + ",".join(test_seams))

    security_root = (ROOT / "data" / "security_master").resolve()
    os.environ["TW_MARKET_SECURITY_MASTER_ROOT"] = str(security_root)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    run_root = ROOT / "data" / "phase_h_h3_live_acceptance" / run_id
    control_root = run_root / "control"
    control_root.mkdir(parents=True, exist_ok=False)
    os.environ["M8R_06_03_CONTROL_ROOT"] = str(control_root)
    os.environ["H3_LIVE_ACCEPTANCE_TELEMETRY"] = "YES"

    # Import only after the installation-local roots have been bound.
    from scripts.m8r_08g_security_master_releases import load_active_identity_service
    from scripts.m8r_06_01c2_mode_a_security_master_loader import get_production_mode_a_security_master
    from scripts.m8r_06_03_execute_once import execute_once
    import scripts.m8r_06_03_production_adapter as production_adapter
    import server.services.unified_mode_b2 as mode_b2
    import server.services.unified_mode_c as mode_c
    from server.services.unified_mode_a import validate_mode_a_request
    from server.services.unified_mode_b1 import build_mode_b1_preview
    from server.unified_mcp.tool_contracts import PREFERRED_REQUEST_SCHEMA_VERSION, build_tool_specs

    mode_b2.CONTROL_ROOT = control_root.resolve()
    mode_c.CONTROL_ROOT = control_root.resolve()

    service, pointer, active_release, manifest = load_active_identity_service(root=security_root)
    release_id = pointer.get("release_id")
    if release_id != "security-master-20260926T151841Z":
        raise RuntimeError("security_master_release_binding_failed")
    identity_runtime = get_production_mode_a_security_master()
    identity = identity_runtime.lookup["by_canonical"].get(TARGET)
    if (
        identity_runtime.validation.get("valid") is not True
        or identity is None
        or identity.get("canonical_target_id") != TARGET
        or (identity.get("classification") or {}).get("market") != "TWSE"
        or (identity.get("classification") or {}).get("instrument_family") != "company_share"
        or (identity.get("classification") or {}).get("instrument_type") != "common_share"
        or (identity.get("execution_eligibility") or {}).get("status") != "allowed"
    ):
        raise RuntimeError("security_master_target_authority_failed")

    request = {
        "schema_version": "unified_market_evidence_request.v3",
        "request_id": "h-act-h3-live-" + uuid.uuid4().hex,
        "targets": [{
            "input": "1423",
            "market_hint": "TWSE",
            "resolution_requirement": "exact",
            "client_target_reference": "h-act-h3-live-target",
        }],
        "data_needs": [{
            "type": "recent_performance",
            "priority": "required",
            "parameters": {"lookback_trading_days": LOOKBACK},
            "client_need_reference": "h-act-h3-live-recent-performance",
        }],
        "execution_mode": "execute",
        "response_preferences": {
            "include_citations": True,
            "include_currentness": True,
            "include_caveats": True,
            "include_audit_reference": True,
        },
    }
    if PREFERRED_REQUEST_SCHEMA_VERSION != "unified_market_evidence_request.v3":
        raise RuntimeError("v3_request_preference_changed")
    validation = validate_mode_a_request(request)
    if validation.get("validation_status") != "valid":
        raise RuntimeError("mode_a_production_validation_failed")
    resolved = [item for item in validation.get("target_results", []) if item.get("resolution_status") == "resolved"]
    if len(resolved) != 1 or (resolved[0].get("canonical_identity") or {}).get("canonical_target_id") != TARGET:
        raise RuntimeError("mode_a_target_binding_failed")

    preview_package = build_mode_b1_preview(request)
    preview = preview_package.get("preview") or {}
    plan = preview_package.get("orchestration_plan") or {}
    operations = plan.get("operations") or []
    if preview.get("status") != "ready_for_confirmation" or len(operations) != 1:
        raise RuntimeError("h3_live_preview_not_single_ready_operation")
    operation = operations[0]
    if (
        operation.get("capability_id") != "recent_performance"
        or operation.get("market") != "TWSE"
        or operation.get("executor_id") != EXECUTOR_ID
        or operation.get("operation_status") != "executable_pending_approval"
        or operation.get("network_required") is not True
    ):
        raise RuntimeError("h3_live_selected_route_mismatch")

    authorization = mode_b2.build_mode_b2_authorization(
        _authorization_payload(
            request,
            preview,
            plan,
            owner_authorization_reference,
        )
    )
    package = control_root / authorization["control_package_id"]
    preflight = json.loads((package / "control" / "preflight.json").read_text(encoding="utf-8"))
    bounded = preflight.get("bounded_execution_requests") or []
    if preflight.get("network_required") is not True or len(bounded) != 1:
        raise RuntimeError("h3_live_preflight_bound_invalid")
    execution_request = bounded[0]
    if (
        execution_request.get("schema_version") != "unified_market_evidence_execution_request.v2"
        or execution_request.get("parameters") != {"lookback_trading_days": LOOKBACK}
        or execution_request.get("approved_security_identifiers") != [TARGET]
        or execution_request.get("timeout_seconds") != TIMEOUT_SECONDS
        or execution_request.get("maximum_records") != 1
        or execution_request.get("network_authorized") is not True
    ):
        raise RuntimeError("h3_live_execution_request_bound_invalid")

    real_fetch = production_adapter.fetch_twse_stock_day_month
    observed_results = []

    def observe_and_delegate(**kwargs):
        result = real_fetch(**kwargs)
        observed_results.append(result)
        return result

    # Passive instrumentation: every real call is delegated unchanged to the
    # accepted transport, and only the returned bounded result metadata stays.
    production_adapter.fetch_twse_stock_day_month = observe_and_delegate
    try:
        execution = execute_once(
            authorization["control_package_id"],
            confirm_execution=True,
            operator_confirmation_reference="h-act-h3-owner-bounded-live",
            confirm_network_execution=True,
        )
    finally:
        production_adapter.fetch_twse_stock_day_month = real_fetch

    if (
        execution.get("transport_mode") != "production_transport"
        or execution.get("test_transport_active") is not False
        or execution.get("external_market_network_attempted") is not True
        or execution.get("external_market_network_executed") is not True
        or execution.get("aggregation_status") != "succeeded"
        or execution.get("operation_statuses") != ["succeeded"]
        or execution.get("consumption_state") != "consumed_success"
    ):
        raise RuntimeError("h3_live_execution_outcome_invalid")

    telemetry_path = package / "h3-live-transport-summary.json"
    telemetry = json.loads(telemetry_path.read_text(encoding="utf-8"))
    months = telemetry.get("month_attempts") or []
    requested_months = telemetry.get("requested_months") or []
    actual_months = [item.requested_month for item in observed_results]
    if (
        len(actual_months) > MAX_UNIQUE_MONTH_GETS
        or len(actual_months) != len(set(actual_months))
        or actual_months != requested_months
        or telemetry.get("network_request_count") != len(actual_months)
        or telemetry.get("retry_count") != 0
        or not 1 <= len(months) <= MAX_UNIQUE_MONTH_GETS
        or any(item.get("http_status") != 200 for item in months)
    ):
        raise RuntimeError("h3_live_month_request_accounting_invalid")

    operation_id = execution_request["operation_id"]
    evidence_path = package / "evidence" / "phase_h" / "h3" / f"{operation_id}.json"
    governance_path = package / "evidence" / "phase_h" / "governance" / f"{operation_id}.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    governance = json.loads(governance_path.read_text(encoding="utf-8"))
    if evidence.get("coverage_status") in {"source_failed", "binding_failed"}:
        raise RuntimeError("h3_live_source_or_binding_failure")
    if governance.get("attempts", [{}])[0].get("activation_state") != "active":
        raise RuntimeError("h3_live_governance_sidecar_invalid")

    result_package = mode_c.build_mode_c_result_package(
        {"control_package_id": authorization["control_package_id"]}, output_schema_version=RESULT_V3,
    )
    audit = mode_c.read_mode_c_audit(authorization["control_package_id"], output_schema_version=RESULT_V3)
    handoff = mode_c.build_mode_c_ai_handoff(authorization["control_package_id"], output_schema_version=RESULT_V3)
    result = result_package["canonical_result"]
    if result.get("schema_version") != RESULT_V3 or audit.get("schema_version") != AUDIT_V3:
        raise RuntimeError("h3_live_v3_projection_missing")
    typed = result["targets"][0]["evidence"].get("recent_performance")
    if not isinstance(typed, dict) or typed.get("coverage_status") in {"source_failed", "binding_failed"}:
        raise RuntimeError("h3_live_result_evidence_invalid")
    if audit.get("authorization_identity", {}).get("authorization_id") != authorization["authorization_id"]:
        raise RuntimeError("h3_live_audit_authorization_lineage_failed")
    source_attempts = (audit.get("phase_h_governance") or {}).get("source_attempts") or []
    if len(source_attempts) != 1:
        raise RuntimeError("h3_live_audit_source_attempt_count_invalid")
    attempt = source_attempts[0]
    if (
        attempt.get("canonical_target_id") != TARGET
        or attempt.get("market") != "TWSE"
        or attempt.get("activation_state") != "active"
        or attempt.get("source_contract_id") != "TWSE_STOCK_DAY_HTML_MONTHLY_V1"
        or attempt.get("outcome") != "succeeded"
    ):
        raise RuntimeError("h3_live_audit_governance_lineage_invalid")
    if handoff.get("canonical_result") != result or handoff.get("additional_market_network_executed") is not False:
        raise RuntimeError("h3_live_handoff_invalid")
    offline_verification = verify_offline_h3_acceptance_package(package)
    if (
        offline_verification["operation_id"] != execution_request["operation_id"]
        or offline_verification["execution_request_id"] != execution_request["execution_request_id"]
        or offline_verification["result"] != result
        or offline_verification["audit"] != audit
    ):
        raise RuntimeError("h3_live_offline_final_verification_mismatch")

    receipt_path, receipt = _unique_json(
        package / "receipts",
        lambda value: any(
            isinstance(item, dict)
            and item.get("execution_request_id") == execution_request["execution_request_id"]
            for item in value.get("operation_receipts", [])
        ),
        "h3_live_receipt_lineage_missing",
    )
    bundle_path, bundle = _unique_json(
        package / "bundles",
        lambda value: any(
            isinstance(item, dict)
            and item.get("operation_id") == execution_request.get("operation_id")
            for item in value.get("operation_evidence_entries", [])
        ),
        "h3_live_bundle_lineage_missing",
    )
    receipt_operations = receipt.get("operation_receipts") or []
    matched_receipts = [
        item for item in receipt_operations
        if isinstance(item, dict)
        and item.get("execution_request_id") == execution_request["execution_request_id"]
    ]
    if len(matched_receipts) != 1 or matched_receipts[0].get("execution_request_hash") != execution_request.get("execution_request_hash"):
        raise RuntimeError("h3_live_execution_request_hash_lineage_failed")
    durable_v2_bridge = _verify_h3_durable_v2_bridge(
        package, execution_request, receipt, bundle
    )

    if [tool.name for tool in build_tool_specs()] != [
        "market_describe_capabilities", "market_validate_request", "market_preview_request",
        "market_read_result", "market_export_ai_handoff", "market_fetch_evidence",
    ]:
        raise RuntimeError("mcp_tool_surface_changed")

    baselines = typed.get("baselines") or []
    baseline = next((item for item in baselines if item.get("lookback_trading_days") == LOOKBACK), None)
    return {
        "schema_version": "phase_h_h_act_h3_live_acceptance_run.v1",
        "status": "PASS",
        "requirement_id": "H0H-LIVE-003",
        "owner_authorization_reference": owner_authorization_reference,
        "target": TARGET,
        "source_id": SOURCE_ID,
        "source_family": "TWSE_STOCK_DAY_OFFICIAL_WEB",
        "source_contract_id": "TWSE_STOCK_DAY_HTML_MONTHLY_V1",
        "provider_automation_permission": "NOT_ESTABLISHED_TERMS_CONFLICTED",
        "security_master": {"release_id": release_id, "canonical_target_id": TARGET},
        "planning": {
            "request_schema_version": request["schema_version"],
            "execution_request_schema_version": execution_request["schema_version"],
            "lookback_trading_days": LOOKBACK,
            "executor_id": operation["executor_id"],
            "plan_id": plan["plan_id"],
            "plan_hash": plan["plan_hash"],
            "execution_request_id": execution_request["execution_request_id"],
            "execution_request_hash": execution_request["execution_request_hash"],
            "authorization_id": authorization["authorization_id"],
        },
        "network": {
            "transport_mode": execution["transport_mode"],
            "actual_unique_month_get_count": len(actual_months),
            "requested_months": requested_months,
            "retry_count": 0,
            "polling": False,
            "scheduler": False,
            "persistent_cache": False,
            "history_database": False,
            "raw_html_persisted": False,
            "full_market_crawl": False,
            "months": months,
        },
        "projection": {
            "coverage_status": typed.get("coverage_status"),
            "requested_observations": typed.get("requested_observations"),
            "valid_observation_count": typed.get("valid_observation_count"),
            "governed_end_observation": typed.get("governed_end_observation"),
            "baseline_20d": baseline,
            "observations": typed.get("observations"),
            "citation_ids": typed.get("citation_ids"),
        },
        "lineage": {
            "primary_evidence_sha256": _sha256(evidence_path),
            "governance_sidecar_sha256": _sha256(governance_path),
            "v2_durable_bridge_artifacts": durable_v2_bridge,
            "corrected_offline_acceptance": "PASS",
            "execution_receipt_sha256": _sha256(receipt_path),
            "evidence_bundle_sha256": _sha256(bundle_path),
            "result_v3_sha256": result_package["result_hash"],
            "audit_v3_sha256": _sha256(package / result_package["audit_reference"]),
            "result_status": result.get("status"),
            "audit_schema_version": audit.get("schema_version"),
            "source_attempt": attempt,
        },
        "rollback": {"performed": False, "rehearsal_required_after_live_pass": True},
        "mcp_tool_count": 6,
        "artifacts_root": package.relative_to(ROOT).as_posix(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm-bounded-live", action="store_true")
    parser.add_argument("--owner-authorization-reference", required=True)
    args = parser.parse_args()
    if not args.confirm_bounded_live:
        raise SystemExit("H0H-LIVE-003 requires --confirm-bounded-live")
    print(json.dumps(
        run(args.owner_authorization_reference),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ))


if __name__ == "__main__":
    main()
