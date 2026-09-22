from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

import pytest

from scripts.m8r_05b_03.dispatch import (
    DispatchRuntimeContext,
    RuntimeAdapterRegistry,
    dispatch_prepared,
    prepare_dispatch,
)
from scripts.m8r_05b_03.errors import OrchestrationError
from scripts.m8r_05b_03.registry import ExecutorMetadataRegistry
from scripts.m8r_filesystem_safety import safe_destination
from tests.unit.m8r_05b_03_test_helpers import (
    PLAN,
    artifacts,
    build_valid_preflight,
    registry_metadata,
    runtime_registration,
)


def test_succeeded_operation_with_empty_artifacts_rejected(tmp_path):
    preflight = build_valid_preflight(tmp_path)
    meta_reg = ExecutorMetadataRegistry.from_json(registry_metadata(PLAN))

    def bad_adapter(request, context):
        from scripts.m8r_05b_03.dispatch import request_identity
        req_id, req_hash = request_identity(request)
        return {
            "schema_version": "unified_market_evidence_operation_result.v1",
            "operation_id": request["operation_id"],
            "execution_request_id": req_id,
            "execution_request_hash": req_hash,
            "executor_id": request["executor_id"],
            "capability_id": request["capability_id"],
            "evidence_contract": request.get("evidence_contract") or "bounded normalized source observation with source health/currentness",
            "status": "succeeded",
            "error_code": None,
            "result_item_count": 0,
            "evidence_artifacts": [],  # MinItems: 1 violation!
            "warnings": [],
        }

    run_reg = RuntimeAdapterRegistry([runtime_registration(PLAN, adapter=bad_adapter)])
    prepared = prepare_dispatch(preflight, meta_reg, run_reg, mode="dry-run")
    with pytest.raises(OrchestrationError, match="operation_result_schema_invalid"):
        dispatch_prepared(prepared, governed_output_root=str(tmp_path), mode="dry-run")


def test_succeeded_operation_with_zero_result_explicit_empty_artifact_accepted(tmp_path):
    preflight = build_valid_preflight(tmp_path)
    meta_reg = ExecutorMetadataRegistry.from_json(registry_metadata(PLAN))

    def zero_result_adapter(request, context):
        from scripts.m8r_05b_03.dispatch import request_identity
        req_id, req_hash = request_identity(request)
        op_id = request["operation_id"]
        rel_path = f"evidence/{op_id}_empty.json"
        content = json.dumps([]).encode("utf-8")
        dest = safe_destination(context.governed_output_root, rel_path, create_parent=True)
        dest.path.write_bytes(content)

        return {
            "schema_version": "unified_market_evidence_operation_result.v1",
            "operation_id": op_id,
            "execution_request_id": req_id,
            "execution_request_hash": req_hash,
            "executor_id": request["executor_id"],
            "capability_id": request["capability_id"],
            "evidence_contract": request.get("evidence_contract") or "bounded normalized source observation with source health/currentness",
            "status": "succeeded",
            "error_code": None,
            "result_item_count": 0,
            "evidence_artifacts": [
                {
                    "relative_path": rel_path,
                    "sha256": sha256(content).hexdigest(),
                    "schema_version": "unified_market_evidence_item.v1",
                    "byte_size": len(content),
                    "item_count": 0,
                }
            ],
            "warnings": ["zero records returned"],
        }

    run_reg = RuntimeAdapterRegistry([runtime_registration(PLAN, adapter=zero_result_adapter, fake_adapter=False)])
    prepared = prepare_dispatch(preflight, meta_reg, run_reg, mode="execute-approved")
    outcomes = dispatch_prepared(prepared, governed_output_root=str(tmp_path), mode="execute-approved")
    assert len(outcomes) == 1
    assert outcomes[0]["status"] == "succeeded"
    assert outcomes[0]["result_item_count"] == 0
    assert len(outcomes[0]["evidence_artifacts"]) == 1


def test_result_item_count_mismatch_rejected(tmp_path):
    preflight = build_valid_preflight(tmp_path)
    meta_reg = ExecutorMetadataRegistry.from_json(registry_metadata(PLAN))

    def count_mismatch_adapter(request, context):
        from scripts.m8r_05b_03.dispatch import request_identity
        req_id, req_hash = request_identity(request)
        op_id = request["operation_id"]
        rel_path = f"evidence/{op_id}.json"
        content = json.dumps([{"item": 1}]).encode("utf-8")
        dest = safe_destination(context.governed_output_root, rel_path, create_parent=True)
        dest.path.write_bytes(content)

        return {
            "schema_version": "unified_market_evidence_operation_result.v1",
            "operation_id": op_id,
            "execution_request_id": req_id,
            "execution_request_hash": req_hash,
            "executor_id": request["executor_id"],
            "capability_id": request["capability_id"],
            "evidence_contract": request.get("evidence_contract") or "bounded normalized source observation with source health/currentness",
            "status": "succeeded",
            "error_code": None,
            "result_item_count": 5,  # Mismatch with artifact item_count = 1!
            "evidence_artifacts": [
                {
                    "relative_path": rel_path,
                    "sha256": sha256(content).hexdigest(),
                    "schema_version": "unified_market_evidence_item.v1",
                    "byte_size": len(content),
                    "item_count": 1,
                }
            ],
            "warnings": [],
        }

    run_reg = RuntimeAdapterRegistry([runtime_registration(PLAN, adapter=count_mismatch_adapter, fake_adapter=False)])
    prepared = prepare_dispatch(preflight, meta_reg, run_reg, mode="execute-approved")
    with pytest.raises(OrchestrationError, match="operation_result_item_count_mismatch"):
        dispatch_prepared(prepared, governed_output_root=str(tmp_path), mode="execute-approved")


