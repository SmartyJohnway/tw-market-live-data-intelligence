"""Deterministic, non-production Phase H control-package test transport."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

from scripts.m8r_05b_01.canonical import plan_hash_and_id
from scripts.m8r_05b_01.planner import plan_identity_scope
from scripts.m8r_05b_02.authorization import build_execution_authorization
from scripts.m8r_05b_02.consumption_binding import build_consumption_binding
from scripts.m8r_05b_03.canonical import canonical_json, sha256_json
from scripts.m8r_05b_03.consumption_claim import atomic_claim_authorization
from scripts.m8r_05b_03.dispatch import (
    RuntimeAdapterRegistration,
    RuntimeAdapterRegistry,
    dispatch_prepared,
    prepare_dispatch,
    request_identity,
)
from scripts.m8r_05b_03.evidence_aggregation import aggregate_dispatch_outcomes
from scripts.m8r_05b_03.preflight import build_orchestrator_preflight
from scripts.m8r_05b_03.receipt import finalize_consumption_and_write_receipt
from scripts.m8r_05b_03.registry import ExecutorMetadataRegistry
from scripts.m8r_05c.citation_builder import _build_citation_id
from scripts.m8r_filesystem_safety import safe_destination
from server.services.phase_h_trading_status_adapters import normalize_tpex_attention
from server.services.unified_mode_a import validate_mode_a_request
from tests.unit.m8r_05b_03_test_helpers import PLAN


ROOT = Path(__file__).resolve().parents[2]
NOW = "2026-09-22T00:00:00Z"
EXECUTOR = "phase_h_imp_7d_deterministic_fixture_executor"
TARGET = {"canonical_target_id": "TPEX:6488", "market": "TPEX", "security_code": "6488"}
FIXTURE_AUTHORITY = "NON_AUTHORITATIVE_TEST_ONLY"


def write_json(root: Path, relative_path: str, value: dict) -> None:
    path = safe_destination(str(root), relative_path, create_parent=True).path
    path.write_text(canonical_json(value) + "\n", encoding="utf-8")


def fixture_request(*, request_id: str = "h-imp-7d-s1", target_inputs: tuple[str, ...] = ("6488",)) -> dict:
    return {
        "schema_version": "unified_market_evidence_request.v3",
        "request_id": request_id,
        "targets": [{"input": value, "market_hint": "TPEX", "resolution_requirement": "exact", "client_target_reference": f"{request_id}-{index}"}
                    for index, value in enumerate(target_inputs)],
        "data_needs": [{"type": "trading_status_context", "priority": "required", "parameters": {}}],
        "execution_mode": "execute",
    }


def fixture_f3(request: dict) -> dict:
    """Use the real F3 validator with its expressly supported fixture input."""
    return validate_mode_a_request(request, allow_fixture_snapshot=True)


def fixture_plan(request: dict, f3: dict, *, operation_id: str | None = None) -> dict:
    plan = deepcopy(PLAN)
    op = plan["operations"][0]
    batch = plan["batch_groups"][0]
    if operation_id is not None:
        op["operation_id"] = operation_id
        batch["operation_ids"] = [operation_id]
    identities = [item["canonical_identity"] for item in f3["target_results"] if item.get("resolution_status") == "resolved"]
    if not identities:
        raise ValueError("fixture_f3_requires_resolved_target")
    op.update({
        "capability_id": "trading_status_context", "canonical_target_ids": [identities[0]["canonical_target_id"]],
        "market": "TPEX", "executor_id": EXECUTOR,
        "expected_evidence_contract": "trading_status_context_evidence.v1", "parameters": {},
        "network_required": False,
    })
    # Frozen plan schema requires a batch group to retain its original network
    # declaration.  The operation and the isolated test-only executor are both
    # explicitly network-free; preflight derives executable network authority
    # from the bound operation/metadata pair.
    batch.update({"capability_id": "trading_status_context", "market": "TPEX", "executor_id": EXECUTOR})
    plan["accounting"].update({"network_request_estimate": 0})
    if len(identities) > 1:
        operations, batches = [op], [batch]
        for identity in identities[1:]:
            suffix = hashlib.sha256(identity["canonical_target_id"].encode("utf-8")).hexdigest()[:20]
            next_op, next_batch = deepcopy(op), deepcopy(batch)
            next_op["operation_id"] = f"umeop-op-v1-{suffix}"
            next_batch["batch_group_id"] = f"umeop-batch-v1-{suffix}"
            next_op["batch_group_id"] = next_batch["batch_group_id"]
            next_op["canonical_target_ids"] = [identity["canonical_target_id"]]
            next_batch["operation_ids"] = [next_op["operation_id"]]
            operations.append(next_op)
            batches.append(next_batch)
        plan["operations"], plan["batch_groups"] = operations, batches
        plan["accounting"].update({"logical_operation_count": len(operations), "batch_group_count": len(batches),
                                    "executor_invocation_count": len(operations), "planned_evidence_bundle_count": 1})
    plan["input_bindings"].update({
        "original_request_hash": sha256_json(request),
        "normalized_request_hash": sha256_json(f3["normalized_request"]),
        "f3_validation_output_hash": sha256_json(f3),
    })
    plan["plan_hash"], plan["plan_id"] = plan_hash_and_id(plan_identity_scope(plan))
    return plan


def fixture_registry() -> dict:
    return {"schema_version": "m8r_05b_03_executor_registry_metadata.v1", "executors": [{
        "executor_id": EXECUTOR, "capability_id": "trading_status_context", "market": "TPEX",
        "supported_security_types": ["equity"], "expected_evidence_contract": "trading_status_context_evidence.v1",
        "network_required": False, "bounded_execution_supported": True, "timeout_seconds": 5,
        "maximum_result_items": 10, "output_policy": "contained_artifact_only",
    }]}


def decision(plan: dict) -> dict:
    return {"decision": "approved", "decision_reason": "H-IMP-7D deterministic fixture transport",
            "owner_identity_reference": "test-owner", "owner_review_reference": "test-review",
            "reviewed_at": NOW, "issued_at": NOW, "expires_at": "2026-09-22T01:00:00Z",
            "single_use": True, "replay_policy": "deny_replay", "maximum_use_count": 1,
            "approval_scope_mode": "selected_operations", "approved_operation_ids": [item["operation_id"] for item in plan["operations"]],
            "approved_batch_group_ids": [], "approved_batch_membership": {}}


def make_runtime(*, malformed: bool = False):
    invocations = {"count": 0}
    rows = json.loads((ROOT / "tests/fixtures/phase_h_h1_adapters/source_rows.json").read_text(encoding="utf-8"))["tpex_attention"]

    def adapter(request: dict, context: Any) -> dict:
        invocations["count"] += 1
        request_id, request_hash = request_identity(request)
        if malformed:
            return {"schema_version": "unified_market_evidence_operation_result.v2", "operation_id": request["operation_id"],
                    "execution_request_id": request_id, "execution_request_hash": request_hash, "executor_id": EXECUTOR,
                    "capability_id": "trading_status_context", "evidence_contract": "trading_status_context_evidence.v1",
                    "status": "failed", "error_code": "source_failed", "result_item_count": 0,
                    "evidence_artifacts": [], "warnings": ["fixture_source_contract_failure"]}
        canonical_target_id = request["approved_security_identifiers"][0]
        target = {"canonical_target_id": canonical_target_id, "market": "TPEX", "security_code": canonical_target_id.split(":", 1)[1]}
        if target["security_code"] != "6488":
            return {"schema_version": "unified_market_evidence_operation_result.v2", "operation_id": request["operation_id"],
                    "execution_request_id": request_id, "execution_request_hash": request_hash, "executor_id": EXECUTOR,
                    "capability_id": "trading_status_context", "evidence_contract": "trading_status_context_evidence.v1",
                    "status": "failed", "error_code": "source_failed", "result_item_count": 0,
                    "evidence_artifacts": [], "warnings": ["fixture_exact_target_row_missing"]}
        evidence_path = f"evidence/phase_h/h1/{request['operation_id']}.json"
        citation = _build_citation_id(request["operation_id"], evidence_path)
        evidence = normalize_tpex_attention(rows, target, observed_at=NOW, citation_id=citation)
        write_json(Path(context.governed_output_root), evidence_path, evidence)
        sidecar_path = f"evidence/phase_h/governance/{request['operation_id']}.json"
        sidecar = {"schema_version": "phase_h_source_attempt_governance.v1", "evidence_artifact_reference": evidence_path,
                   "canonical_target_id": target["canonical_target_id"], "capability_id": "trading_status_context", "attempts": [{
                       "source_family": evidence["source"]["source_family"], "source_contract_id": evidence["source"]["source_contract_id"],
                       "source_role": evidence["source"]["source_role"], "activation_state": evidence["source"]["activation_state"],
                       "provider_availability": "not_required", "license_authority": evidence["source"]["license_authority"],
                       "coverage_result": evidence["status"], "outcome": "succeeded", "failure_code": None,
                       "citation_ids": evidence["citation_ids"],
                   }]}
        write_json(Path(context.governed_output_root), sidecar_path, sidecar)
        def artifact(relative_path: str, value: dict, role: str) -> dict:
            content = (Path(context.governed_output_root) / relative_path).read_bytes()
            return {"relative_path": relative_path, "sha256": hashlib.sha256(content).hexdigest(),
                    "schema_version": value["schema_version"], "byte_size": len(content), "item_count": 1,
                    "evidence_contract": value["schema_version"], "artifact_role": role}
        return {"schema_version": "unified_market_evidence_operation_result.v2", "operation_id": request["operation_id"],
                "execution_request_id": request_id, "execution_request_hash": request_hash, "executor_id": EXECUTOR,
                "capability_id": "trading_status_context", "evidence_contract": "trading_status_context_evidence.v1",
                "status": "succeeded", "error_code": None, "result_item_count": 1,
                "evidence_artifacts": [artifact(evidence_path, evidence, "primary_evidence"), artifact(sidecar_path, sidecar, "supporting_governance")],
                "warnings": []}
    registration = RuntimeAdapterRegistration(EXECUTOR, "trading_status_context", "TPEX", ("equity",),
        "trading_status_context_evidence.v1", False, True, 5, 10, "contained_artifact_only", adapter, fake_adapter=False)
    return RuntimeAdapterRegistry([registration]), invocations


def execute_fixture_package(tmp_path: Path, *, malformed: bool = False, target_inputs: tuple[str, ...] = ("6488",)) -> dict:
    request = fixture_request(target_inputs=target_inputs)
    f3 = fixture_f3(request)
    plan = fixture_plan(request, f3)
    authorization = build_execution_authorization(plan, decision(plan))
    binding = build_consumption_binding(authorization)
    state = {"authorization_id": authorization["authorization_id"], "authorization_hash": authorization["authorization_hash"],
             "consumption_binding_id": binding["consumption_binding_id"], "consumption_binding_hash": binding["consumption_binding_hash"],
             "registry_contract_version": "m8r_05b_03.v1", "state": "unused"}
    package = tmp_path / authorization["authorization_id"]
    package.mkdir(parents=True)
    registry = fixture_registry()
    preflight = build_orchestrator_preflight(plan, authorization, binding, supplied_consumption_state=state,
        evaluation_timestamp=NOW, executor_registry_metadata=registry, output_root=str(package))
    controls = {"request": request, "plan": plan, "authorization": authorization, "consumption_binding": binding,
                "unused_consumption_state": state, "preflight": preflight}
    for name, value in controls.items():
        write_json(package, f"control/{name}.json", value)
    hashes = {name: hashlib.sha256((package / "control" / f"{name}.json").read_bytes()).hexdigest() for name in controls}
    write_json(package, "control/manifest.json", {"schema_version": "m8r_06_03_control_package.v1",
        "authorization_id": authorization["authorization_id"], "authorization_hash": authorization["authorization_hash"],
        "plan_id": plan["plan_id"], "plan_hash": plan["plan_hash"], "preflight_id": preflight["preflight_id"],
        "preflight_hash": preflight["preflight_hash"], "artifact_hashes": hashes})
    runtime, invocations = make_runtime(malformed=malformed)
    prepared = prepare_dispatch(preflight, ExecutorMetadataRegistry.from_json(registry), runtime, mode="execute-approved")
    claim, claim_path = atomic_claim_authorization(preflight, state, output_root=str(package), claim_created_at=NOW,
        operator_confirmation_reference="h-imp-7d", network_execution_confirmed=False)
    outcomes = dispatch_prepared(prepared, governed_output_root=preflight["governed_output_root"], mode="execute-approved", accepted_preflight=preflight)
    aggregation = aggregate_dispatch_outcomes(preflight, outcomes)
    final_claim, receipt, bundle = finalize_consumption_and_write_receipt(preflight, claim, claim_path, aggregation,
        output_root=str(package), finalized_at=NOW, finalization_owner_id="umefo-v1-00000000000000000000")
    return {"request": request, "f3": f3, "plan": plan, "authorization": authorization, "binding": binding,
            "preflight": preflight, "package": package, "claim": final_claim, "receipt": receipt, "bundle": bundle,
            "outcomes": outcomes, "aggregation": aggregation, "invocations": invocations}


def prepare_unused_fixture_package(tmp_path: Path) -> dict:
    """Materialize a governed package through preflight, leaving its claim unused."""
    request = fixture_request(request_id="h-imp-7d-concurrent")
    f3 = fixture_f3(request)
    plan = fixture_plan(request, f3)
    authorization = build_execution_authorization(plan, decision(plan))
    binding = build_consumption_binding(authorization)
    state = {"authorization_id": authorization["authorization_id"], "authorization_hash": authorization["authorization_hash"],
             "consumption_binding_id": binding["consumption_binding_id"], "consumption_binding_hash": binding["consumption_binding_hash"],
             "registry_contract_version": "m8r_05b_03.v1", "state": "unused"}
    package = tmp_path / authorization["authorization_id"]
    package.mkdir(parents=True)
    registry = fixture_registry()
    preflight = build_orchestrator_preflight(plan, authorization, binding, supplied_consumption_state=state,
        evaluation_timestamp=NOW, executor_registry_metadata=registry, output_root=str(package))
    controls = {"request": request, "plan": plan, "authorization": authorization, "consumption_binding": binding,
                "unused_consumption_state": state, "preflight": preflight}
    for name, value in controls.items():
        write_json(package, f"control/{name}.json", value)
    hashes = {name: hashlib.sha256((package / "control" / f"{name}.json").read_bytes()).hexdigest() for name in controls}
    write_json(package, "control/manifest.json", {"schema_version": "m8r_06_03_control_package.v1",
        "authorization_id": authorization["authorization_id"], "authorization_hash": authorization["authorization_hash"],
        "plan_id": plan["plan_id"], "plan_hash": plan["plan_hash"], "preflight_id": preflight["preflight_id"],
        "preflight_hash": preflight["preflight_hash"], "artifact_hashes": hashes})
    return {"preflight": preflight, "state": state, "package": package}
