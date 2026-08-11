from __future__ import annotations

import json

import pytest

from scripts.m8r_05b_03.dispatch import (
    RuntimeAdapterRegistry,
    dispatch_prepared,
    prepare_dispatch,
)
from scripts.m8r_05b_03.errors import OrchestrationError
from scripts.m8r_05b_03.preflight import build_orchestrator_preflight
from scripts.m8r_05b_03.registry import ExecutorMetadataRegistry
from tests.unit.m8r_05b_03_test_helpers import (
    EVALUATION_TIMESTAMP,
    ROOT,
    artifacts,
    build_valid_preflight,
    default_mock_adapter,
    registry_metadata,
    runtime_registration,
)


def test_approved_adapter_invoked_exactly_once_sequentially(tmp_path):
    invocations = []

    def mock_adapter(request, context):
        invocations.append(request["operation_id"])
        return default_mock_adapter(request, context)

    plan, authorization, binding, state = artifacts()
    preflight = build_valid_preflight(tmp_path)
    meta_reg = ExecutorMetadataRegistry.from_json(registry_metadata(plan))
    run_reg = RuntimeAdapterRegistry([runtime_registration(plan, adapter=mock_adapter, fake_adapter=True)])

    prepared = prepare_dispatch(preflight, meta_reg, run_reg, mode="dry-run")
    outcomes = dispatch_prepared(prepared, governed_output_root=str(tmp_path), mode="dry-run")

    assert len(invocations) == 1
    assert invocations[0] == preflight["approved_operation_order"][0]
    assert len(outcomes) == 1
    assert outcomes[0]["status"] == "succeeded"
    assert outcomes[0]["error_code"] is None


def test_multi_operation_dispatch_order_proof(tmp_path):
    multi_plan = json.loads((ROOT / "tests/fixtures/m8r_05b_01/golden/batching_none_two_unique_batches.json").read_text(encoding="utf-8"))
    plan, authorization, binding, state = artifacts(multi_plan)

    preflight = build_orchestrator_preflight(
        plan,
        authorization,
        binding,
        supplied_consumption_state=state,
        evaluation_timestamp=EVALUATION_TIMESTAMP,
        executor_registry_metadata=registry_metadata(plan),
        output_root=str(tmp_path),
    )

    expected_order = preflight["approved_operation_order"]
    assert len(expected_order) > 1
    assert expected_order == sorted(expected_order)

    # Verify bounded execution requests order
    req_order = [r["operation_id"] for r in preflight["bounded_execution_requests"]]
    assert req_order == expected_order

    # Build runtime registry with custom adapters for each operation
    invocations = []

    def mock_multi_adapter(request, context):
        invocations.append(request["operation_id"])
        return default_mock_adapter(request, context)

    meta_reg = ExecutorMetadataRegistry.from_json(registry_metadata(plan))
    run_reg = RuntimeAdapterRegistry([runtime_registration(plan, adapter=mock_multi_adapter, fake_adapter=True)])

    prepared = prepare_dispatch(preflight, meta_reg, run_reg, mode="dry-run")
    prep_order = [p.request["operation_id"] for p in prepared]
    assert prep_order == expected_order

    outcomes = dispatch_prepared(prepared, governed_output_root=str(tmp_path), mode="dry-run")
    assert invocations == expected_order
    assert len(outcomes) == len(expected_order)


@pytest.mark.parametrize("bad_batch", ["missing", "duplicate"])
def test_batch_adapter_result_membership_fails_closed(tmp_path, bad_batch):
    multi_plan = json.loads((ROOT / "tests/fixtures/m8r_05b_01/golden/multi_target_same_source_batch.json").read_text(encoding="utf-8"))
    plan, authorization, binding, state = artifacts(multi_plan)
    preflight = build_orchestrator_preflight(
        plan, authorization, binding, supplied_consumption_state=state,
        evaluation_timestamp=EVALUATION_TIMESTAMP, executor_registry_metadata=registry_metadata(plan), output_root=str(tmp_path),
    )

    def batch_adapter(requests, context):
        results = [default_mock_adapter(request, context) for request in requests]
        return results[:1] if bad_batch == "missing" else [results[0], results[0]]

    metadata = ExecutorMetadataRegistry.from_json(registry_metadata(plan))
    runtime = RuntimeAdapterRegistry([runtime_registration(plan, fake_adapter=False, batch_adapter=batch_adapter)])
    prepared = prepare_dispatch(preflight, metadata, runtime, mode="execute-approved")
    with pytest.raises(OrchestrationError, match="batch_operation_result_(count|membership)_mismatch"):
        dispatch_prepared(prepared, governed_output_root=str(tmp_path), mode="execute-approved", accepted_preflight=preflight)


