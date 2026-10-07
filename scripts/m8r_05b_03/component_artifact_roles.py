"""Fail-closed artifact-role rules for additive Result-level H1 composition."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

COMPOSITE_CONTRACT = "trading_status_context_composite.v1"
H1_COMPONENT_CONTRACTS = {"trading_status_context_evidence.v1", "trading_status_context_evidence.v2"}


def validate_operation_artifact_roles(value: Mapping[str, Any]) -> None:
    artifacts = value.get("evidence_artifacts", [])
    if not isinstance(artifacts, list):
        raise ValueError("operation_result_artifacts_invalid")
    is_composite = (
        value.get("capability_id") == "trading_status_context"
        and value.get("evidence_contract") == COMPOSITE_CONTRACT
    )
    if not is_composite:
        if any(isinstance(item, Mapping) and item.get("artifact_role") == "component_evidence" for item in artifacts):
            raise ValueError("component_evidence_role_requires_composite_operation")
        return
    if value.get("schema_version") != "unified_market_evidence_operation_result.v2":
        raise ValueError("composite_requires_operation_result_v2")
    if value.get("status") != "succeeded":
        if artifacts:
            raise ValueError("failed_composite_operation_has_artifacts")
        return
    primary = [item for item in artifacts if isinstance(item, Mapping) and item.get("artifact_role") == "primary_evidence"]
    components = [item for item in artifacts if isinstance(item, Mapping) and item.get("artifact_role") == "component_evidence"]
    if len(primary) != 1 or primary[0].get("schema_version") != COMPOSITE_CONTRACT:
        raise ValueError("composite_primary_artifact_cardinality_invalid")
    if len(components) != 3:
        raise ValueError("composite_component_artifact_cardinality_invalid")
    if any(item.get("schema_version") not in H1_COMPONENT_CONTRACTS for item in components):
        raise ValueError("composite_component_schema_unsupported")
    component_h1 = [item for item in artifacts if item.get("schema_version") in H1_COMPONENT_CONTRACTS]
    if len(component_h1) != len(components):
        raise ValueError("composite_unclassified_h1_artifact")
    if any(item.get("evidence_contract") != item.get("schema_version") for item in artifacts):
        raise ValueError("operation_result_artifact_contract_mismatch")
    if any(item.get("evidence_contract") != COMPOSITE_CONTRACT for item in primary):
        raise ValueError("composite_primary_contract_mismatch")
    paths = [item.get("relative_path") for item in artifacts]
    hashes = [item.get("sha256") for item in artifacts]
    if len(paths) != len(set(paths)) or len(hashes) != len(set(hashes)):
        raise ValueError("composite_duplicate_artifact_identity")
