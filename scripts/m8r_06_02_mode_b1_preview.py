"""Pure Mode B1 planning bindings and canonical Preview projection.

This module performs no network access, authorization, execution, or writes.
"""
from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Mapping

import jsonschema

from scripts.m8r_05b_01.artifact_loader import load_json
from scripts.m8r_05b_01.canonical import sha256_json
from scripts.m8r_05b_01.models import PLANNER_VERSION, PlanningError
from scripts.m8r_05b_01.planner import HANDOFF_VERSION, ROUTING_VERSION, build_plan

ROOT = Path(__file__).resolve().parents[1]
CAPABILITY_CATALOG_PATH = ROOT / "docs/data_capabilities/unified_market_evidence_capability_catalog.v1.json"
ROUTING_MATRIX_PATH = ROOT / "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.json"
HANDOFF_CONTRACT_PATH = ROOT / "docs/data_capabilities/m8r_05b_orchestration_handoff_contract.json"
EXECUTOR_DISPOSITION_PATH = ROOT / "docs/data_capabilities/m8r_05b_existing_orchestrator_disposition.json"
PREVIEW_SCHEMA_PATH = ROOT / "schemas/unified_market_evidence_preview_response.v1.schema.json"

F3_RESOLUTION_TO_SUMMARY = {
    "resolved": "resolved",
    "ambiguous": "ambiguous",
    "not_found": "not_found",
    "market_mismatch": "market_hint_conflict",
    "unsupported_market": "unsupported_market",
    "invalid_market_hint": "invalid_market_hint",
    "unsupported_security_type": "unsupported_security_type",
    "invalid_input": "invalid_input",
    "duplicate": "duplicate",
    "quarantined": "quarantined",
}
TARGET_SUMMARY_FIELDS = tuple(dict.fromkeys(F3_RESOLUTION_TO_SUMMARY.values()))
NON_PLANNABLE_TARGET_STATUSES = frozenset(
    status for status in F3_RESOLUTION_TO_SUMMARY if status not in {"resolved", "ambiguous"}
)


def load_planning_authorities() -> dict[str, dict[str, Any]]:
    """Load current immutable planning inputs on every service request."""
    return {
        "capability_catalog": load_json(CAPABILITY_CATALOG_PATH),
        "routing_matrix": load_json(ROUTING_MATRIX_PATH),
        "handoff_contract": load_json(HANDOFF_CONTRACT_PATH),
        "executor_disposition": load_json(EXECUTOR_DISPOSITION_PATH),
        "preview_schema": load_json(PREVIEW_SCHEMA_PATH),
    }


def build_planning_bindings(
    original_request: Mapping[str, Any],
    f3_validation: Mapping[str, Any],
    security_master: Any,
    *,
    capability_catalog: Mapping[str, Any],
    routing_matrix: Mapping[str, Any],
    handoff_contract: Mapping[str, Any],
) -> dict[str, Any]:
    """Bind F3 and the active governed compact candidate using 05B canonical hashes."""
    pointer = security_master.pointer
    return {
        "original_request_hash": sha256_json(original_request),
        "normalized_request_hash": sha256_json(f3_validation["normalized_request"]),
        "f3_validation_output_hash": sha256_json(f3_validation),
        "security_master_evidence_references": [
            pointer["index_path"],
            pointer["manifest_path"],
        ],
        "security_master_artifact_hashes": [
            pointer["compact_index_sha256"],
            pointer["compact_manifest_sha256"],
        ],
        "capability_catalog_hash": sha256_json(capability_catalog),
        "planner_version": PLANNER_VERSION,
        "routing_matrix_version": ROUTING_VERSION,
        "routing_matrix_hash": sha256_json(routing_matrix),
        "handoff_contract_version": HANDOFF_VERSION,
        "handoff_contract_hash": sha256_json(handoff_contract),
    }


def _target_label(target: Mapping[str, Any]) -> str:
    identity = target.get("canonical_identity") or {}
    return str(
        identity.get("canonical_target_id")
        or target.get("original_input")
        or f"target[{target.get('target_index', '?')}]"
    )


def _target_summary(validation: Mapping[str, Any]) -> dict[str, list[str]]:
    summary = {field: [] for field in TARGET_SUMMARY_FIELDS}
    for target in validation.get("target_results") or []:
        status = target.get("resolution_status")
        if status not in F3_RESOLUTION_TO_SUMMARY:
            raise ValueError("mode_b1_unknown_f3_resolution_status")
        summary[F3_RESOLUTION_TO_SUMMARY[status]].append(_target_label(target))
    for values in summary.values():
        values.sort()
    return summary


