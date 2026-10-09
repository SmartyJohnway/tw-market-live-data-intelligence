"""Shared deterministic dependency graph validation for preflight and dispatch."""
from __future__ import annotations

from typing import Any, Iterable

from .errors import OrchestrationError


def validate_dependency_graph(plan: dict[str, Any], approved_operation_ids: Iterable[str]) -> None:
    operations = plan.get("operations")
    if not isinstance(operations, list):
        raise OrchestrationError("dependency_graph_invalid")
    by_id: dict[str, dict[str, Any]] = {}
    for operation in operations:
        if not isinstance(operation, dict):
            raise OrchestrationError("dependency_graph_invalid")
        operation_id = operation.get("operation_id")
        if not isinstance(operation_id, str) or not operation_id or operation_id in by_id:
            raise OrchestrationError("dependency_graph_invalid")
        by_id[operation_id] = operation

    approved = set(approved_operation_ids)
    graph: dict[str, list[str]] = {}
    for operation_id, operation in by_id.items():
        dependencies = operation.get("dependency_operation_ids", [])
        if (not isinstance(dependencies, list)
                or any(not isinstance(value, str) or not value for value in dependencies)
                or len(dependencies) != len(set(dependencies))):
            raise OrchestrationError("dependency_duplicate_or_invalid")
        if operation_id in dependencies:
            raise OrchestrationError("dependency_self_reference")
        for dependency_id in dependencies:
            dependency = by_id.get(dependency_id)
            if dependency is None:
                raise OrchestrationError("dependency_operation_missing")
            if (dependency.get("operation_status") != "executable_pending_approval"
                    or dependency.get("executor_invocation_eligible") is not True
                    or dependency_id not in approved):
                raise OrchestrationError("dependency_operation_not_approved")
        if (operation.get("capability_id") == "corporate_action_context"
                and operation.get("market") == "TWSE"
                and (operation.get("operation_status") == "executable_pending_approval" or dependencies)):
            if len(dependencies) != 1:
                raise OrchestrationError("h2_dependency_count_invalid")
            dependency = by_id[dependencies[0]]
            if (dependency.get("capability_id") != "recent_performance"
                    or dependency.get("market") != "TWSE"
                    or dependency.get("canonical_target_ids") != operation.get("canonical_target_ids")):
                raise OrchestrationError("h2_h3_dependency_binding_mismatch")
        graph[operation_id] = dependencies

    remaining = {key: set(value) for key, value in graph.items()}
    while remaining:
        ready = sorted(key for key, dependencies in remaining.items() if not dependencies)
        if not ready:
            raise OrchestrationError("dependency_cycle")
        for key in ready:
            remaining.pop(key)
        for dependencies in remaining.values():
            dependencies.difference_update(ready)
