from __future__ import annotations

from copy import deepcopy

import pytest

from scripts.m8r_05b_03.controlled_dispatch import claim_and_dispatch_approved
from scripts.m8r_05b_03.dispatch import RuntimeAdapterRegistry
from scripts.m8r_05b_03.errors import OrchestrationError
from tests.unit.m8r_05b_03_test_helpers import (
    CLAIM_TIMESTAMP,
    EVALUATION_TIMESTAMP,
    artifacts,
    build_valid_preflight,
    registry_metadata,
    runtime_registration,
)


def test_dry_run_is_non_consuming_and_leaves_no_durable_claim(tmp_path):
    plan, authorization, binding, state = artifacts()
    preflight = build_valid_preflight(tmp_path)
    run_reg = RuntimeAdapterRegistry([runtime_registration(plan, fake_adapter=True)])

    res = claim_and_dispatch_approved(
        plan,
        authorization,
        binding,
        supplied_consumption_state=state,
        accepted_preflight=preflight,
        evaluation_timestamp=EVALUATION_TIMESTAMP,
        claim_created_at=CLAIM_TIMESTAMP,
        executor_registry_metadata=registry_metadata(plan),
        runtime_adapter_registry=run_reg,
        output_root=str(tmp_path),
        mode="dry-run",
    )

    assert res["consumption_state"] == "unconsumed_dry_run"
    assert res["claim_record"] is None
    assert res["claim_relative_path"] is None
    assert res["aggregation_created"] is False
    assert res["execution_receipt_created"] is False

    # Verify no claim file was written to disk
    assert not (tmp_path / "claims").exists()


def test_repeated_dry_run_then_successful_execute_and_replay_block(tmp_path):
    plan, authorization, binding, state = artifacts()
    preflight = build_valid_preflight(tmp_path)

    dry_run_reg = RuntimeAdapterRegistry([runtime_registration(plan, fake_adapter=True)])
    real_run_reg = RuntimeAdapterRegistry([runtime_registration(plan, fake_adapter=False)])

    # 1. First dry-run
    res_dry1 = claim_and_dispatch_approved(
        plan,
        authorization,
        binding,
        supplied_consumption_state=state,
        accepted_preflight=preflight,
        evaluation_timestamp=EVALUATION_TIMESTAMP,
        claim_created_at=CLAIM_TIMESTAMP,
        executor_registry_metadata=registry_metadata(plan),
        runtime_adapter_registry=dry_run_reg,
        output_root=str(tmp_path),
        mode="dry-run",
    )
    assert res_dry1["consumption_state"] == "unconsumed_dry_run"
    assert not (tmp_path / "claims").exists()

    # 2. Second dry-run
    res_dry2 = claim_and_dispatch_approved(
        plan,
        authorization,
        binding,
        supplied_consumption_state=state,
        accepted_preflight=preflight,
        evaluation_timestamp=EVALUATION_TIMESTAMP,
        claim_created_at=CLAIM_TIMESTAMP,
        executor_registry_metadata=registry_metadata(plan),
        runtime_adapter_registry=dry_run_reg,
        output_root=str(tmp_path),
        mode="dry-run",
    )
    assert res_dry2["consumption_state"] == "unconsumed_dry_run"
    assert not (tmp_path / "claims").exists()

    # 3. Third step: execute-approved
    res_exec = claim_and_dispatch_approved(
        plan,
        authorization,
        binding,
        supplied_consumption_state=state,
        accepted_preflight=preflight,
        evaluation_timestamp=EVALUATION_TIMESTAMP,
        claim_created_at=CLAIM_TIMESTAMP,
        executor_registry_metadata=registry_metadata(plan),
        runtime_adapter_registry=real_run_reg,
        output_root=str(tmp_path),
        mode="execute-approved",
        confirm_execution=True,
        operator_confirmation_reference="op-ref-seq-test",
        confirm_network_execution=True,
    )
    assert res_exec["consumption_state"] == "claimed"
    assert (tmp_path / res_exec["claim_relative_path"]).exists()

    # 4. Fourth step: second execute-approved is replay-blocked
    with pytest.raises(OrchestrationError, match="authorization_already_claimed"):
        claim_and_dispatch_approved(
            plan,
            authorization,
            binding,
            supplied_consumption_state=state,
            accepted_preflight=preflight,
            evaluation_timestamp=EVALUATION_TIMESTAMP,
            claim_created_at=CLAIM_TIMESTAMP,
            executor_registry_metadata=registry_metadata(plan),
            runtime_adapter_registry=real_run_reg,
            output_root=str(tmp_path),
            mode="execute-approved",
            confirm_execution=True,
            operator_confirmation_reference="op-ref-seq-test",
            confirm_network_execution=True,
        )


