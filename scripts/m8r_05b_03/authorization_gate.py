"""Cross-artifact checks performed before any consumption or dispatch."""
from __future__ import annotations

from scripts.m8r_05b_02.consumption_binding import evaluate_consumption_preflight
from scripts.m8r_05b_02.models import AuthorizationError

from .errors import OrchestrationError


def authorize(plan: dict, authorization: dict, binding: dict, *, evaluation_timestamp: str, supplied_consumption_state: dict) -> dict:
    try:
        return evaluate_consumption_preflight(authorization, plan, binding, evaluation_timestamp, supplied_consumption_state)
    except AuthorizationError as exc:
        raise OrchestrationError(exc.code) from exc


def approved_operation_map(plan: dict, authorization: dict) -> dict[str, dict]:
    operations = {item.get("operation_id"): item for item in plan.get("operations", []) if isinstance(item, dict)}
    bindings = {item.get("operation_id"): item for item in authorization.get("approved_operation_bindings", []) if isinstance(item, dict)}
    approved = authorization.get("approved_operation_ids", [])
    if not isinstance(approved, list) or set(approved) != set(bindings):
        raise OrchestrationError("approved_operation_binding_mismatch")
    result: dict[str, dict] = {}
    for operation_id in approved:
        operation, binding = operations.get(operation_id), bindings.get(operation_id)
        if not operation or not binding or operation.get("operation_status") != "executable_pending_approval":
            raise OrchestrationError("operation_not_approvable")
        for field in ("capability_id", "executor_id", "expected_evidence_contract", "batch_group_id", "market"):
            if operation.get(field) != binding.get(field):
                raise OrchestrationError("approved_operation_binding_mismatch")
        if sorted(operation.get("security_types", [])) != binding.get("security_types"):
            raise OrchestrationError("approved_operation_binding_mismatch")
        result[operation_id] = binding
    if set(authorization.get("approved_executor_ids", [])) != {item["executor_id"] for item in result.values()}:
        raise OrchestrationError("executor_binding_mismatch")
    return result