def test_execute_approved_multi_operation_batch_requires_accepted_preflight(tmp_path):
    multi_plan = json.loads((ROOT / "tests/fixtures/m8r_05b_01/golden/multi_target_same_source_batch.json").read_text(encoding="utf-8"))
    plan, authorization, binding, state = artifacts(multi_plan)
    preflight = build_orchestrator_preflight(
        plan, authorization, binding, supplied_consumption_state=state,
        evaluation_timestamp=EVALUATION_TIMESTAMP, executor_registry_metadata=registry_metadata(plan), output_root=str(tmp_path),
    )
    metadata = ExecutorMetadataRegistry.from_json(registry_metadata(plan))
    runtime = RuntimeAdapterRegistry([runtime_registration(plan, fake_adapter=False, batch_adapter=lambda requests, context: [default_mock_adapter(item, context) for item in requests])])
    prepared = prepare_dispatch(preflight, metadata, runtime, mode="execute-approved")
    with pytest.raises(OrchestrationError, match="accepted_preflight_required_for_batch_dispatch"):
        dispatch_prepared(prepared, governed_output_root=str(tmp_path), mode="execute-approved")


def test_dry_run_requires_fake_adapter_and_execute_approved_rejects_fake(tmp_path):
    plan, _auth, _bind, _state = artifacts()
    preflight = build_valid_preflight(tmp_path)
    meta_reg = ExecutorMetadataRegistry.from_json(registry_metadata(plan))

    fake_reg = RuntimeAdapterRegistry([runtime_registration(plan, fake_adapter=True)])
    real_reg = RuntimeAdapterRegistry([runtime_registration(plan, fake_adapter=False)])

    # dry-run with real adapter should fail
    with pytest.raises(OrchestrationError, match="dry_run_requires_fake_adapter"):
        prepare_dispatch(preflight, meta_reg, real_reg, mode="dry-run")

    # execute-approved with fake adapter should fail
    with pytest.raises(OrchestrationError, match="execute_approved_rejects_fake_adapter"):
        prepare_dispatch(preflight, meta_reg, fake_reg, mode="execute-approved")


def test_unknown_runtime_adapter_rejected(tmp_path):
    plan, _auth, _bind, _state = artifacts()
    preflight = build_valid_preflight(tmp_path)
    meta_reg = ExecutorMetadataRegistry.from_json(registry_metadata(plan))
    empty_reg = RuntimeAdapterRegistry([])

    with pytest.raises(OrchestrationError, match="unknown_runtime_adapter"):
        prepare_dispatch(preflight, meta_reg, empty_reg, mode="dry-run")


def test_metadata_runtime_mismatch_rejected(tmp_path):
    plan, _auth, _bind, _state = artifacts()
    preflight = build_valid_preflight(tmp_path)
    meta_reg = ExecutorMetadataRegistry.from_json(registry_metadata(plan))

    bad_reg = RuntimeAdapterRegistry([runtime_registration(plan, market="INVALID_MARKET", fake_adapter=True)])

    with pytest.raises(OrchestrationError, match="market_mismatch"):
        prepare_dispatch(preflight, meta_reg, bad_reg, mode="dry-run")


def test_adapter_timeout_and_exception_normalized(tmp_path):
    def timeout_adapter(request, context):
        raise TimeoutError("timeout")

    def error_adapter(request, context):
        raise RuntimeError("crash")

    plan, _auth, _bind, _state = artifacts()
    preflight = build_valid_preflight(tmp_path)
    meta_reg = ExecutorMetadataRegistry.from_json(registry_metadata(plan))

    t_reg = RuntimeAdapterRegistry([runtime_registration(plan, adapter=timeout_adapter, fake_adapter=True)])
    prepared = prepare_dispatch(preflight, meta_reg, t_reg, mode="dry-run")
    outcomes = dispatch_prepared(prepared, governed_output_root=str(tmp_path), mode="dry-run")
    assert outcomes[0]["status"] == "failed"
    assert outcomes[0]["error_code"] == "adapter_timeout"

    e_reg = RuntimeAdapterRegistry([runtime_registration(plan, adapter=error_adapter, fake_adapter=True)])
    prepared = prepare_dispatch(preflight, meta_reg, e_reg, mode="dry-run")
    outcomes = dispatch_prepared(prepared, governed_output_root=str(tmp_path), mode="dry-run")
    assert outcomes[0]["status"] == "failed"
    assert outcomes[0]["error_code"] == "adapter_exception"
