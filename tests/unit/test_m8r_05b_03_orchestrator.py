from __future__ import annotations

import hashlib
import json

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
    op = plan["operations"][0]

    def fake_dry_adapter(request, context):
        return {
            "schema_version": "unified_market_evidence_operation_result.v1",
            "operation_id": request["operation_id"],
            "execution_request_id": request["execution_request_id"],
            "execution_request_hash": request["execution_request_hash"],
            "executor_id": request["executor_id"],
            "capability_id": request["capability_id"],
            "evidence_contract": op["expected_evidence_contract"],
            "status": "succeeded",
            "error_code": None,
            "result_item_count": 0,
            "evidence_artifacts": [],
            "warnings": [],
        }

    run_reg = RuntimeAdapterRegistry([runtime_registration(plan, adapter=fake_dry_adapter, fake_adapter=True)])

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


def test_end_to_end_approved_execution_with_real_evidence_artifact(tmp_path):
    plan, authorization, binding, state = artifacts()
    preflight = build_valid_preflight(tmp_path)
    op = plan["operations"][0]
    art_rel = f"evidence/{op['operation_id']}.json"

    invoked = []

    def mock_real_adapter(request, context):
        invoked.append(request["operation_id"])

        # Materialize real evidence artifact file on disk
        dest_path = tmp_path / art_rel
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        content = json.dumps({"market": "TWSE", "items": [{"id": 100}]}).encode("utf-8")
        dest_path.write_bytes(content)
        sha = hashlib.sha256(content).hexdigest()

        return {
            "schema_version": "unified_market_evidence_operation_result.v1",
            "operation_id": request["operation_id"],
            "execution_request_id": request["execution_request_id"],
            "execution_request_hash": request["execution_request_hash"],
            "executor_id": request["executor_id"],
            "capability_id": request["capability_id"],
            "evidence_contract": op["expected_evidence_contract"],
            "status": "succeeded",
            "error_code": None,
            "result_item_count": 1,
            "evidence_artifacts": [
                {
                    "relative_path": art_rel,
                    "sha256": sha,
                    "schema_version": "test.evidence.v1",
                    "byte_size": len(content),
                    "item_count": 1,
                }
            ],
            "warnings": [],
        }

    run_reg = RuntimeAdapterRegistry([runtime_registration(plan, adapter=mock_real_adapter, fake_adapter=False)])

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
    assert len(res["evidence_bundle"]["artifact_inventory"]) == 1
    assert len(invoked) == 1

    # Verify artifacts exist on disk
    auth_id = authorization["authorization_id"]
    assert (tmp_path / "claims" / f"{auth_id}.consumption-record.json").exists()
    assert (tmp_path / "receipts" / f"{auth_id}.execution-receipt.json").exists()
    assert (tmp_path / "bundles" / f"{auth_id}.evidence-bundle.json").exists()
    assert (tmp_path / art_rel).exists()
