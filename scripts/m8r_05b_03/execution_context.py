"""The only request shape exposed to a registered executor adapter."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ExecutionContext:
    authorization_id: str
    authorization_hash: str
    plan_id: str
    plan_hash: str
    scope_hash: str
    operation: dict[str, Any]
    operation_binding: dict[str, Any]
    execution_timestamp: str

    @property
    def bounded_request(self) -> dict[str, Any]:
        """Return only fields explicitly bound by the immutable plan/authorization."""
        operation = self.operation
        return {
            "operation_id": operation["operation_id"],
            "capability_id": operation["capability_id"],
            "canonical_target_ids": list(operation["canonical_target_ids"]),
            "market": operation.get("market"),
            "security_types": list(operation.get("security_types", [])),
            "parameters": dict(operation.get("parameters", {})),
            "executor_id": operation["executor_id"],
            "batch_group_id": operation["batch_group_id"],
            "expected_evidence_contract": operation["expected_evidence_contract"],
        }
