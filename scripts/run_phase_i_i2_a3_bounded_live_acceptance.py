"""Phase I2 A3 acceptance-only governed runner with an explicitly re-armed CLI."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import sys
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft7Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.m8r_05b_02.authorization import build_execution_authorization
from scripts.m8r_05b_02.consumption_binding import build_consumption_binding
from scripts.m8r_05b_03.canonical import sha256_json
from scripts.m8r_05b_03.dispatch import RuntimeAdapterRegistration, RuntimeAdapterRegistry
from scripts.m8r_05b_03.preflight import build_orchestrator_preflight, validate_preflight_hashes
from scripts.m8r_05b_03.orchestrator import execute_controlled_plan
from scripts.m8r_05b_03.request_projection import relative_operation_request_path
from scripts.m8r_filesystem_safety import atomic_write_bytes
from scripts.m8r_06_01c2_mode_a_security_master_loader import load_active_mode_a_security_master
from scripts.m8r_06_02_mode_b1_preview import build_mode_b1_preview_package, load_planning_authorities
from scripts.m8r_05c.artifact_loader import load_projection_inputs
from scripts.m8r_05c.audit_package_builder import build_audit_package
from scripts.m8r_05c.citation_builder import _build_citation_id, build_citation_index
from scripts.m8r_05c.lineage_resolver import build_lineage_map
from scripts.m8r_05c.result_builder import build_result
from scripts.m8r_05c.errors import ProjectionError
from server.services.phase_i_i2_index_futures_adapters import (
    CAPABILITY_ID, EVIDENCE_SCHEMA, MAX_RESPONSE_BYTES, SOURCE_ENDPOINT,
    normalize_taifex_tx_payload, select_tx_regular_series,
)
from server.services.phase_i_i2_live_acceptance_candidate import (
    acquire_taifex_once,
)

EXECUTOR_ID = "phase_i_i2_index_futures_context_executor"
PRE_NETWORK_AUTHORITY = "USER_CHAT_2026-10-01_PHASE_I_I2_A3_PRE_NETWORK_GOVERNED_RUNNER_CLOSURE"
RESULT_V3 = "unified_market_evidence_result.v3"
AUDIT_V3 = "unified_market_evidence_audit_package.v3"
STAMP = "2026-10-01T00:00:00Z"


class P0Error(RuntimeError):
    pass


def _zulu() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def deterministic_fixture_payload() -> bytes:
    """Small source-shaped payload proving newest-date / nearest-month rules."""
    def row(period: str, *, date: str = "20260929", session: str = "一般", contract: str = "TX"):
        return {
            "Date": date, "Contract": contract, "ContractMonth(Week)": period,
            "Open": "48098", "High": "48194", "Low": "47630", "Last": "47767",
            "Change": "-358", "%": "-0.74%", "Volume": "43812",
            "SettlementPrice": "47781", "OpenInterest": "102023", "BestBid": "47753",
            "BestAsk": "47765", "TradingHalt": "", "TradingSession": session,
        }
    rows = [
        row("202609", date="20260928"), row("202610"), row("202611"), row("202612"),
        row("202610W1"), row("202610/202611"), row("202609", session="盤後"),
        row("202610", contract="MTX"),
    ]
    return json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _target_identity(record: Mapping[str, Any]) -> dict[str, Any]:
    ident = record.get("identity") or {}
    listing = record.get("current_listing") or {}
    cls = record.get("classification") or {}
    return {
        "canonical_target_id": record["canonical_target_id"],
        "isin": ident.get("isin"), "market": listing.get("market"),
        "security_code": ident.get("security_code"),
        "security_name_zh": ident.get("security_name_zh"),
        "security_name_en": ident.get("security_name_en"),
        "instrument_family": cls.get("instrument_family"),
        "instrument_type": cls.get("instrument_type"),
    }


def _authorities(*, live: bool = False) -> tuple[dict[str, Any], dict[str, Any]]:
    authorities = load_planning_authorities("unified_market_evidence_request.v3")
    catalog = copy.deepcopy(authorities["capability_catalog"])
    routing = copy.deepcopy(authorities["routing_matrix"])
    cap = next(x for x in catalog["data_need_capabilities"] if x.get("capability_id") == CAPABILITY_ID)
    route = next(x for x in routing["routes"] if x.get("capability_id") == CAPABILITY_ID)
    cap.update({"support_status": "runtime_executable", "runtime_executable": True,
                "phase_i_activation_state": "bounded_live_acceptance_only"})
    route.update({"runtime_executable": True, "provisional": False,
                  "selected_executor_id": EXECUTOR_ID, "candidate_executor_ids": [EXECUTOR_ID],
                  "routing_status": "resolved", "network_required": True,
                  "batching_scope": "same_source", "blocking_reasons": [],
                  "capability_status_source": "in-memory A3-P0 overlay only; canonical route remains dormant"})
    surfaces = authorities["executor_disposition"].get("surfaces")
    if not isinstance(surfaces, list):
        raise P0Error("executor_disposition_surfaces_missing")
    if any(isinstance(x, dict) and x.get("surface_id") == EXECUTOR_ID for x in surfaces):
        raise P0Error("candidate_surface_already_present")
    surfaces.append({
        "surface_id": EXECUTOR_ID, "path": "server/services/phase_i_i2_live_acceptance_candidate.py",
        "surface_type": "acceptance_only_i2_candidate_executor",
        "current_status": "single-GET Owner-authorized acceptance only" if live else "P0 fake-transport only; live execution disarmed",
        "network_behavior": "one fixed-endpoint acquisition per same_source batch; retry zero" if live else "one injected acquisition per same_source batch; no live delegate",
        "input_contract": "execution_request.v2 index_futures_context / TWSE / approved target",
        "output_contract": EVIDENCE_SCHEMA,
        "approval_boundary": "05B authorization, consumption binding, preflight, execute-once claim",
        "authorization_binding": "operation, executor, capability, market and approved target",
        "single_use_enforced": True, "supported_markets": ["TWSE"],
        "supported_security_types": ["equity"], "supported_capabilities": [CAPABILITY_ID],
        "batching_supported": True, "deterministic": False, "reusable_for_05b": True,
        "reuse_mode": "adapter_required", "disposition": "adapter_required", "blocking_gaps": [],
    })
    authorities["capability_catalog"] = catalog
    authorities["routing_matrix"] = routing
    return authorities, {"capability_catalog": catalog, "routing_matrix": routing}


def _executor_registry_metadata() -> dict[str, Any]:
    return {"schema_version": "m8r_05b_03_executor_registry_metadata.v1", "executors": [{
        "executor_id": EXECUTOR_ID, "capability_id": CAPABILITY_ID, "market": "TWSE",
        "supported_security_types": ["equity"], "expected_evidence_contract": EVIDENCE_SCHEMA,
        "network_required": True, "bounded_execution_supported": True,
        "timeout_seconds": 30, "maximum_result_items": 1,
        "output_policy": "contained_artifact_only",
    }]}


def _operation_result_status(evidence_status: str) -> tuple[str, str | None]:
    """Mirror the accepted I2/A2 evidence-to-operation status contract."""
    if evidence_status in {"complete", "partial", "unavailable"}:
        return "succeeded", None
    if evidence_status in {"source_failed", "binding_failed"}:
        return "failed", evidence_status
    raise P0Error("evidence_status_unrecognized")


def _make_batch_adapter(fake_transport, *, governed_timestamp: str, live: bool = False):
    acquisitions = []

    def batch(requests, context):
        if len(acquisitions) >= 1:
            raise P0Error("same_source_second_acquisition_denied")
        if context.mode != "execute-approved" or len(requests) != 2:
            raise P0Error("acceptance_batch_scope_invalid")
        for request in requests:
            if (request.get("capability_id"), request.get("executor_id"), request.get("market"),
                    request.get("network_authorized"), request.get("timeout_seconds"),
                    request.get("maximum_records"), request.get("parameters")) != (
                CAPABILITY_ID, EXECUTOR_ID, "TWSE", True, 30, 1, {}
            ):
                raise P0Error("execution_request_scope_invalid")
        acquired = acquire_taifex_once(transport=fake_transport,
            clock=None if live else lambda: datetime(2026, 10, 1, tzinfo=timezone.utc))
        acquisitions.append(acquired)
        from server.services.phase_i_i2_index_futures_adapters import decode_taifex_payload
        rows, error = decode_taifex_payload(acquired.body)
        if error or rows is None:
            raise P0Error(error or "source_failed:decode")
        results = []
        from scripts.m8r_05b_03.canonical import canonical_json
        from scripts.m8r_05c.citation_builder import _build_citation_id
        for request in requests:
            operation_id = request["operation_id"]
            rel = f"evidence/phase_i/i2/{operation_id}.json"
            evidence = normalize_taifex_tx_payload(
                rows, governed_retrieved_at=governed_timestamp, fmtqik_benchmark_date=None,
                citation_ids=[_build_citation_id(operation_id, rel)],
                transport={"http_status": acquired.http_status, "content_type": acquired.content_type,
                           "response_byte_count": acquired.response_byte_count,
                           "response_sha256": acquired.response_sha256, "retrieved_at": acquired.retrieved_at,
                           "get_count": 1, "retry_count": 0, "raw_payload_persisted": False},
            )
            operation_status, error_code = _operation_result_status(evidence["status"])
            payload = canonical_json(evidence).encode("utf-8")
            atomic_write_bytes(context.governed_output_root, rel, payload, allow_overwrite=False)
            artifact = {"relative_path": rel, "sha256": hashlib.sha256(payload).hexdigest(),
                        "schema_version": EVIDENCE_SCHEMA, "byte_size": len(payload),
                        "item_count": 1, "evidence_contract": EVIDENCE_SCHEMA,
                        "artifact_role": "primary_evidence"}
            results.append({
                "schema_version": "unified_market_evidence_operation_result.v2",
                "operation_id": operation_id, "execution_request_id": request["execution_request_id"],
                "execution_request_hash": request["execution_request_hash"],
                "executor_id": EXECUTOR_ID, "capability_id": CAPABILITY_ID,
                "evidence_contract": EVIDENCE_SCHEMA, "status": operation_status, "error_code": error_code,
                "result_item_count": 1, "evidence_artifacts": [artifact],
                "warnings": list(evidence.get("caveats", [])),
            })
        return results

    return batch, acquisitions


def run_fake_governed_acceptance(*, output_root: Path, fake_transport) -> dict[str, Any]:
    """Run real 05B/05C orchestration using only an injected fake transport."""
    return _run_governed_acceptance(output_root=output_root, fake_transport=fake_transport)


def _run_governed_acceptance(*, output_root: Path, fake_transport,
        owner_authority: str = PRE_NETWORK_AUTHORITY, execution_timestamp: str = STAMP,
        live: bool = False) -> dict[str, Any]:
    """The reviewed P0 chain; live mode changes only delegate, authority and time."""
    import server.services.unified_mode_a as mode_a
    import server.services.unified_mode_b2 as mode_b2
    import server.services.unified_mode_c as mode_c
    from scripts.m8r_05b_02.canonical import sha256_json as _sha256_json
    from scripts.m8r_05b_02.authorization import build_execution_authorization
    from scripts.m8r_05b_02.consumption_binding import build_consumption_binding
    from scripts.m8r_05b_03.canonical import sha256_json

    output_root.mkdir(parents=True, exist_ok=False)
    control_root = output_root / "control"
    control_root.mkdir()
    run_id = ("a3-live-" if live else "a3-p0-") + uuid.uuid4().hex[:12]
    identity_runtime = load_active_mode_a_security_master(security_master_root=ROOT / "data" / "security_master")
    if identity_runtime.validation.get("valid") is not True:
        raise P0Error("security_master_invalid")
    by_id = identity_runtime.lookup["by_canonical"]
    selected_records = [by_id[x] for x in ("TWSE:1101", "TWSE:1102")]
    targets = []
    for record in selected_records:
        cls = record.get("classification") or {}
        if (record.get("canonical_target_id"), cls.get("market"), cls.get("instrument_family"), cls.get("instrument_type"),
                (record.get("execution_eligibility") or {}).get("status")) not in (
            ("TWSE:1101", "TWSE", "company_share", "common_share", "allowed"),
            ("TWSE:1102", "TWSE", "company_share", "common_share", "allowed"),
        ):
            raise P0Error("security_master_target_scope_invalid")
        targets.append(_target_identity(record))
    request = {
        "schema_version": "unified_market_evidence_request.v3", "request_id": run_id,
        "targets": [{"input": target["security_code"], "market_hint": "TWSE",
                     "resolution_requirement": "exact", "client_target_reference": target["canonical_target_id"]}
                    for target in targets],
        "data_needs": [{"type": CAPABILITY_ID, "priority": "required", "parameters": {}}],
        "execution_mode": "execute",
        "response_preferences": {"include_citations": True, "include_currentness": True,
            "include_caveats": True, "include_audit_reference": True},
    }
    authorities, overlay = _authorities(live=live)
    overlay_path = output_root / "acceptance_only_catalog_overlay.json"
    overlay_path.write_text(json.dumps(overlay["capability_catalog"], ensure_ascii=False, sort_keys=True, indent=2)+"\n", encoding="utf-8")
    overlay_record_path = output_root / "acceptance_only_authority_overlay.json"
    overlay_record_path.write_text(json.dumps(overlay, ensure_ascii=False, sort_keys=True, indent=2)+"\n", encoding="utf-8")
    overlay_hash = hashlib.sha256(overlay_record_path.read_bytes()).hexdigest()
    old_catalog_paths = mode_a.REQUEST_CAPABILITY_CATALOG_PATHS
    old_security_master_getter = mode_a.get_production_mode_a_security_master
    old_control_root = mode_b2.CONTROL_ROOT
    old_mode_c_root = mode_c.CONTROL_ROOT
    old_env = os.environ.get("TW_MARKET_SECURITY_MASTER_ROOT")
    mode_a.REQUEST_CAPABILITY_CATALOG_PATHS = dict(old_catalog_paths)
    mode_a.REQUEST_CAPABILITY_CATALOG_PATHS["unified_market_evidence_request.v3"] = overlay_path
    mode_b2.CONTROL_ROOT = control_root.resolve()
    mode_c.CONTROL_ROOT = control_root.resolve()
    os.environ["TW_MARKET_SECURITY_MASTER_ROOT"] = str(ROOT / "data" / "security_master")
    mode_a.get_production_mode_a_security_master = lambda pointer_path=None: identity_runtime
    try:
        from server.services.unified_mode_a import validate_mode_a_request
        f3 = validate_mode_a_request(request)
        if f3.get("validation_status") != "valid" or len(f3.get("target_results", [])) != 2:
            raise P0Error("mode_a_exact_target_resolution_failed")
        authorities.update(overlay)
        from scripts.m8r_06_02_mode_b1_preview import build_mode_b1_preview_package
        preview_pkg = build_mode_b1_preview_package(request, f3, identity_runtime,
            planning_timestamp=execution_timestamp, authorities=authorities)
        preview, plan = preview_pkg.get("preview"), preview_pkg.get("orchestration_plan")
        if not isinstance(preview, dict) or preview.get("status") != "ready_for_confirmation" or not isinstance(plan, dict):
            raise P0Error("acceptance_overlay_plan_not_executable")
        operations, groups = plan.get("operations", []), plan.get("batch_groups", [])
        if (len(operations), len(groups), plan.get("accounting", {}).get("network_request_estimate")) != (2, 1, 1):
            raise P0Error("exact_two_operation_same_source_plan_required")
        if any(op.get("executor_id") != EXECUTOR_ID or op.get("operation_status") != "executable_pending_approval" for op in operations):
            raise P0Error("planned_operation_authority_mismatch")
        registry_json = _executor_registry_metadata()
        decision_at = execution_timestamp
        expires_at = (datetime.fromisoformat(decision_at.replace("Z", "+00:00")) + timedelta(minutes=15)).isoformat().replace("+00:00", "Z")
        decision = {"decision": "approved", "decision_reason": "Owner-authorized single-GET bounded live acceptance" if live else "Owner-authorized A3-P0 fake-transport proof only",
            "owner_identity_reference": "USER_CHAT_OWNER", "owner_review_reference": owner_authority,
            "reviewed_at": decision_at, "issued_at": decision_at, "expires_at": expires_at,
            "single_use": True, "replay_policy": "deny_replay", "maximum_use_count": 1,
            "approval_scope_mode": "whole_plan_executable_scope", "approved_operation_ids": [],
            "approved_batch_group_ids": [], "approved_batch_membership": {}}
        authorization = build_execution_authorization(plan, decision)
        consumption_binding = build_consumption_binding(authorization)
        unused_state = {"authorization_id": authorization["authorization_id"],
            "authorization_hash": authorization["authorization_hash"],
            "consumption_binding_id": consumption_binding["consumption_binding_id"],
            "consumption_binding_hash": consumption_binding["consumption_binding_hash"],
            "registry_contract_version": "m8r_05b_03.v1", "state": "unused"}
        package_root = control_root / authorization["authorization_id"]
        package_root.mkdir()
        preflight = build_orchestrator_preflight(plan, authorization, consumption_binding,
            supplied_consumption_state=unused_state, evaluation_timestamp=decision_at,
            executor_registry_metadata=registry_json, output_root=str(package_root))
        validate_preflight_hashes(preflight)
        reqs = preflight.get("bounded_execution_requests", [])
        if len(reqs) != 2 or any(x.get("schema_version") != "unified_market_evidence_execution_request.v2" for x in reqs):
            raise P0Error("i2_execution_request_v2_preflight_failed")
        import server.services.unified_mode_b2 as m2
        control_paths = m2._write_control_package(package_root, {
            "request": request, "plan": plan, "authorization": authorization,
            "consumption_binding": consumption_binding, "unused_consumption_state": unused_state,
            "preflight": preflight,
        })
        batch_adapter, acquisitions = _make_batch_adapter(fake_transport, governed_timestamp=execution_timestamp, live=live)
        reg = RuntimeAdapterRegistration(EXECUTOR_ID, CAPABILITY_ID, "TWSE", ("equity",), EVIDENCE_SCHEMA,
            True, True, 30, 1, "contained_artifact_only",
            adapter=lambda req, ctx: (_ for _ in ()).throw(P0Error("single-operation-route_forbidden")),
            batch_adapter=batch_adapter, fake_adapter=False)
        runtime_registry = RuntimeAdapterRegistry([reg])
        execution = execute_controlled_plan(plan, authorization, consumption_binding,
            supplied_consumption_state=unused_state, accepted_preflight=preflight,
            evaluation_timestamp=decision_at, claim_created_at=decision_at, finalized_at=decision_at,
            executor_registry_metadata=registry_json, runtime_adapter_registry=runtime_registry,
            output_root=str(package_root), mode="execute-approved", confirm_execution=True,
            operator_confirmation_reference=owner_authority, confirm_network_execution=True)
        outcomes = execution.get("dispatch_outcomes", [])
        failed_count = sum(item.get("status") == "failed" for item in outcomes)
        expected_claim_state = (
            "consumed_success" if failed_count == 0 else
            "consumed_failed" if failed_count == len(operations) else
            "consumed_partial"
        )
        if execution.get("consumption_state") != expected_claim_state or execution.get("claim_record", {}).get("attempt_count") != 1:
            raise P0Error("execute_once_fake_transport_claim_failed")
        if len(outcomes) != 2 or len(acquisitions) != 1:
            raise P0Error("same_source_fake_acquisition_count_invalid")
        from scripts.m8r_05b_03.errors import OrchestrationError
        try:
            execute_controlled_plan(plan, authorization, consumption_binding,
                supplied_consumption_state=unused_state, accepted_preflight=preflight,
                evaluation_timestamp=decision_at, claim_created_at=decision_at, finalized_at=decision_at,
                executor_registry_metadata=registry_json, runtime_adapter_registry=runtime_registry,
                output_root=str(package_root), mode="execute-approved", confirm_execution=True,
                operator_confirmation_reference=owner_authority, confirm_network_execution=True)
        except OrchestrationError:
            replay_denied = True
        else:
            replay_denied = False
        if not replay_denied or len(acquisitions) != 1:
            raise P0Error("execute_once_replay_not_denied_before_transport")
        # Reconstruct 05C from governed control artifacts and the real receipt/bundle.
        claim_path = package_root / execution["claim_relative_path"]
        receipt_path = next((package_root / "receipts").glob("*.json"))
        bundle_path = next((package_root / "bundles").glob("*.json"))
        result_package = mode_c.build_mode_c_result_package({"control_package_id": authorization["authorization_id"]}, output_schema_version=RESULT_V3)
        audit = mode_c.read_mode_c_audit(authorization["authorization_id"], output_schema_version=RESULT_V3)
        result = result_package["canonical_result"]
        inputs = load_projection_inputs(request_path=str(package_root / "control" / "request.json"),
            f3_validation_path=str(package_root / "mode_c" / "f3_validation.json"),
            plan_path=str(package_root / "control" / "plan.json"),
            authorization_path=str(package_root / "control" / "authorization.json"),
            consumption_binding_path=str(package_root / "control" / "consumption_binding.json"),
            claim_path=str(claim_path), receipt_path=str(receipt_path), bundle_path=str(bundle_path),
            artifact_root=str(package_root), calculated_at=decision_at, calculated_at_source="receipt.finalized_at")
        lineage = build_lineage_map(inputs)
        citations = build_citation_index(lineage, inputs.bundle, RESULT_V3)
        if result != build_result(inputs, output_schema_version=RESULT_V3):
            raise P0Error("result_v3_replay_mismatch")
        replay_audit = build_audit_package(result, inputs, citations, result_package["canonical_result_reference"], output_schema_version=AUDIT_V3)
        if replay_audit != audit:
            raise P0Error("audit_v3_replay_mismatch")
        Draft7Validator(json.loads((ROOT / "schemas/unified_market_evidence_result.v3.schema.json").read_text(encoding="utf-8")), format_checker=FormatChecker()).validate(result)
        Draft7Validator(json.loads((ROOT / "schemas/unified_market_evidence_audit_package.v3.schema.json").read_text(encoding="utf-8")), format_checker=FormatChecker()).validate(audit)
        evidence_objects = []
        operation_evidence = {}
        for operation_result in execution["dispatch_outcomes"]:
            artifacts = operation_result.get("evidence_artifacts", [])
            if len(artifacts) != 1:
                raise P0Error("operation_evidence_artifact_missing")
            artifact = artifacts[0]
            artifact_bytes = (package_root / artifact["relative_path"]).read_bytes()
            if (len(artifact_bytes) != artifact["byte_size"]
                    or hashlib.sha256(artifact_bytes).hexdigest() != artifact["sha256"]):
                raise P0Error("operation_evidence_artifact_integrity_mismatch")
            operation_evidence[operation_result["operation_id"]] = json.loads(artifact_bytes)
        for target in result["targets"]:
            target_id = target["resolution"]["canonical_target_id"]
            if target_id not in {"TWSE:1101", "TWSE:1102"}:
                raise P0Error("result_i2_target_or_alignment_mismatch")
            binding = lineage.bindings[target_id][CAPABILITY_ID]
            evidence = operation_evidence[binding.operation_id]
            artifact_ref = binding.evidence_artifacts[0]
            rel_path = artifact_ref["relative_path"]
            expected_citation = _build_citation_id(binding.operation_id, rel_path)
            if evidence.get("citation_ids") != [expected_citation] or binding.artifact_objects.get(rel_path) != evidence:
                raise P0Error("evidence_artifact_citation_or_lineage_mismatch")
            if not any(item.get("relative_path") == rel_path
                       and item.get("sha256") == artifact_ref.get("sha256")
                       for item in inputs.bundle.get("artifact_inventory", [])):
                raise P0Error("evidence_bundle_artifact_binding_missing")
            if evidence.get("status") in {"source_failed", "binding_failed"}:
                if binding.status != "failed" or binding.error_code != evidence["status"]:
                    raise P0Error("failed_evidence_lineage_status_mismatch")
                if CAPABILITY_ID in target.get("evidence", {}):
                    raise P0Error("failed_operation_must_not_project_as_successful_typed_binding")
                if not binding.evidence_artifacts or not binding.artifact_objects:
                    raise P0Error("failed_evidence_artifact_lineage_missing")
                if citations.target_need_citations.get(f"{target_id}::{CAPABILITY_ID}") != []:
                    raise P0Error("failed_evidence_must_not_emit_success_citations")
            else:
                if binding.status != "succeeded" or CAPABILITY_ID not in target.get("evidence", {}):
                    raise P0Error("successful_evidence_binding_missing")
                typed = target["evidence"][CAPABILITY_ID]
                expected_alignment = "not_comparable" if evidence["status"] in {"complete", "partial"} else "unavailable"
                if (typed["target"]["canonical_target_id"] != target_id
                        or typed["venue"] != "TAIFEX" or typed["product_code"] != "TX"
                        or typed["status"] != evidence["status"]
                        or typed["alignment_status"] != expected_alignment):
                    raise P0Error("result_i2_target_or_alignment_mismatch")
                if expected_citation not in citations.target_need_citations.get(f"{target_id}::{CAPABILITY_ID}", []):
                    raise P0Error("successful_evidence_citation_index_missing")
            evidence_objects.append(evidence)
        source_hashes = {x["transport"]["response_sha256"] for x in evidence_objects}
        source_counts = {x["transport"]["response_byte_count"] for x in evidence_objects}
        if len(source_hashes) != 1 or len(source_counts) != 1 or any(not x["citation_ids"] for x in evidence_objects):
            raise P0Error("same_source_evidence_lineage_mismatch")
        source = acquisitions[0]
        # Search every generated control/projection byte for full source body.
        raw_absent = all(source.body not in p.read_bytes() for p in output_root.rglob("*") if p.is_file())
        if not raw_absent:
            raise P0Error("raw_fixture_payload_persisted")
        result_path = package_root / result_package["canonical_result_reference"]
        audit_path = package_root / result_package["audit_reference"]
        return {"package_root": package_root, "request": request, "f3": f3, "plan": plan, "authorization": authorization,
            "consumption_binding": consumption_binding, "preflight": preflight, "execution": execution,
            "source_acquisition": source, "overlay_sha256": overlay_hash,
            "selected_targets": targets, "operation_ids": [x["operation_id"] for x in operations],
            "batch_group_ids": [x["batch_group_id"] for x in groups],
            "simulated_source_acquisitions": 0 if live else len(acquisitions), "actual_external_market_calls": len(acquisitions) if live else 0,
            "replay_denied_before_transport": replay_denied,
            "result_v3_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
            "audit_v3_sha256": hashlib.sha256(audit_path.read_bytes()).hexdigest(),
            "lineage": lineage, "citation_index": citations, "result": result, "audit": audit,
            "result_v3_replay": True, "audit_v3_replay": True, "raw_payload_persistence": "NONE",
            "source_selection": select_tx_regular_series(json.loads(source.body)), "overlay": overlay,
            "evidence_objects": evidence_objects, "result_path": result_path, "audit_path": audit_path,
            "security_master_pointer": identity_runtime.pointer}
    finally:
        mode_a.REQUEST_CAPABILITY_CATALOG_PATHS = old_catalog_paths
        mode_a.get_production_mode_a_security_master = old_security_master_getter
        mode_b2.CONTROL_ROOT = old_control_root
        mode_c.CONTROL_ROOT = old_mode_c_root
        if old_env is None:
            os.environ.pop("TW_MARKET_SECURITY_MASTER_ROOT", None)
        else:
            os.environ["TW_MARKET_SECURITY_MASTER_ROOT"] = old_env


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fake-preflight", action="store_true", help="run synthetic TAIFEX fixture through 05B/05C; zero network")
    parser.add_argument("--live", action="store_true", help="requires fresh single-GET Owner authority and guards")
    parser.add_argument("--confirm-single-taifex-get", action="store_true")
    parser.add_argument("--owner-authorization-reference")
    parser.add_argument("--expected-live-runner-head")
    parser.add_argument("--expected-live-runner-tree")
    args = parser.parse_args()
    if args.live:
        from scripts.phase_i_i2_a3_live_support import execute_single_get_acceptance
        try:
            outcome = execute_single_get_acceptance(guard_args=args)
        except (ValueError, P0Error) as exc:
            parser.error(str(exc))
        print(json.dumps(outcome, ensure_ascii=False, sort_keys=True, indent=2))
        return 0 if outcome["status"] == "PASS" else 1
    if not args.fake_preflight:
        parser.error("select --fake-preflight; live execution is not re-armed")
    payload = deterministic_fixture_payload()
    calls = []
    def fake(url, timeout):
        if (url, timeout) != (SOURCE_ENDPOINT, 30) or calls:
            raise P0Error("fake_transport_scope_or_count_invalid")
        calls.append(url)
        return 200, {"Content-Type": "application/octet-stream"}, payload
    with tempfile.TemporaryDirectory(prefix="i2-a3-p0-") as tmp:
        outcome = run_fake_governed_acceptance(output_root=Path(tmp) / "out", fake_transport=fake)
    print(json.dumps({"status": "PASS", "actual_external_market_calls": 0,
        "simulated_source_acquisitions": len(calls), "plan_operations": len(outcome["plan"]["operations"]),
        "batch_groups": len(outcome["plan"]["batch_groups"]), "claim_state": outcome["execution"]["consumption_state"],
        "attempt_count": outcome["execution"]["claim_record"]["attempt_count"],
        "result_v3": "PASS", "audit_v3": "PASS", "raw_payload_persistence": "NONE",
        "live_execution_rearm_required": True}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
