from __future__ import annotations

import hashlib
import json

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


def test_valid_operation_result_with_real_contained_evidence_artifact(tmp_path):
    plan, authorization, binding, state = artifacts()
    preflight = build_valid_preflight(tmp_path)
    op = plan["operations"][0]
    req = preflight["bounded_execution_requests"][0]

    # Create real evidence artifact file on disk under output_root
    art_rel = f"evidence/{op['operation_id']}.json"
    art_path = tmp_path / art_rel
    art_path.parent.mkdir(parents=True, exist_ok=True)
    art_data = json.dumps({"market": "TW", "items": [1, 2, 3]}).encode("utf-8")
    art_path.write_bytes(art_data)
    art_sha = hashlib.sha256(art_data).hexdigest()

    def mock_real_adapter(request, context):
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
            "result_item_count": 3,
            "evidence_artifacts": [
                {
                    "relative_path": art_rel,
                    "sha256": art_sha,
                    "schema_version": "test.evidence.v1",
                    "byte_size": len(art_data),
                    "item_count": 3,
                }
            ],
            "warnings": [],
        }

    meta_reg = ExecutorMetadataRegistry.from_json(registry_metadata(plan))
    run_reg = RuntimeAdapterRegistry([runtime_registration(plan, adapter=mock_real_adapter, fake_adapter=False)])

    prepared = prepare_dispatch(preflight, meta_reg, run_reg, mode="execute-approved")
    outcomes = dispatch_prepared(prepared, governed_output_root=str(tmp_path), mode="execute-approved")

    assert len(outcomes) == 1
    assert outcomes[0]["status"] == "succeeded"
    assert outcomes[0]["evidence_artifacts"][0]["sha256"] == art_sha


def test_missing_evidence_artifact_file_rejected(tmp_path):
    plan, authorization, binding, state = artifacts()
    preflight = build_valid_preflight(tmp_path)
    op = plan["operations"][0]
    art_rel = f"evidence/{op['operation_id']}.json"

    def mock_adapter(request, context):
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
                    "sha256": "00" * 32,
                    "schema_version": "test.v1",
                    "byte_size": 100,
                    "item_count": 1,
                }
            ],
            "warnings": [],
        }

    meta_reg = ExecutorMetadataRegistry.from_json(registry_metadata(plan))
    run_reg = RuntimeAdapterRegistry([runtime_registration(plan, adapter=mock_adapter, fake_adapter=False)])

    prepared = prepare_dispatch(preflight, meta_reg, run_reg, mode="execute-approved")
    with pytest.raises(OrchestrationError, match="evidence_artifact_missing"):
        dispatch_prepared(prepared, governed_output_root=str(tmp_path), mode="execute-approved")


def test_evidence_artifact_hash_mismatch_rejected(tmp_path):
    plan, authorization, binding, state = artifacts()
    preflight = build_valid_preflight(tmp_path)
    op = plan["operations"][0]
    art_rel = f"evidence/{op['operation_id']}.json"

    art_path = tmp_path / art_rel
    art_path.parent.mkdir(parents=True, exist_ok=True)
    art_data = b"some data"
    art_path.write_bytes(art_data)

    def mock_adapter(request, context):
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
                    "sha256": "ff" * 32,  # Wrong hash
                    "schema_version": "test.v1",
                    "byte_size": len(art_data),
                    "item_count": 1,
                }
            ],
            "warnings": [],
        }

    meta_reg = ExecutorMetadataRegistry.from_json(registry_metadata(plan))
    run_reg = RuntimeAdapterRegistry([runtime_registration(plan, adapter=mock_adapter, fake_adapter=False)])

    prepared = prepare_dispatch(preflight, meta_reg, run_reg, mode="execute-approved")
    with pytest.raises(OrchestrationError, match="evidence_artifact_hash_mismatch"):
        dispatch_prepared(prepared, governed_output_root=str(tmp_path), mode="execute-approved")
