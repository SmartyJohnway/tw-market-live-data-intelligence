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


def test_aggregate_preserves_execution_request_v2_identity_verbatim(tmp_path):
    preflight = build_valid_preflight(tmp_path)
    op_id = preflight["approved_operation_order"][0]
    req = preflight["bounded_execution_requests"][0]
    req.update({
        "schema_version": "unified_market_evidence_execution_request.v2",
        "execution_request_id": "umereq-v2-" + "b" * 20,
        "execution_request_hash": "c" * 64,
        "capability_id": "recent_performance",
        "parameters": {"lookback_trading_days": 20},
    })
    binding = preflight["resolved_operation_bindings"][op_id]
    binding["capability_id"] = "recent_performance"
    outcome = {
        "schema_version": "unified_market_evidence_operation_result.v2",
        "operation_id": op_id,
        "execution_request_id": req["execution_request_id"],
        "execution_request_hash": req["execution_request_hash"],
        "executor_id": req["executor_id"],
        "capability_id": req["capability_id"],
        "evidence_contract": binding["expected_evidence_contract"],
        "status": "failed", "error_code": "fixture_failure", "result_item_count": 0,
        "evidence_artifacts": [], "warnings": [],
    }
    aggregation = aggregate_dispatch_outcomes(preflight, [outcome])
    operation_receipt = aggregation["operation_receipts"][0]
    assert operation_receipt["execution_request_id"] == req["execution_request_id"]
    assert operation_receipt["execution_request_hash"] == req["execution_request_hash"]


def test_aggregate_v2_preserves_per_artifact_contract_and_excludes_supporting_items(tmp_path):
    preflight = build_valid_preflight(tmp_path)
    op_id = preflight["approved_operation_order"][0]
    req = preflight["bounded_execution_requests"][0]
    binding = preflight["resolved_operation_bindings"][op_id]
    binding["expected_evidence_contract"] = "trading_status_context_evidence.v1"
    primary = {"relative_path": "evidence/typed.json", "sha256": "11" * 32,
               "schema_version": "trading_status_context_evidence.v1", "byte_size": 10, "item_count": 1,
               "evidence_contract": binding["expected_evidence_contract"], "artifact_role": "primary_evidence"}
    support = {"relative_path": "evidence/governance.json", "sha256": "22" * 32,
               "schema_version": "phase_h_source_attempt_governance.v1", "byte_size": 10, "item_count": 1,
               "evidence_contract": "phase_h_source_attempt_governance.v1", "artifact_role": "supporting_governance"}
    outcome = {"schema_version": "unified_market_evidence_operation_result.v2", "operation_id": op_id,
               "execution_request_id": req["execution_request_id"], "execution_request_hash": req["execution_request_hash"],
               "executor_id": req["executor_id"], "capability_id": req["capability_id"],
               "evidence_contract": binding["expected_evidence_contract"], "status": "succeeded", "error_code": None,
               "result_item_count": 1, "evidence_artifacts": [primary, support], "warnings": []}
    agg = aggregate_dispatch_outcomes(preflight, [outcome])
    assert agg["total_item_count"] == 1
    assert {item["evidence_contract"] for item in agg["artifact_inventory"]} == {
        binding["expected_evidence_contract"], "phase_h_source_attempt_governance.v1"}
    assert all(set(item) == {"relative_path", "sha256", "schema_version", "byte_size", "item_count"}
               for item in agg["operation_receipts"][0]["evidence_artifacts"])
    assert all(set(item) == {"relative_path", "sha256", "schema_version", "byte_size", "item_count"}
               for item in agg["operation_evidence_entries"][0]["artifacts"])


@pytest.mark.parametrize("artifacts, count, code", [
    ([{"artifact_role": "supporting_governance", "evidence_contract": "x", "schema_version": "x", "item_count": 1}], 0, "operation_result_primary_artifact_missing"),
    ([{"artifact_role": "primary_evidence", "evidence_contract": "wrong", "schema_version": "wrong", "item_count": 1}], 1, "operation_result_artifact_contract_mismatch"),
    ([{"artifact_role": "primary_evidence", "evidence_contract": "trading_status_context_evidence.v1", "schema_version": "trading_status_context_evidence.v1", "item_count": 3}, {"artifact_role": "supporting_governance", "evidence_contract": "sidecar.v1", "schema_version": "sidecar.v1", "item_count": 1}], 4, "operation_result_item_count_mismatch"),
])
def test_aggregate_v2_rejects_invalid_primary_or_count(tmp_path, artifacts, count, code):
    preflight = build_valid_preflight(tmp_path)
    op_id = preflight["approved_operation_order"][0]
    req = preflight["bounded_execution_requests"][0]
    binding = preflight["resolved_operation_bindings"][op_id]
    binding["expected_evidence_contract"] = "trading_status_context_evidence.v1"
    for index, artifact in enumerate(artifacts):
        artifact.update({"relative_path": f"evidence/{index}.json", "sha256": f"{index + 1:02x}" * 32, "byte_size": 1})
    outcome = {"schema_version": "unified_market_evidence_operation_result.v2", "operation_id": op_id,
               "execution_request_id": req["execution_request_id"], "execution_request_hash": req["execution_request_hash"],
               "executor_id": req["executor_id"], "capability_id": req["capability_id"],
               "evidence_contract": binding["expected_evidence_contract"], "status": "succeeded", "error_code": None,
               "result_item_count": count, "evidence_artifacts": artifacts, "warnings": []}
    with pytest.raises(OrchestrationError, match=code):
        aggregate_dispatch_outcomes(preflight, [outcome])


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