def test_execute_approved_requires_all_confirmations_before_claim(tmp_path):
    plan, authorization, binding, state = artifacts()
    preflight = build_valid_preflight(tmp_path)
    run_reg = RuntimeAdapterRegistry([runtime_registration(plan, fake_adapter=False)])

    # Missing confirm_execution
    with pytest.raises(OrchestrationError, match="execution_confirmation_required"):
        claim_and_dispatch_approved(
            plan,
            authorization,
            binding,
            supplied_consumption_state=state,
            accepted_preflight=preflight,
            evaluation_timestamp=EVALUATION_TIMESTAMP,
            claim_created_at=CLAIM_TIMESTAMP,
            executor_registry_metadata=registry_metadata(plan),
            runtime_adapter_registry=run_reg,
            output_root=str(tmp_path),
            mode="execute-approved",
            confirm_execution=False,
            operator_confirmation_reference="op-ref-1",
            confirm_network_execution=True,
        )

    # Missing operator_confirmation_reference
    with pytest.raises(OrchestrationError, match="operator_confirmation_reference_required"):
        claim_and_dispatch_approved(
            plan,
            authorization,
            binding,
            supplied_consumption_state=state,
            accepted_preflight=preflight,
            evaluation_timestamp=EVALUATION_TIMESTAMP,
            claim_created_at=CLAIM_TIMESTAMP,
            executor_registry_metadata=registry_metadata(plan),
            runtime_adapter_registry=run_reg,
            output_root=str(tmp_path),
            mode="execute-approved",
            confirm_execution=True,
            operator_confirmation_reference="",
            confirm_network_execution=True,
        )

    # Missing confirm_network_execution for network_required preflight
    with pytest.raises(OrchestrationError, match="network_execution_confirmation_required"):
        claim_and_dispatch_approved(
            plan,
            authorization,
            binding,
            supplied_consumption_state=state,
            accepted_preflight=preflight,
            evaluation_timestamp=EVALUATION_TIMESTAMP,
            claim_created_at=CLAIM_TIMESTAMP,
            executor_registry_metadata=registry_metadata(plan),
            runtime_adapter_registry=run_reg,
            output_root=str(tmp_path),
            mode="execute-approved",
            confirm_execution=True,
            operator_confirmation_reference="op-ref-1",
            confirm_network_execution=False,
        )

    # Verify no claim file was written during failed confirmation calls
    assert not (tmp_path / "claims").exists()


def test_successful_execute_approved_creates_claim_and_dispatches(tmp_path):
    invoked = []

    def mock_real_adapter(request, context):
        invoked.append(request["operation_id"])
        return {"status": "succeeded"}

    plan, authorization, binding, state = artifacts()
    preflight = build_valid_preflight(tmp_path)
    run_reg = RuntimeAdapterRegistry([runtime_registration(plan, adapter=mock_real_adapter, fake_adapter=False)])

    res = claim_and_dispatch_approved(
        plan,
        authorization,
        binding,
        supplied_consumption_state=state,
        accepted_preflight=preflight,
        evaluation_timestamp=EVALUATION_TIMESTAMP,
        claim_created_at=CLAIM_TIMESTAMP,
        executor_registry_metadata=registry_metadata(plan),
        runtime_adapter_registry=run_reg,
        output_root=str(tmp_path),
        mode="execute-approved",
        confirm_execution=True,
        operator_confirmation_reference="op-ref-123",
        confirm_network_execution=True,
    )

    assert res["consumption_state"] == "claimed"
    assert res["claim_record"] is not None
    assert (tmp_path / res["claim_relative_path"]).exists()
    assert len(invoked) == 1
    assert res["aggregation_created"] is False
    assert res["execution_receipt_created"] is False


def test_adapter_failure_leaves_authorization_claimed(tmp_path):
    def failing_real_adapter(request, context):
        raise RuntimeError("network failure")

    plan, authorization, binding, state = artifacts()
    preflight = build_valid_preflight(tmp_path)
    run_reg = RuntimeAdapterRegistry([runtime_registration(plan, adapter=failing_real_adapter, fake_adapter=False)])

    res = claim_and_dispatch_approved(
        plan,
        authorization,
        binding,
        supplied_consumption_state=state,
        accepted_preflight=preflight,
        evaluation_timestamp=EVALUATION_TIMESTAMP,
        claim_created_at=CLAIM_TIMESTAMP,
        executor_registry_metadata=registry_metadata(plan),
        runtime_adapter_registry=run_reg,
        output_root=str(tmp_path),
        mode="execute-approved",
        confirm_execution=True,
        operator_confirmation_reference="op-ref-123",
        confirm_network_execution=True,
    )

    assert res["consumption_state"] == "claimed"
    assert res["dispatch_outcomes"][0]["status"] == "failed"
    assert res["dispatch_outcomes"][0]["error_code"] == "adapter_exception"
    # Claim file remains present on disk
    assert (tmp_path / res["claim_relative_path"]).exists()
