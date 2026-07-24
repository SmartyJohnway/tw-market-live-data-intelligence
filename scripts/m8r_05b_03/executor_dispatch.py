"""Sequential finite dispatch with normalized per-operation outcomes."""
from __future__ import annotations

from typing import Any

from .containment import contained_evidence
from .errors import OrchestrationError
from .execution_context import ExecutionContext
from .registry import ExecutorRegistry


def dispatch(*, plan: dict, authorization: dict, approved_bindings: dict[str, dict], registry: ExecutorRegistry, execution_timestamp: str) -> list[dict[str, Any]]:
    plan_operations = {item["operation_id"]: item for item in plan["operations"]}
    results: list[dict[str, Any]] = []
    for operation_id in authorization["approved_operation_ids"]:
        operation = plan_operations[operation_id]
        binding = approved_bindings[operation_id]
        context = ExecutionContext(authorization["authorization_id"], authorization["authorization_hash"], plan["plan_id"], plan["plan_hash"], authorization["scope_hash"], operation, binding, execution_timestamp)
        try:
            adapter = registry.resolve(operation["executor_id"])
            raw = adapter(context)
            evidence = contained_evidence(raw, operation["expected_evidence_contract"])
            results.append({"operation_id": operation_id, "status": "success", "executor_id": operation["executor_id"], "expected_evidence_contract": operation["expected_evidence_contract"], "evidence": evidence, "omission_reason": None})
        except OrchestrationError as exc:
            results.append({"operation_id": operation_id, "status": "failed", "executor_id": operation["executor_id"], "expected_evidence_contract": operation["expected_evidence_contract"], "evidence": None, "omission_reason": exc.code})
        except Exception as exc:  # adapters must not leak exception content into artifacts
            results.append({"operation_id": operation_id, "status": "failed", "executor_id": operation["executor_id"], "expected_evidence_contract": operation["expected_evidence_contract"], "evidence": None, "omission_reason": "executor_execution_failed", "error_class": exc.__class__.__name__})
    return results