def test_v2_primary_and_supporting_artifacts_are_validated_independently(tmp_path):
    preflight = build_valid_preflight(tmp_path)
    op_id = preflight["approved_operation_order"][0]
    preflight["resolved_operation_bindings"][op_id]["expected_evidence_contract"] = "trading_status_context_evidence.v1"
    meta_reg = ExecutorMetadataRegistry.from_json(registry_metadata(PLAN, expected_evidence_contract="trading_status_context_evidence.v1"))

    def v2_adapter(request, context):
        req_id, req_hash = request["execution_request_id"], request["execution_request_hash"]
        primary_path, sidecar_path = "evidence/typed.json", "evidence/governance.json"
        primary, sidecar = b'{"typed":true}', b'{"governance":true}'
        safe_destination(context.governed_output_root, primary_path, create_parent=True).path.write_bytes(primary)
        safe_destination(context.governed_output_root, sidecar_path, create_parent=True).path.write_bytes(sidecar)
        return {"schema_version": "unified_market_evidence_operation_result.v2", "operation_id": request["operation_id"],
                "execution_request_id": req_id, "execution_request_hash": req_hash, "executor_id": request["executor_id"],
                "capability_id": request["capability_id"], "evidence_contract": "trading_status_context_evidence.v1",
                "status": "succeeded", "error_code": None, "result_item_count": 1, "warnings": [], "evidence_artifacts": [
                    {"relative_path": primary_path, "sha256": sha256(primary).hexdigest(), "schema_version": "trading_status_context_evidence.v1", "byte_size": len(primary), "item_count": 1, "evidence_contract": "trading_status_context_evidence.v1", "artifact_role": "primary_evidence"},
                    {"relative_path": sidecar_path, "sha256": sha256(sidecar).hexdigest(), "schema_version": "phase_h_source_attempt_governance.v1", "byte_size": len(sidecar), "item_count": 1, "evidence_contract": "phase_h_source_attempt_governance.v1", "artifact_role": "supporting_governance"},
                ]}

    registration = runtime_registration(PLAN, adapter=v2_adapter, fake_adapter=False, expected_evidence_contract="trading_status_context_evidence.v1")
    prepared = prepare_dispatch(preflight, meta_reg, RuntimeAdapterRegistry([registration]), mode="execute-approved")
    result = dispatch_prepared(prepared, governed_output_root=str(tmp_path), mode="execute-approved")[0]
    assert result["schema_version"] == "unified_market_evidence_operation_result.v2"
    assert result["result_item_count"] == 1


@pytest.mark.parametrize("artifact_role, artifact_contract, item_count, code", [
    ("primary_evidence", "phase_h_source_attempt_governance.v1", 1, "operation_result_artifact_contract_mismatch"),
    ("supporting_governance", "phase_h_source_attempt_governance.v1", 0, "operation_result_primary_artifact_missing"),
])
def test_v2_rejects_invalid_artifact_roles_and_contracts(tmp_path, artifact_role, artifact_contract, item_count, code):
    preflight = build_valid_preflight(tmp_path)
    op_id = preflight["approved_operation_order"][0]
    preflight["resolved_operation_bindings"][op_id]["expected_evidence_contract"] = "trading_status_context_evidence.v1"
    meta_reg = ExecutorMetadataRegistry.from_json(registry_metadata(PLAN, expected_evidence_contract="trading_status_context_evidence.v1"))

    def bad_adapter(request, context):
        body = b'{}'; path = "evidence/item.json"
        safe_destination(context.governed_output_root, path, create_parent=True).path.write_bytes(body)
        return {"schema_version": "unified_market_evidence_operation_result.v2", "operation_id": request["operation_id"], "execution_request_id": request["execution_request_id"], "execution_request_hash": request["execution_request_hash"], "executor_id": request["executor_id"], "capability_id": request["capability_id"], "evidence_contract": "trading_status_context_evidence.v1", "status": "succeeded", "error_code": None, "result_item_count": item_count, "warnings": [], "evidence_artifacts": [{"relative_path": path, "sha256": sha256(body).hexdigest(), "schema_version": artifact_contract, "byte_size": len(body), "item_count": 1, "evidence_contract": artifact_contract, "artifact_role": artifact_role}]}

    registration = runtime_registration(PLAN, adapter=bad_adapter, fake_adapter=False, expected_evidence_contract="trading_status_context_evidence.v1")
    prepared = prepare_dispatch(preflight, meta_reg, RuntimeAdapterRegistry([registration]), mode="execute-approved")
    with pytest.raises(OrchestrationError, match=code):
        dispatch_prepared(prepared, governed_output_root=str(tmp_path), mode="execute-approved")


def test_unknown_operation_result_version_fails_closed(tmp_path):
    preflight = build_valid_preflight(tmp_path)
    meta_reg = ExecutorMetadataRegistry.from_json(registry_metadata(PLAN))

    def unknown_adapter(request, context):
        return {"schema_version": "unified_market_evidence_operation_result.v999", "operation_id": request["operation_id"]}

    prepared = prepare_dispatch(preflight, meta_reg, RuntimeAdapterRegistry([runtime_registration(PLAN, adapter=unknown_adapter)]), mode="dry-run")
    with pytest.raises(OrchestrationError, match="operation_result_schema_version_unsupported"):
        dispatch_prepared(prepared, governed_output_root=str(tmp_path), mode="dry-run")
