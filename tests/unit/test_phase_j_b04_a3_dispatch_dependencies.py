"""Fail-closed dependency graph tests before any runtime adapter is called."""
from __future__ import annotations

from scripts.m8r_05b_03.dispatch import (
    DispatchRuntimeContext,
    PreparedDispatch,
    RuntimeAdapterRegistration,
    dispatch_prepared,
)
from scripts.m8r_05b_03.errors import OrchestrationError
from scripts.m8r_05b_03.registry import ExecutorMetadata

TARGET = ["TWSE:2330"]


def _prepared(operation_id: str, capability: str, executor: str, contract: str, order: int, call_log: list[str]):
    request = {
        "schema_version": "unified_market_evidence_execution_request.v3",
        "operation_id": operation_id,
        "execution_request_id": f"umereq-v3-{order:020x}",
        "execution_request_hash": f"{order:064x}",
        "executor_id": executor,
        "capability_id": capability,
        "market": "TWSE",
        "batch_group_id": f"batch-{operation_id}",
        "approved_security_identifiers": TARGET,
        "approved_security_types": ["equity"],
        "timeout_seconds": 15,
        "maximum_records": 1,
        "network_authorized": True,
        "relative_contained_output_path": f"operations/{operation_id}/",
    }

    def adapter(req, context: DispatchRuntimeContext):
        call_log.append(req["operation_id"])
        return {
            "schema_version": "unified_market_evidence_operation_result.v2",
            "operation_id": req["operation_id"],
            "execution_request_id": req["execution_request_id"],
            "execution_request_hash": req["execution_request_hash"],
            "executor_id": executor,
            "capability_id": capability,
            "evidence_contract": contract,
            "status": "failed",
            "error_code": "fixture_not_executed",
            "result_item_count": 0,
            "evidence_artifacts": [],
            "warnings": [],
        }

    metadata = ExecutorMetadata(executor, capability, "TWSE", ("equity",), contract, True, True, 15, 1, "contained_artifact_only")
    registration = RuntimeAdapterRegistration(
        executor, capability, "TWSE", ("equity",), contract, True, True, 15, 1,
        "contained_artifact_only", adapter,
    )
    return PreparedDispatch(request, metadata, registration)


def _plan(h2_dep: list[str], *, h3_capability: str = "recent_performance", h3_target: list[str] | None = None):
    return {"operations": [
        {"operation_id": "h2", "capability_id": "corporate_action_context", "market": "TWSE", "canonical_target_ids": TARGET, "dependency_operation_ids": h2_dep},
        {"operation_id": "h3", "capability_id": h3_capability, "market": "TWSE", "canonical_target_ids": h3_target or TARGET, "dependency_operation_ids": []},
    ]}


def _items(log: list[str]):
    return (
        _prepared("h2", "corporate_action_context", "phase_h_h2_twse_exright_pre_executor", "corporate_action_context_evidence.v1", 1, log),
        _prepared("h3", "recent_performance", "phase_h_h3_twse_recent_performance_executor", "recent_performance_evidence.v1", 2, log),
    )


def test_dispatch_executes_h3_before_h2_even_if_input_order_is_reversed(tmp_path):
    log = []
    result = dispatch_prepared(
        _items(log), governed_output_root=str(tmp_path), mode="execute-approved",
        plan=_plan(["h3"]),
    )
    assert log == ["h3", "h2"]
    assert [item["operation_id"] for item in result] == ["h2", "h3"]


def test_graph_errors_fail_before_any_adapter_call(tmp_path):
    cases = [
        (_plan(["missing"]), "dependency_operation_missing"),
        (_plan(["h2"]), "dependency_graph_invalid"),
        (_plan(["h3"], h3_capability="corporate_action_context"), "h2_h3_dependency_binding_mismatch"),
        (_plan(["h3"], h3_target=["TWSE:0050"]), "h2_h3_dependency_binding_mismatch"),
    ]
    for plan, message in cases:
        log = []
        with pytest.raises(OrchestrationError, match=message):
            dispatch_prepared(_items(log), governed_output_root=str(tmp_path), mode="execute-approved", plan=plan)
        assert log == []


import pytest
