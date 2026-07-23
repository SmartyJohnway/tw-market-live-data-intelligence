"""Stable M8R-05B-01 plan vocabulary; this module performs no I/O."""
from __future__ import annotations
from dataclasses import dataclass

PLAN_SCHEMA_VERSION = "unified_market_evidence_orchestration_plan.v1"
PLANNER_VERSION = "m8r_05b_01.v1"
PLAN_STATUSES = frozenset(("plan_ready", "plan_ready_with_warnings", "plan_only_not_executable", "blocked", "requires_clarification", "unsupported"))
OPERATION_STATUSES = frozenset(("executable_pending_approval", "plan_only_not_executable"))
ERROR_CODES = frozenset(("input_schema_invalid", "validation_status_not_plannable", "f3_invariant_mismatch", "capability_catalog_hash_mismatch", "routing_matrix_hash_mismatch", "handoff_contract_hash_mismatch", "unsupported_contract_version", "target_binding_invalid", "required_capability_blocked", "executor_route_missing", "selected_executor_invalid", "batch_contract_invalid", "operation_limit_exceeded", "canonicalization_error", "output_schema_invalid", "output_path_forbidden"))

@dataclass(frozen=True)
class PlanningError(ValueError):
    """A deterministic, machine-readable failure at the planning boundary."""
    code: str
    detail: str = ""

    def __post_init__(self) -> None:
        if self.code not in ERROR_CODES:
            raise ValueError("unknown_planning_error_code")

    def __str__(self) -> str:
        return self.code if not self.detail else f"{self.code}: {self.detail}"
