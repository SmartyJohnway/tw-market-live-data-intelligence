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