def _planning_gap_codes(plan: Mapping[str, Any]) -> list[str]:
    gaps: set[str] = set()
    for operation in plan.get("operations") or []:
        if operation.get("operation_status") == "plan_only_not_executable":
            gaps.add(f"{operation.get('capability_id')}:plan_only_not_executable")
        for warning in operation.get("warnings") or []:
            gaps.add(str(warning.get("code") or "operation_warning"))
    for blocked in plan.get("blocked_operations") or []:
        capability = blocked.get("capability_id")
        for reason in blocked.get("blocking_reason_codes") or ["blocked"]:
            gaps.add(f"{capability}:{reason}")
    for omitted in plan.get("omitted_optional_capabilities") or []:
        gaps.add(f"{omitted.get('capability_id')}:{omitted.get('reason_code')}")
    return sorted(gaps)


def _estimated_operation_count(
    validation: Mapping[str, Any], routing_matrix: Mapping[str, Any]
) -> int:
    routes = {
        route.get("capability_id"): route
        for route in routing_matrix.get("routes") or []
        if isinstance(route, dict)
    }
    resolved_count = sum(
        target.get("resolution_status") == "resolved"
        for target in validation.get("target_results") or []
    )
    return sum(
        resolved_count if (routes.get(cap.get("capability_id")) or {}).get("target_required") else 1
        for cap in validation.get("capability_results") or []
    )


def project_canonical_preview(
    f3_validation: Mapping[str, Any],
    orchestration_plan: Mapping[str, Any] | None,
    *,
    capability_catalog: Mapping[str, Any],
    routing_matrix: Mapping[str, Any],
    preview_schema: Mapping[str, Any],
    planning_error: str | None = None,
) -> dict[str, Any]:
    """Project F3 plus the internal 05B plan into canonical Preview v1."""
    validation = copy.deepcopy(f3_validation)
    plan = copy.deepcopy(orchestration_plan) if orchestration_plan is not None else None
    summary = _target_summary(validation)
    target_statuses = {
        target.get("resolution_status") for target in validation.get("target_results") or []
    }
    blocker_codes = {
        issue.get("code") for issue in validation.get("blocking_issues") or []
    }
    catalog_bounds = capability_catalog.get("bounds") or {}
    operation_count = (
        (plan.get("accounting") or {}).get("logical_operation_count", 0)
        if plan is not None
        else _estimated_operation_count(validation, routing_matrix)
    )
    network_estimate = (
        (plan.get("accounting") or {}).get("network_request_estimate", 0)
        if plan is not None
        else 0
    )
    executable_caps = sorted(
        {
            operation["capability_id"]
            for operation in (plan or {}).get("operations") or []
            if operation.get("operation_status") == "executable_pending_approval"
        }
    )
    gaps = _planning_gap_codes(plan or {})

    if planning_error == "operation_limit_exceeded" or "TARGET_LIMIT_EXCEEDED" in blocker_codes:
        status, coverage = "rejected_resource_bound", "none_possible"
        gaps.append(planning_error or "TARGET_LIMIT_EXCEEDED")
    elif target_statuses.intersection(NON_PLANNABLE_TARGET_STATUSES):
        status, coverage = "target_not_plannable", "none_possible"
        gaps.extend(sorted(target_statuses.intersection(NON_PLANNABLE_TARGET_STATUSES)))
    elif "ambiguous" in target_statuses:
        status, coverage = "ambiguous_target", "none_possible"
        gaps.append("ambiguous_target_requires_clarification")
    elif plan is None:
        status, coverage = "error", "none_possible"
        gaps.append(planning_error or "planning_output_unavailable")
    else:
        plan_status = plan.get("plan_status")
        has_non_executable = bool(gaps)
        if plan_status == "requires_clarification":
            status, coverage = "ambiguous_target", "none_possible"
        elif plan_status in {"unsupported", "blocked", "plan_only_not_executable"}:
            status = "unsupported_capability"
            coverage = "partial_possible" if executable_caps else "none_possible"
        elif plan_status == "plan_ready_with_warnings" or has_non_executable:
            status = "partial_possible" if executable_caps else "unsupported_capability"
            coverage = "partial_possible" if executable_caps else "none_possible"
        elif plan_status == "plan_ready":
            status, coverage = "ready_for_confirmation", "full_possible"
        else:
            status, coverage = "error", "none_possible"
            gaps.append("unexpected_plan_status")

    gaps = sorted(set(gaps))
    target_count = (validation.get("limits") or {}).get("target_count", 0)
    expanded_scope = bool(
        target_count > catalog_bounds.get("default_target_limit", target_count)
        or operation_count > catalog_bounds.get("default_operation_limit", operation_count)
    )
    approval_required = bool(
        plan
        and (plan.get("package_approval_requirements") or {}).get(
            "package_requires_owner_approval"
        )
    )
    preview_identity = {
        "f3_validation_output_hash": sha256_json(validation),
        "plan_hash": (plan or {}).get("plan_hash"),
        "status": status,
    }
    preview = {
        "schema_version": "unified_market_evidence_preview_response.v1",
        "request_id": validation.get("request_id", ""),
        "status": status,
        "target_resolution_summary": summary,
        "requested_data_needs": [
            need.get("type", "")
            for need in (validation.get("normalized_request") or {}).get("data_needs") or []
        ],
        "planned_evidence": executable_caps,
        "coverage_expectation": {"status": coverage, "known_gaps": gaps},
        "bounds": {
            "target_count": target_count,
            "operation_count": operation_count,
            "estimated_network_calls": network_estimate or 0,
            "expanded_scope": expanded_scope,
        },
        "fallbacks": [],
        "approval": {
            "required": approval_required,
            "confirmation_text": (
                "Owner confirmation is required before any future authorization."
                if approval_required
                else "Preview only; execution is not authorized."
            ),
        },
        "internal_execution_reference": {
            "preview_id": "umepreview-v1-" + sha256_json(preview_identity)[:20]
        },
        "caveats": ["PREVIEW_ONLY", "NO_NETWORK_EXECUTED", "EXECUTION_NOT_AUTHORIZED"],
    }
    try:
        jsonschema.Draft7Validator.check_schema(preview_schema)
    except jsonschema.SchemaError as exc:
        raise PlanningError("input_schema_invalid", "preview_schema") from exc
    try:
        jsonschema.Draft7Validator(preview_schema).validate(preview)
    except jsonschema.ValidationError as exc:
        raise PlanningError("output_schema_invalid", "preview") from exc
    return preview


