"""Deterministic bounded execution-request projection. It never dispatches."""
from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from .canonical import sha256_json
from .errors import OrchestrationError
from .registry import ExecutorMetadata


ROOT = Path(__file__).resolve().parents[2]
REQUEST_SCHEMA_PATH = ROOT / "schemas" / "unified_market_evidence_execution_request.v1.schema.json"


def relative_operation_request_path(operation_id: str) -> str:
    return f"operations/{operation_id}.execution-request.json"


def build_execution_request_projection(
    *,
    plan: dict,
    authorization: dict,
    consumption_binding: dict,
    operation: dict,
    binding: dict,
    executor: ExecutorMetadata,
    network_authorized: bool,
) -> tuple[dict, list[str]]:
    parameters = operation.get("parameters")
    warnings: list[str] = []
    if not isinstance(parameters, dict):
        parameters = {}
        warnings.append("operation_parameters_unavailable")
    requested_fields = parameters.get("requested_fields")
    if requested_fields is None:
        requested_fields = []
        warnings.append("requested_fields_unavailable")
    currentness_requirement = parameters.get("currentness_requirement")
    if currentness_requirement is None:
        currentness_requirement = "eod_reference_only"
        warnings.append("currentness_requirement_unavailable")

    identity_body = {
        "operation_id": operation["operation_id"],
        "batch_group_id": operation["batch_group_id"],
        "plan_id": plan["plan_id"],
        "plan_hash": plan["plan_hash"],
        "authorization_id": authorization["authorization_id"],
        "authorization_hash": authorization["authorization_hash"],
        "consumption_binding_id": consumption_binding["consumption_binding_id"],
        "consumption_binding_hash": consumption_binding["consumption_binding_hash"],
        "market": binding["market"],
        "approved_security_identifiers": sorted(operation.get("canonical_target_ids", [])),
        "approved_security_types": sorted(operation.get("security_types", [])),
        "capability_id": binding["capability_id"],
        "executor_id": binding["executor_id"],
        "requested_fields": sorted(requested_fields),
        "currentness_requirement": currentness_requirement,
        "maximum_records": executor.maximum_result_items,
        "timeout_seconds": executor.timeout_seconds,
        "network_authorized": network_authorized,
    }
    req_hash = sha256_json(identity_body)
    req_id = "umereq-v1-" + req_hash[:20]

    request = {
        "schema_version": "unified_market_evidence_execution_request.v1",
        "execution_request_id": req_id,
        "execution_request_hash": req_hash,
        "operation_id": operation["operation_id"],
        "batch_group_id": operation["batch_group_id"],
        "plan_id": plan["plan_id"],
        "plan_hash": plan["plan_hash"],
        "authorization_id": authorization["authorization_id"],
        "authorization_hash": authorization["authorization_hash"],
        "consumption_binding_id": consumption_binding["consumption_binding_id"],
        "consumption_binding_hash": consumption_binding["consumption_binding_hash"],
        "market": binding["market"],
        "approved_security_identifiers": sorted(operation.get("canonical_target_ids", [])),
        "approved_security_types": sorted(operation.get("security_types", [])),
        "capability_id": binding["capability_id"],
        "executor_id": binding["executor_id"],
        "requested_fields": sorted(requested_fields),
        "currentness_requirement": currentness_requirement,
        "maximum_records": executor.maximum_result_items,
        "timeout_seconds": executor.timeout_seconds,
        "network_authorized": network_authorized,
        "relative_contained_output_path": relative_operation_request_path(operation["operation_id"]),
    }
    schema = json.loads(REQUEST_SCHEMA_PATH.read_text(encoding="utf-8"))
    if list(Draft202012Validator(schema).iter_errors(request)):
        raise OrchestrationError("execution_request_schema_invalid")
    return request, warnings
