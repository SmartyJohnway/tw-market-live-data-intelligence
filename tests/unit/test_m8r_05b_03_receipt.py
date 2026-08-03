from __future__ import annotations

import json

from jsonschema import Draft202012Validator, FormatChecker

from scripts.m8r_05b_03.consumption_claim import atomic_claim_authorization
from scripts.m8r_05b_03.receipt import (
    build_evidence_bundle,
    build_execution_receipt,
    finalize_consumption_and_write_receipt,
)
from tests.unit.m8r_05b_03_test_helpers import (
    CLAIM_TIMESTAMP,
    ROOT,
    artifacts,
    build_valid_preflight,
)


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

    agg = {
        "overall_status": "succeeded",
        "total_operations": 1,
        "succeeded_operations": 1,
        "failed_operations": 0,
        "operation_receipts": [{
            "operation_id": preflight["approved_operation_order"][0],
            "executor_id": "exec1",
            "capability_id": "cap1",
            "status": "succeeded",
            "error_code": None,
            "execution_request_id": "umereq-v1-00000000000000000001",
            "execution_request_hash": "00" * 32,
            "result_item_count": 10,
            "artifact_relative_path": "art.json",
        }],
    }

    final_time = "2026-07-23T00:32:00Z"
    receipt = build_execution_receipt(preflight, claim_rec, agg, finalized_at=final_time)
    bundle = build_evidence_bundle(preflight, claim_rec, receipt, finalized_at=final_time)

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