def build_mode_b1_preview_package(
    original_request: Mapping[str, Any],
    f3_validation: Mapping[str, Any],
    security_master: Any,
    *,
    planning_timestamp: str,
    authorities: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build one offline, non-authorizing Mode B1 response envelope."""
    loaded = copy.deepcopy(authorities) if authorities is not None else load_planning_authorities()
    if f3_validation.get("request_schema_status") != "valid":
        return {
            "validation": copy.deepcopy(f3_validation),
            "preview": None,
            "orchestration_plan": None,
            "network_executed": False,
            "authorization_created": False,
            "authorization_consumed": False,
            "execution_performed": False,
        }
    bindings = build_planning_bindings(
        original_request,
        f3_validation,
        security_master,
        capability_catalog=loaded["capability_catalog"],
        routing_matrix=loaded["routing_matrix"],
        handoff_contract=loaded["handoff_contract"],
    )
    plan = None
    planning_error = None
    try:
        plan = build_plan(
            f3_validation,
            capability_catalog=loaded["capability_catalog"],
            routing_matrix=loaded["routing_matrix"],
            handoff_contract=loaded["handoff_contract"],
            executor_disposition=loaded["executor_disposition"],
            input_bindings=bindings,
            planning_timestamp=planning_timestamp,
        )
    except PlanningError as exc:
        if exc.code != "operation_limit_exceeded":
            raise
        planning_error = exc.code
    preview = project_canonical_preview(
        f3_validation,
        plan,
        capability_catalog=loaded["capability_catalog"],
        routing_matrix=loaded["routing_matrix"],
        preview_schema=loaded["preview_schema"],
        planning_error=planning_error,
    )
    return {
        "validation": copy.deepcopy(f3_validation),
        "preview": preview,
        "orchestration_plan": plan,
        "network_executed": False,
        "authorization_created": False,
        "authorization_consumed": False,
        "execution_performed": False,
    }
