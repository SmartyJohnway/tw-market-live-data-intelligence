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
}


@dataclass
class TargetResolution:
    """Explicit mapping from f3_validation for a single target."""
    target_index: int
    original_input: str
    resolution_status: str
    canonical_target_id: str | None = None
    market: str | None = None


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
    evidence_artifacts: list[dict] = field(default_factory=list)
    # Resolved evidence artifact JSON objects keyed by relative_path
    artifact_objects: dict[str, dict] = field(default_factory=dict)


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
            market=market
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

        # Resolve operation status from bundle.
        bundle_entry = operation_evidence_index.get(operation_id, {})
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
            binding = OperationBinding(
                operation_id=operation_id,
                capability_id=capability_id,
                executor_id=executor_id,
                canonical_target_id=canonical_target_id,
                requested_data_need=data_need,
                market=market,
                status=op_status,
                error_code=error_code,
                evidence_artifacts=raw_artifacts,
                artifact_objects=artifact_objects,
            )

            if canonical_target_id not in lineage.bindings:
                lineage.bindings[canonical_target_id] = {}
            if data_need in lineage.bindings[canonical_target_id]:
                raise ProjectionError("duplicate_binding")
                
            lineage.bindings[canonical_target_id][data_need] = binding
            lineage.by_operation_id[operation_id] = binding

    return lineage
