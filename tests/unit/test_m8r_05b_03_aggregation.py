from __future__ import annotations

import pytest

from scripts.m8r_05b_03.errors import OrchestrationError
from scripts.m8r_05b_03.evidence_aggregation import aggregate_dispatch_outcomes
from tests.unit.m8r_05b_03_test_helpers import build_valid_preflight


def test_aggregate_all_succeeded(tmp_path):
    preflight = build_valid_preflight(tmp_path)
    op_id = preflight["approved_operation_order"][0]
    req = preflight["bounded_execution_requests"][0]
    binding = preflight["resolved_operation_bindings"][op_id]

    outcomes = [{
        "schema_version": "unified_market_evidence_operation_result.v1",
        "operation_id": op_id,
        "execution_request_id": req["execution_request_id"],
        "execution_request_hash": req["execution_request_hash"],
        "executor_id": req["executor_id"],
        "capability_id": req["capability_id"],
        "evidence_contract": binding["expected_evidence_contract"],
        "status": "succeeded",
        "error_code": None,
        "result_item_count": 5,
        "evidence_artifacts": [{
            "relative_path": req["relative_contained_output_path"],
            "sha256": "00" * 32,
            "schema_version": "test.v1",
            "byte_size": 10,
            "item_count": 5,
        }],
        "warnings": [],
    }]

    agg = aggregate_dispatch_outcomes(preflight, outcomes)
    assert agg["overall_status"] == "succeeded"
    assert agg["total_operations"] == 1
    assert agg["succeeded_operations"] == 1
    assert agg["failed_operations"] == 0
    assert len(agg["operation_receipts"]) == 1
    assert len(agg["artifact_inventory"]) == 1
    assert agg["total_item_count"] == 5


def test_aggregate_duplicate_operation_raises(tmp_path):
    preflight = build_valid_preflight(tmp_path)
    op_id = preflight["approved_operation_order"][0]
    req = preflight["bounded_execution_requests"][0]
    binding = preflight["resolved_operation_bindings"][op_id]

    outcome = {
        "schema_version": "unified_market_evidence_operation_result.v1",
        "operation_id": op_id,
        "execution_request_id": req["execution_request_id"],
        "execution_request_hash": req["execution_request_hash"],
        "executor_id": req["executor_id"],
        "capability_id": req["capability_id"],
        "evidence_contract": binding["expected_evidence_contract"],
        "status": "succeeded",
        "error_code": None,
        "result_item_count": 1,
        "evidence_artifacts": [],
        "warnings": [],
    }

    # Pass 2 identical operation outcomes for preflight that has 2 operations
    preflight_2 = dict(preflight)
    preflight_2["approved_operation_order"] = [op_id, op_id]

    with pytest.raises(OrchestrationError, match="duplicate_operation_id"):
        aggregate_dispatch_outcomes(preflight_2, [outcome, outcome])


def test_aggregate_reordered_operations_raises(tmp_path):
    preflight = build_valid_preflight(tmp_path)
    op_id = preflight["approved_operation_order"][0]
    req = preflight["bounded_execution_requests"][0]
    binding = preflight["resolved_operation_bindings"][op_id]

    preflight_multi = dict(preflight)
    preflight_multi["approved_operation_order"] = ["opA", "opB"]
    preflight_multi["bounded_execution_requests"] = [
        dict(req, operation_id="opA"),
        dict(req, operation_id="opB"),
    ]
    preflight_multi["resolved_operation_bindings"] = {
        "opA": binding,
        "opB": binding,
    }

    outcomes_reordered = [
        {
            "schema_version": "unified_market_evidence_operation_result.v1",
            "operation_id": "opB",
            "execution_request_id": req["execution_request_id"],
            "execution_request_hash": req["execution_request_hash"],
            "executor_id": req["executor_id"],
            "capability_id": req["capability_id"],
            "evidence_contract": binding["expected_evidence_contract"],
            "status": "succeeded",
            "error_code": None,
            "result_item_count": 0,
            "evidence_artifacts": [],
            "warnings": [],
        },
        {
            "schema_version": "unified_market_evidence_operation_result.v1",
            "operation_id": "opA",
            "execution_request_id": req["execution_request_id"],
            "execution_request_hash": req["execution_request_hash"],
            "executor_id": req["executor_id"],
            "capability_id": req["capability_id"],
            "evidence_contract": binding["expected_evidence_contract"],
            "status": "succeeded",
            "error_code": None,
            "result_item_count": 0,
            "evidence_artifacts": [],
            "warnings": [],
        },
    ]

    with pytest.raises(OrchestrationError, match="aggregation_order_mismatch"):
        aggregate_dispatch_outcomes(preflight_multi, outcomes_reordered)
