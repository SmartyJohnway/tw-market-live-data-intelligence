from __future__ import annotations

from copy import deepcopy

import pytest

from scripts.m8r_05b_03.dispatch import (
    RuntimeAdapterRegistry,
    dispatch_prepared,
    prepare_dispatch,
)
from scripts.m8r_05b_03.errors import OrchestrationError
from scripts.m8r_05b_03.registry import ExecutorMetadataRegistry
from tests.unit.m8r_05b_03_test_helpers import (
    artifacts,
    build_valid_preflight,
    registry_metadata,
    runtime_registration,
)


def test_approved_adapter_invoked_exactly_once_sequentially(tmp_path):
    invocations = []

    def mock_adapter(request, context):
        invocations.append(request["operation_id"])
        return {"status": "succeeded"}

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
