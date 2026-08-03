from __future__ import annotations

from scripts.m8r_05b_03.dispatch import RuntimeAdapterRegistry
from scripts.m8r_05b_03.orchestrator import execute_controlled_plan
from tests.unit.m8r_05b_03_test_helpers import (
    CLAIM_TIMESTAMP,
    EVALUATION_TIMESTAMP,
    artifacts,
    build_valid_preflight,
    registry_metadata,
    runtime_registration,
)


def test_end_to_end_dry_run_execution(tmp_path):
    plan, authorization, binding, state = artifacts()
    preflight = build_valid_preflight(tmp_path)
    run_reg = RuntimeAdapterRegistry([runtime_registration(plan, fake_adapter=True)])

    res = execute_controlled_plan(
        plan,
        authorization,
        binding,
        supplied_consumption_state=state,
        accepted_preflight=preflight,
        evaluation_timestamp=EVALUATION_TIMESTAMP,
        claim_created_at=CLAIM_TIMESTAMP,
        finalized_at="2026-07-23T00:32:00Z",
        executor_registry_metadata=registry_metadata(plan),
        runtime_adapter_registry=run_reg,
        output_root=str(tmp_path),
        mode="dry-run",
    )

    assert res["mode"] == "dry-run"
    assert res["consumption_state"] == "unconsumed_dry_run"
    assert res["aggregation_created"] is True
    assert res["execution_receipt_created"] is False
    assert res["execution_receipt"] is None
    assert res["evidence_bundle"] is None


def test_end_to_end_approved_execution(tmp_path):
    invoked = []

    def mock_adapter(request, context):
        invoked.append(request["operation_id"])
        return {"status": "succeeded"}

    plan, authorization, binding, state = artifacts()
    preflight = build_valid_preflight(tmp_path)
    run_reg = RuntimeAdapterRegistry([runtime_registration(plan, adapter=mock_adapter, fake_adapter=False)])

    res = execute_controlled_plan(
        plan,
        authorization,
        binding,
        supplied_consumption_state=state,
        accepted_preflight=preflight,
        evaluation_timestamp=EVALUATION_TIMESTAMP,
        claim_created_at=CLAIM_TIMESTAMP,
        finalized_at="2026-07-23T00:32:00Z",
        executor_registry_metadata=registry_metadata(plan),
        runtime_adapter_registry=run_reg,
        output_root=str(tmp_path),
        mode="execute-approved",
        confirm_execution=True,
        operator_confirmation_reference="op-e2e-ref",
        confirm_network_execution=True,
    )

    assert res["mode"] == "execute-approved"
    assert res["consumption_state"] == "consumed_success"
    assert res["aggregation_created"] is True
    assert res["execution_receipt_created"] is True
    assert res["execution_receipt"]["overall_status"] == "succeeded"
    assert res["evidence_bundle"]["overall_status"] == "succeeded"
    assert len(invoked) == 1

    # Verify artifacts exist on disk
    auth_id = authorization["authorization_id"]
    assert (tmp_path / "claims" / f"{auth_id}.consumption-record.json").exists()
    assert (tmp_path / "receipts" / f"{auth_id}.execution-receipt.json").exists()
    assert (tmp_path / "bundles" / f"{auth_id}.evidence-bundle.json").exists()
