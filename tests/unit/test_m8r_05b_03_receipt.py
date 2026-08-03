from __future__ import annotations

import json

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from scripts.m8r_05b_03.consumption_claim import atomic_claim_authorization
from scripts.m8r_05b_03.dispatch import request_identity
from scripts.m8r_05b_03.errors import OrchestrationError
from scripts.m8r_05b_03.receipt import (
    build_evidence_bundle,
    build_execution_receipt,
    finalize_consumption_and_write_receipt,
    validate_finalization_timestamps,
)
from tests.unit.m8r_05b_03_test_helpers import (
    CLAIM_TIMESTAMP,
    ROOT,
    artifacts,
    build_valid_preflight,
)


def test_temporal_inversion_rejected():
    with pytest.raises(OrchestrationError, match="temporal_inversion_detected"):
        validate_finalization_timestamps("2026-07-23T00:31:00Z", "2026-07-23T00:30:00Z")


def test_build_and_validate_receipt_and_bundle(tmp_path):
    _plan, _auth, _bind, state = artifacts()
    preflight = build_valid_preflight(tmp_path)
    claim_rec, claim_path = atomic_claim_authorization(
        preflight,
        state,
        output_root=str(tmp_path),
        claim_created_at=CLAIM_TIMESTAMP,
        operator_confirmation_reference="op-receipt-test",
    )

    op_id = preflight["approved_operation_order"][0]
    req = preflight["bounded_execution_requests"][0]
    req_id, req_hash = request_identity(req)

    agg = {
        "overall_status": "succeeded",
        "total_operations": 1,
        "succeeded_operations": 1,
        "failed_operations": 0,
        "operation_receipts": [{
            "operation_id": op_id,
            "executor_id": req["executor_id"],
            "capability_id": req["capability_id"],
            "status": "succeeded",
            "error_code": None,
            "execution_request_id": req_id,
            "execution_request_hash": req_hash,
            "result_item_count": 10,
            "evidence_artifacts": [{
                "relative_path": req["relative_contained_output_path"],
                "sha256": "00" * 32,
                "schema_version": "test.v1",
                "byte_size": 20,
                "item_count": 10,
            }],
        }],
        "operation_evidence_entries": [{
            "operation_id": op_id,
            "status": "succeeded",
            "error_code": None,
            "result_item_count": 10,
            "artifacts": [{
                "relative_path": req["relative_contained_output_path"],
                "sha256": "00" * 32,
                "byte_size": 20,
                "item_count": 10,
            }],
        }],
        "artifact_inventory": [{
            "relative_path": req["relative_contained_output_path"],
            "sha256": "00" * 32,
            "byte_size": 20,
            "item_count": 10,
            "evidence_contract": "test_contract",
        }],
        "total_item_count": 10,
    }

    final_time = "2026-07-23T00:32:00Z"
    receipt = build_execution_receipt(preflight, claim_rec, agg, finalized_at=final_time)
    bundle = build_evidence_bundle(preflight, claim_rec, receipt, agg, finalized_at=final_time)

    rec_schema = json.loads((ROOT / "schemas/unified_market_evidence_execution_receipt.v1.schema.json").read_text(encoding="utf-8"))
    bun_schema = json.loads((ROOT / "schemas/unified_market_evidence_bundle.v1.schema.json").read_text(encoding="utf-8"))

    assert list(Draft202012Validator(rec_schema, format_checker=FormatChecker()).iter_errors(receipt)) == []
    assert list(Draft202012Validator(bun_schema, format_checker=FormatChecker()).iter_errors(bundle)) == []

    final_claim, rec_written, bun_written = finalize_consumption_and_write_receipt(
        preflight,
        claim_rec,
        claim_path,
        agg,
        output_root=str(tmp_path),
        finalized_at=final_time,
    )

    assert final_claim["state"] == "consumed_success"
    assert final_claim["execution_receipt_id"] == receipt["execution_receipt_id"]
    assert (tmp_path / claim_path).exists()
    assert (tmp_path / "receipts" / f"{preflight['authorization_id']}.execution-receipt.json").exists()
    assert (tmp_path / "bundles" / f"{preflight['authorization_id']}.evidence-bundle.json").exists()


def test_idempotent_finalization_succeeds(tmp_path):
    _plan, _auth, _bind, state = artifacts()
    preflight = build_valid_preflight(tmp_path)
    claim_rec, claim_path = atomic_claim_authorization(
        preflight,
        state,
        output_root=str(tmp_path),
        claim_created_at=CLAIM_TIMESTAMP,
        operator_confirmation_reference="op-receipt-test",
    )

    op_id = preflight["approved_operation_order"][0]
    req = preflight["bounded_execution_requests"][0]
    req_id, req_hash = request_identity(req)

    agg = {
        "overall_status": "succeeded",
        "total_operations": 1,
        "succeeded_operations": 1,
        "failed_operations": 0,
        "operation_receipts": [{
            "operation_id": op_id,
            "executor_id": req["executor_id"],
            "capability_id": req["capability_id"],
            "status": "succeeded",
            "error_code": None,
            "execution_request_id": req_id,
            "execution_request_hash": req_hash,
            "result_item_count": 1,
            "evidence_artifacts": [],
        }],
        "operation_evidence_entries": [{
            "operation_id": op_id,
            "status": "succeeded",
            "error_code": None,
            "result_item_count": 1,
            "artifacts": [],
        }],
        "artifact_inventory": [],
        "total_item_count": 1,
    }

    final_time = "2026-07-23T00:32:00Z"
    f1_claim, f1_rec, f1_bun = finalize_consumption_and_write_receipt(
        preflight,
        claim_rec,
        claim_path,
        agg,
        output_root=str(tmp_path),
        finalized_at=final_time,
    )

    # Second finalization call with exact same inputs returns idempotent success
    f2_claim, f2_rec, f2_bun = finalize_consumption_and_write_receipt(
        preflight,
        claim_rec,
        claim_path,
        agg,
        output_root=str(tmp_path),
        finalized_at=final_time,
    )

    assert f2_claim["state"] == "consumed_success"
    assert f2_rec["execution_receipt_id"] == f1_rec["execution_receipt_id"]
