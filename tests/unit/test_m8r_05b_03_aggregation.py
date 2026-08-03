from __future__ import annotations

import pytest

from scripts.m8r_05b_03.errors import OrchestrationError
from scripts.m8r_05b_03.evidence_aggregation import aggregate_dispatch_outcomes
from tests.unit.m8r_05b_03_test_helpers import build_valid_preflight


def test_aggregate_all_succeeded(tmp_path):
    preflight = build_valid_preflight(tmp_path)
    outcomes = [{
        "operation_id": preflight["approved_operation_order"][0],
        "executor_id": "test-executor",
        "capability_id": "test-cap",
        "status": "succeeded",
        "error_code": None,
        "request": {
            "execution_request_id": "umereq-v1-00000000000000000001",
            "execution_request_hash": "00" * 32,
        },
        "result_item_count": 5,
        "artifact_relative_path": "artifacts/op1.json",
    }]

    agg = aggregate_dispatch_outcomes(preflight, outcomes)
    assert agg["overall_status"] == "succeeded"
    assert agg["total_operations"] == 1
    assert agg["succeeded_operations"] == 1
    assert agg["failed_operations"] == 0
    assert len(agg["operation_receipts"]) == 1


def test_aggregate_partial_success(tmp_path):
    preflight = dict(build_valid_preflight(tmp_path))
    preflight["approved_operation_order"] = ["op1", "op2"]

    outcomes = [
        {
            "operation_id": "op1",
            "executor_id": "e1",
            "capability_id": "c1",
            "status": "succeeded",
            "error_code": None,
            "request": {"execution_request_id": "umereq-v1-00000000000000000001", "execution_request_hash": "00" * 32},
            "result_item_count": 2,
            "artifact_relative_path": "art1",
        },
        {
            "operation_id": "op2",
            "executor_id": "e2",
            "capability_id": "c2",
            "status": "failed",
            "error_code": "adapter_timeout",
            "request": {"execution_request_id": "umereq-v1-00000000000000000002", "execution_request_hash": "00" * 32},
            "result_item_count": 0,
            "artifact_relative_path": None,
        },
    ]

    agg = aggregate_dispatch_outcomes(preflight, outcomes)
    assert agg["overall_status"] == "partial_success"
    assert agg["succeeded_operations"] == 1
    assert agg["failed_operations"] == 1


def test_aggregate_all_failed(tmp_path):
    preflight = build_valid_preflight(tmp_path)
    outcomes = [{
        "operation_id": preflight["approved_operation_order"][0],
        "executor_id": "test-executor",
        "capability_id": "test-cap",
        "status": "failed",
        "error_code": "adapter_exception",
        "request": {"execution_request_id": "umereq-v1-00000000000000000001", "execution_request_hash": "00" * 32},
        "result_item_count": 0,
        "artifact_relative_path": None,
    }]

    agg = aggregate_dispatch_outcomes(preflight, outcomes)
    assert agg["overall_status"] == "failed"
    assert agg["succeeded_operations"] == 0
    assert agg["failed_operations"] == 1


def test_aggregate_count_mismatch_raises(tmp_path):
    preflight = build_valid_preflight(tmp_path)
    # preflight expects 1 operation, pass 2 outcomes to trigger count mismatch
    outcomes = [
        {
            "operation_id": "op1",
            "status": "succeeded",
            "request": {"execution_request_id": "umereq-v1-00000000000000000001", "execution_request_hash": "00" * 32},
        },
        {
            "operation_id": "op2",
            "status": "succeeded",
            "request": {"execution_request_id": "umereq-v1-00000000000000000002", "execution_request_hash": "00" * 32},
        },
    ]
    with pytest.raises(OrchestrationError, match="dispatch_outcomes_count_mismatch"):
        aggregate_dispatch_outcomes(preflight, outcomes)
