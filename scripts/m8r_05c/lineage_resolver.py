"""Deterministic lineage resolver for M8R-05C.

Maps each (canonical_target_id, requested_data_need) pair to the
authoritative operation(s) and their evidence artifacts from the
05B-03 bundle.

This module:
- Is a pure function (no side effects, no network, no clock).
- Uses f3_validation for explicit target resolution mapping.
- Uses plan.operations[] as the authoritative mapping.
- Uses bundle.artifact_inventory as the authoritative artifact registry.
- Enforces strict governance: duplicate operations or bindings raise errors, unknown capabilities raise errors.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .errors import ProjectionError
from .models import ProjectionInputs

# Map from capability_id (used in plan) to data_need type (used in request).
# These are the accepted capability identifiers for M8R-05A evidence needs.
_CAPABILITY_TO_DATA_NEED: dict[str, str] = {
    "identity": "identity",
    "current_observation": "current_observation",
    "official_eod_reference": "official_eod_reference",
    "recent_performance": "recent_performance",
    "session_status": "session_status",
    "source_currentness": "source_currentness",
    "evidence_quality": "evidence_quality",
    "material_disclosures": "material_disclosures",
    "monthly_revenue": "monthly_revenue",
    "trading_status_context": "trading_status_context",
    "corporate_action_context": "corporate_action_context",
    "market_state_context": "market_state_context",
    "index_futures_context": "index_futures_context",
    "cash_institutional_flow_context": "cash_institutional_flow_context",
}

_TARGET_SCOPED_EVIDENCE_CONTRACTS = {
    "phase_g_material_disclosure_operation_evidence.v1",
    "phase_g_monthly_revenue_operation_evidence.v1",
    "trading_status_context_evidence.v1",
    "trading_status_context_evidence.v2",
    "trading_status_context_composite.v1",
    "corporate_action_context_evidence.v1",
    "recent_performance_evidence.v1",
    "market_state_context_evidence.v1",
    "index_futures_context_evidence.v1",
    "cash_institutional_flow_context_evidence.v2",
}

_PHASE_H_TYPED_EVIDENCE_CONTRACTS = {
    "trading_status_context_evidence.v1",
    "trading_status_context_evidence.v2",
    "corporate_action_context_evidence.v1",
    "recent_performance_evidence.v1",
}

_PHASE_H_TYPED_CONTRACT_BY_DATA_NEED = {
    "trading_status_context": "trading_status_context_evidence.v1",
    "corporate_action_context": "corporate_action_context_evidence.v1",
    "recent_performance": "recent_performance_evidence.v1",
}

_PHASE_I_TYPED_CONTRACT_BY_DATA_NEED = {
    "market_state_context": "market_state_context_evidence.v1",
    "index_futures_context": "index_futures_context_evidence.v1",
    "cash_institutional_flow_context": "cash_institutional_flow_context_evidence.v2",
}
_PHASE_I_TYPED_EVIDENCE_CONTRACTS = set(_PHASE_I_TYPED_CONTRACT_BY_DATA_NEED.values())


def _expected_typed_contract(data_need: str) -> str | None:
    return (_PHASE_H_TYPED_CONTRACT_BY_DATA_NEED.get(data_need)
            or _PHASE_I_TYPED_CONTRACT_BY_DATA_NEED.get(data_need))


def _allowed_typed_contracts(data_need: str) -> set[str]:
    if data_need == "trading_status_context":
        return {"trading_status_context_evidence.v1", "trading_status_context_evidence.v2"}
    expected = _expected_typed_contract(data_need)
    return {expected} if expected is not None else set()


@dataclass
class TargetResolution:
    """Explicit mapping from f3_validation for a single target."""
    target_index: int
    original_input: str
    resolution_status: str
    canonical_target_id: str | None = None
    market: str | None = None
    canonical_identity: dict | None = None


@dataclass
class OperationBinding:
    """Resolved binding for one (canonical_target_id, data_need) pair."""
    operation_id: str
    capability_id: str
    executor_id: str
    canonical_target_id: str
    requested_data_need: str
    market: str | None
    status: str  # succeeded | failed
    error_code: str | None
    # Planning status remains authoritative when an intentional plan-only
    # operation has no execution-bundle entry.
    plan_operation_status: str | None = None
    evidence_artifacts: list[dict] = field(default_factory=list)
    # Resolved evidence artifact JSON objects keyed by relative_path
    artifact_objects: dict[str, dict] = field(default_factory=dict)
    primary_evidence_relative_path: str | None = None


@dataclass
class LineageMap:
    """Full lineage: target_id → data_need → OperationBinding."""
    # target_id → data_need → binding
    bindings: dict[str, dict[str, OperationBinding]] = field(default_factory=dict)
    # operation_id → OperationBinding (flat lookup)
    by_operation_id: dict[str, OperationBinding] = field(default_factory=dict)
    # requested data needs from request
    requested_data_needs: list[str] = field(default_factory=list)
    # Target resolutions mapped by their index in the request
    target_resolutions: dict[int, TargetResolution] = field(default_factory=dict)


def build_lineage_map(inputs: ProjectionInputs) -> LineageMap:
    """Build the deterministic lineage map from f3_validation, plan, and bundle.

    Pure function: no network, no clock, no side effects.
    Raises ProjectionError on unresolvable mapping, duplicate operations, or unknown capabilities.
    """
    plan = inputs.plan
    bundle = inputs.bundle
    f3_validation = inputs.f3_validation
    evidence_artifacts = inputs.evidence_artifacts

    # Index request data_needs.
    data_needs = inputs.request.get("data_needs", [])
    if not isinstance(data_needs, list):
        raise ProjectionError("request_data_needs_invalid")
    requested_data_needs = sorted(
        dn["type"] for dn in data_needs if isinstance(dn, dict) and "type" in dn
    )

    # Process f3_validation target mappings.
    target_resolutions: dict[int, TargetResolution] = {}
    for t_res in f3_validation.get("target_results", []):
        if not isinstance(t_res, dict):
            continue
        target_idx = t_res.get("target_index")
        if target_idx is None:
            continue
            
        canonical_id = None
        market = None
        identity = t_res.get("canonical_identity")
        if isinstance(identity, dict):
            canonical_id = identity.get("canonical_target_id")
            market = identity.get("market")
            
        target_resolutions[target_idx] = TargetResolution(
            target_index=target_idx,
            original_input=t_res.get("original_input", ""),
            resolution_status=t_res.get("resolution_status", "not_found"),
            canonical_target_id=canonical_id,
            market=market,
            canonical_identity=identity.copy() if isinstance(identity, dict) else None,
        )

    # Index bundle operation evidence entries by operation_id.
    operation_evidence_index: dict[str, dict] = {}
    for entry in bundle.get("operation_evidence_entries", []):
        if isinstance(entry, dict) and "operation_id" in entry:
            op_id = entry["operation_id"]
            if op_id in operation_evidence_index:
                raise ProjectionError("duplicate_operation_id")
            operation_evidence_index[op_id] = entry

    lineage = LineageMap(
        requested_data_needs=requested_data_needs,
        target_resolutions=target_resolutions,
    )

    # Build (target_id, data_need) → OperationBinding mapping.
    for op in plan.get("operations", []):
        if not isinstance(op, dict):
            continue
        operation_id = op.get("operation_id")
        capability_id = op.get("capability_id")
        executor_id = op.get("executor_id") or ""
        market = op.get("market")
        canonical_target_ids = op.get("canonical_target_ids", [])

        if not operation_id or not capability_id:
            continue

        # Map capability_id to data_need.
        data_need = _CAPABILITY_TO_DATA_NEED.get(capability_id)
        if data_need is None:
            raise ProjectionError("unknown_capability")

        # Only process requested data_needs.
        if data_need not in requested_data_needs:
            continue

        # An absent execution entry is only non-failure when the plan itself
        # explicitly marks the operation as non-executable.
        plan_operation_status = op.get("operation_status")
        bundle_entry = operation_evidence_index.get(operation_id)
        if bundle_entry is None and plan_operation_status == "plan_only_not_executable":
            op_status, error_code, raw_artifacts = "plan_only_not_executed", None, []
        else:
            bundle_entry = bundle_entry or {}
            op_status = bundle_entry.get("status", "failed")
            error_code = bundle_entry.get("error_code")
            raw_artifacts = bundle_entry.get("artifacts", [])

        # Resolve artifact objects.
        artifact_objects: dict[str, dict] = {}
        for art in raw_artifacts:
            if isinstance(art, dict):
                rel_path = art.get("relative_path")
                if rel_path and rel_path in evidence_artifacts:
                    artifact_objects[rel_path] = evidence_artifacts[rel_path]

        for canonical_target_id in canonical_target_ids:
            target_artifacts: list[dict] = []
            target_artifact_objects: dict[str, dict] = {}
            artifact_roles = {
                art.get("relative_path"): art.get("artifact_role", "primary_evidence")
                for art in raw_artifacts if isinstance(art, dict)
            }
            for art in raw_artifacts:
                if not isinstance(art, dict):
                    continue
                rel_path = art.get("relative_path")
                artifact_obj = artifact_objects.get(rel_path)
                schema_version = artifact_obj.get("schema_version") if isinstance(artifact_obj, dict) else None
                expected_typed_contracts = _allowed_typed_contracts(data_need)
                if (schema_version in _PHASE_H_TYPED_EVIDENCE_CONTRACTS | _PHASE_I_TYPED_EVIDENCE_CONTRACTS
                        and schema_version not in expected_typed_contracts):
                    continue
                if schema_version in _TARGET_SCOPED_EVIDENCE_CONTRACTS and schema_version not in _PHASE_I_TYPED_EVIDENCE_CONTRACTS:
                    artifact_target = artifact_obj.get("target") or {}
                    if artifact_target.get("canonical_target_id") != canonical_target_id:
                        continue
                target_artifacts.append(art)
                if rel_path in artifact_objects:
                    target_artifact_objects[rel_path] = artifact_objects[rel_path]
            composite_candidates = [
                (path, obj) for path, obj in target_artifact_objects.items()
                if isinstance(obj, dict) and obj.get("schema_version") == "trading_status_context_composite.v1"
            ]
            component_candidates = [
                (path, obj) for path, obj in target_artifact_objects.items()
                if isinstance(obj, dict) and obj.get("schema_version") in _allowed_typed_contracts(data_need)
                and artifact_roles.get(path) == "component_evidence"
            ]
            primary_evidence_path = None
            if composite_candidates or component_candidates:
                if data_need != "trading_status_context" or len(composite_candidates) != 1:
                    raise ProjectionError("composite_operation_artifact_model_invalid")
                primary_evidence_path, composite = composite_candidates[0]
                if op_status != "succeeded" or composite.get("target", {}).get("market") != market:
                    raise ProjectionError("composite_operation_target_or_status_mismatch")
                if artifact_roles.get(primary_evidence_path) != "primary_evidence":
                    raise ProjectionError("composite_primary_role_invalid")
                expected_components = composite.get("components", [])
                if len(component_candidates) != 3 or len(expected_components) != 3:
                    raise ProjectionError("composite_component_artifact_cardinality_invalid")
                component_by_path = {path: obj for path, obj in component_candidates}
                if len(component_by_path) != 3:
                    raise ProjectionError("composite_duplicate_component_artifact")
                inventory_by_path = {
                    item.get("relative_path"): item for item in bundle.get("artifact_inventory", [])
                    if isinstance(item, dict)
                }
                primary_inventory = inventory_by_path.get(primary_evidence_path)
                primary_operation_ref = next(
                    (item for item in raw_artifacts if isinstance(item, dict)
                     and item.get("relative_path") == primary_evidence_path), None,
                )
                if (not isinstance(primary_inventory, dict) or not isinstance(primary_operation_ref, dict)
                        or primary_inventory.get("artifact_role") != "primary_evidence"
                        or primary_inventory.get("evidence_contract") != "trading_status_context_composite.v1"
                        or primary_inventory.get("item_count") != composite.get("canonical_item_count")
                        or primary_inventory.get("sha256") != primary_operation_ref.get("sha256")
                        or primary_inventory.get("schema_version") != primary_operation_ref.get("schema_version")):
                    raise ProjectionError("composite_primary_artifact_reference_mismatch")
                try:
                    from .trading_status_composer import (
                        validate_component_artifact_bindings,
                        validate_trading_status_context_composite,
                    )
                    validate_trading_status_context_composite(composite)
                    validate_component_artifact_bindings(composite, component_by_path, inventory_by_path)
                except (TypeError, ValueError) as exc:
                    raise ProjectionError("composite_artifact_invalid") from exc
                expected_paths = {item["artifact_reference"]["relative_path"] for item in expected_components}
                if any(component.get("source_contract_id") != component.get("evidence", {}).get("source", {}).get("source_contract_id")
                       or component.get("evidence", {}).get("target") != composite.get("target")
                       for component in expected_components):
                    raise ProjectionError("composite_component_reference_mismatch")
                if expected_paths != set(component_by_path):
                    raise ProjectionError("composite_unreferenced_component_artifact")
                allowed_paths = expected_paths | {primary_evidence_path}
                extra_typed = [
                    path for path, obj in target_artifact_objects.items()
                    if isinstance(obj, dict)
                    and obj.get("schema_version") in _PHASE_H_TYPED_EVIDENCE_CONTRACTS
                    and path not in allowed_paths
                ]
                if extra_typed:
                    raise ProjectionError("composite_unapproved_h1_artifact")
            elif any(role == "component_evidence" for role in artifact_roles.values()):
                raise ProjectionError("component_evidence_without_composite")

            typed_artifact_count = sum(
                artifact.get("schema_version") in _allowed_typed_contracts(data_need)
                for path, artifact in target_artifact_objects.items()
                if isinstance(artifact, dict) and artifact_roles.get(path) != "component_evidence"
            )
            if typed_artifact_count > 1 and not composite_candidates:
                raise ProjectionError("duplicate_phase_h_typed_artifact")
            binding = OperationBinding(
                operation_id=operation_id,
                capability_id=capability_id,
                executor_id=executor_id,
                canonical_target_id=canonical_target_id,
                requested_data_need=data_need,
                market=market,
                status=op_status,
                error_code=error_code,
                plan_operation_status=plan_operation_status,
                evidence_artifacts=target_artifacts,
                artifact_objects=target_artifact_objects,
                primary_evidence_relative_path=primary_evidence_path,
            )

            if canonical_target_id not in lineage.bindings:
                lineage.bindings[canonical_target_id] = {}
            if data_need in lineage.bindings[canonical_target_id]:
                raise ProjectionError("duplicate_binding")
                
            lineage.bindings[canonical_target_id][data_need] = binding
            lineage.by_operation_id[operation_id] = binding

    return lineage
