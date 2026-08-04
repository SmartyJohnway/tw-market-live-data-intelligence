"""Commit 1 preflight for M8R-05B-03.

This module validates contracts and builds deterministic bounded request
projections. It does not claim, dispatch, aggregate evidence, or write files.
"""
from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from .authorization_gate import approved_operations, authorize
from .canonical import sha256_json
from .containment import validate_contained_relative_paths
from .errors import OrchestrationError
from .registry import ExecutorMetadataRegistry, validate_executor_for_operation
from .request_projection import build_execution_request_projection, relative_operation_request_path


ROOT = Path(__file__).resolve().parents[2]
PREFLIGHT_SCHEMA_PATH = ROOT / "schemas" / "unified_market_evidence_orchestrator_preflight.v1.schema.json"


def _batch_bindings(plan: dict, approved_operation_ids: list[str]) -> dict:
    approved = set(approved_operation_ids)
    result = {}
    for batch in plan.get("batch_groups", []):
        if not isinstance(batch, dict):
            continue
        operation_ids = sorted(item for item in batch.get("operation_ids", []) if item in approved)
        if operation_ids:
            result[batch["batch_group_id"]] = {
                "capability_id": batch.get("capability_id"),
                "executor_id": batch.get("executor_id"),
                "market": batch.get("market"),
                "operation_ids": operation_ids,
            }
    return result


def build_orchestrator_preflight(
    plan: dict,
    authorization: dict,
    consumption_binding: dict,
    *,
    supplied_consumption_state: dict,
    evaluation_timestamp: str,
    executor_registry_metadata: dict,
    output_root: str,
) -> dict:
    registry = ExecutorMetadataRegistry.from_json(executor_registry_metadata)
    authorize(
        plan,
        authorization,
        consumption_binding,
        evaluation_timestamp=evaluation_timestamp,
        supplied_consumption_state=supplied_consumption_state,
    )
    operation_pairs = approved_operations(plan, authorization)
    approved_operation_order = [operation["operation_id"] for operation, _binding in operation_pairs]
    contained_paths = validate_contained_relative_paths(
        output_root,
        [relative_operation_request_path(operation_id) for operation_id in approved_operation_order],
    )

    bounded_projections: list[dict] = []
    warnings: list[str] = []
    executor_bindings: dict[str, dict] = {}
    network_required = False
    for (operation, binding), relative_path in zip(operation_pairs, contained_paths, strict=True):
        executor = validate_executor_for_operation(
            operation,
            binding,
            registry,
            network_authorized=authorization["network_authorized"],
        )
        network_required = network_required or executor.network_required
        request, request_warnings = build_execution_request_projection(
            plan=plan,
            authorization=authorization,
            consumption_binding=consumption_binding,
            operation=operation,
            binding=binding,
            executor=executor,
            network_authorized=authorization["network_authorized"],
        )

        request["relative_contained_output_path"] = relative_path
        bounded_projections.append(request)
        warnings.extend(f"{operation['operation_id']}:{warning}" for warning in request_warnings)

        executor_bindings[executor.executor_id] = {
            "executor_id": executor.executor_id,
            "capability_id": executor.capability_id,
            "market": executor.market,
            "supported_security_types": list(executor.supported_security_types),
            "expected_evidence_contract": executor.expected_evidence_contract,
            "network_required": executor.network_required,
            "bounded_execution_supported": executor.bounded_execution_supported,
            "timeout_seconds": executor.timeout_seconds,
            "maximum_result_items": executor.maximum_result_items,
            "output_policy": executor.output_policy,
        }

    output_root_resolved = str(Path(output_root).resolve(strict=True))
    preflight_identity_scope = {
        "plan_id": plan["plan_id"],
        "plan_hash": plan["plan_hash"],
        "authorization_id": authorization["authorization_id"],
        "authorization_hash": authorization["authorization_hash"],
        "consumption_binding_id": consumption_binding["consumption_binding_id"],
        "consumption_binding_hash": consumption_binding["consumption_binding_hash"],
        "scope_hash": authorization["scope_hash"],
        "approved_operation_order": approved_operation_order,
        "executor_registry_ids": registry.ids(),
        "bounded_execution_requests": bounded_projections,
        "governed_output_root": output_root_resolved,
    }
    preflight_identity_hash = sha256_json(preflight_identity_scope)
    artifact_without_artifact_hash = {
        "schema_version": "unified_market_evidence_orchestrator_preflight.v1",
        "preflight_id": "umeopf-v1-" + preflight_identity_hash[:20],
        "preflight_hash": preflight_identity_hash,
        "preflight_identity_hash": preflight_identity_hash,
        "preflight_identity_scope": preflight_identity_scope,
        "plan_id": plan["plan_id"],
        "plan_hash": plan["plan_hash"],
        "authorization_id": authorization["authorization_id"],
        "authorization_hash": authorization["authorization_hash"],
        "consumption_binding_id": consumption_binding["consumption_binding_id"],
        "consumption_binding_hash": consumption_binding["consumption_binding_hash"],
        "scope_hash": authorization["scope_hash"],
        "approved_operation_order": approved_operation_order,
        "resolved_operation_bindings": {binding["operation_id"]: binding for _operation, binding in operation_pairs},
        "resolved_batch_bindings": _batch_bindings(plan, approved_operation_order),
        "resolved_executor_bindings": executor_bindings,
        "bounded_execution_requests": bounded_projections,
        "network_required": network_required,
        "network_authorized": authorization["network_authorized"],
        "execution_authorized": authorization["execution_authorized"],
        "governed_output_root": output_root_resolved,
        "containment_status": "passed",
        "warnings": sorted(set(warnings)),
        "blocking_errors": [],
        "ready_for_claim": True,
        "created_by_component": "m8r_05b_03_preflight",
    }
    artifact = {
        **artifact_without_artifact_hash,
        "preflight_artifact_hash": sha256_json(artifact_without_artifact_hash),
    }
    schema = json.loads(PREFLIGHT_SCHEMA_PATH.read_text(encoding="utf-8"))
    if list(Draft202012Validator(schema).iter_errors(artifact)):
        raise OrchestrationError("preflight_schema_invalid")
    return artifact


def validate_preflight_hashes(preflight: dict) -> None:
    if not isinstance(preflight, dict):
        raise OrchestrationError("preflight_schema_invalid")
    schema = json.loads(PREFLIGHT_SCHEMA_PATH.read_text(encoding="utf-8"))
    if list(Draft202012Validator(schema).iter_errors(preflight)):
        raise OrchestrationError("preflight_schema_invalid")
    identity_hash = sha256_json(preflight["preflight_identity_scope"])
    if (
        preflight["preflight_identity_hash"] != identity_hash
        or preflight["preflight_hash"] != identity_hash
        or preflight["preflight_id"] != "umeopf-v1-" + identity_hash[:20]
    ):
        raise OrchestrationError("preflight_identity_mismatch")
    artifact_without_hash = {key: value for key, value in preflight.items() if key != "preflight_artifact_hash"}
    if preflight["preflight_artifact_hash"] != sha256_json(artifact_without_hash):
        raise OrchestrationError("preflight_artifact_hash_mismatch")


def validate_accepted_preflight(preflight: dict, rebuilt_preflight: dict) -> None:
    validate_preflight_hashes(preflight)
    validate_preflight_hashes(rebuilt_preflight)
    if preflight != rebuilt_preflight:
        raise OrchestrationError("preflight_drift")
