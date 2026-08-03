from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.m8r_05b_03.canonical import sha256_json
from scripts.m8r_05b_03.errors import OrchestrationError
from scripts.m8r_05b_03.evidence_aggregation import aggregate_dispatch_outcomes
from scripts.m8r_05b_03.receipt import (
    build_evidence_bundle,
    build_execution_receipt,
    finalize_consumption_and_write_receipt,
    validate_finalization_timestamps,
)
from scripts.m8r_filesystem_safety import safe_destination
from tests.unit.m8r_05b_03_test_helpers import (
    CLAIM_TIMESTAMP,
    EVALUATION_TIMESTAMP,
    PLAN,
    artifacts,
    build_valid_preflight,
    default_mock_adapter,
    registry_metadata,
)


class DummyContext:
    def __init__(self, root: str):
        self.governed_output_root = root
        self.mode = "execute-approved"


def test_validate_finalization_timestamps_rejects_inversion():
    with pytest.raises(OrchestrationError, match="temporal_inversion_detected"):
        validate_finalization_timestamps("2026-07-23T00:30:00Z", "2026-07-23T00:29:59Z")


def test_build_receipt_and_bundle_with_warnings(tmp_path):
    preflight = build_valid_preflight(tmp_path)
    ctx = DummyContext(str(tmp_path))
    req = preflight["bounded_execution_requests"][0]
    out1 = default_mock_adapter(req, ctx)
    out1["warnings"] = ["warning_1", "warning_2"]

    agg = aggregate_dispatch_outcomes(preflight, [out1])
    assert agg["warnings"] == ["warning_1", "warning_2"]

    claim_rec = {
        "schema_version": "unified_market_evidence_consumption_record.v1",
        "authorization_id": preflight["authorization_id"],
        "authorization_hash": preflight["authorization_hash"],
        "consumption_binding_id": preflight["consumption_binding_id"],
        "consumption_binding_hash": preflight["consumption_binding_hash"],
        "preflight_id": preflight["preflight_id"],
        "preflight_identity_hash": preflight["preflight_identity_hash"],
        "preflight_artifact_hash": preflight["preflight_artifact_hash"],
        "claim_id": "umecl-v1-01234567890123456789",
        "claim_hash": "a" * 64,
        "state": "claimed",
        "execution_mode": "execute-approved",
        "execution_confirmed": True,
        "operator_confirmation_reference": "ref-1",
        "network_execution_confirmed": True,
        "confirmation_bound_at": EVALUATION_TIMESTAMP,
        "claim_created_at": CLAIM_TIMESTAMP,
        "attempt_count": 1,
        "claimed_by_component": "unit_test",
    }

    rec = build_execution_receipt(preflight, claim_rec, agg, finalized_at="2026-07-23T00:32:00Z")
    assert rec["warnings"] == ["warning_1", "warning_2"]

    bun = build_evidence_bundle(preflight, claim_rec, rec, agg, finalized_at="2026-07-23T00:32:00Z")
    assert bun["warnings"] == ["warning_1", "warning_2"]
    assert "schema_version" in bun["artifact_inventory"][0]


def test_finalization_transaction_journal_staging_and_idempotent_recovery(tmp_path):
    from scripts.m8r_05b_03.controlled_dispatch import claim_and_dispatch_approved
    from scripts.m8r_05b_03.dispatch import RuntimeAdapterRegistry

    plan, authorization, binding, state = artifacts()
    preflight = build_valid_preflight(tmp_path)
    run_reg = RuntimeAdapterRegistry([default_mock_adapter_registration(plan)])

    disp_res = claim_and_dispatch_approved(
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
        operator_confirmation_reference="op-ref",
        confirm_network_execution=True,
    )

    claim_rec = disp_res["claim_record"]
    claim_rel = disp_res["claim_relative_path"]
    outcomes = disp_res["dispatch_outcomes"]
    agg = aggregate_dispatch_outcomes(preflight, outcomes)

    # First finalization
    fin_claim, rec, bun = finalize_consumption_and_write_receipt(
        preflight,
        claim_rec,
        claim_rel,
        agg,
        output_root=str(tmp_path),
        finalized_at="2026-07-23T00:35:00Z",
    )

    assert fin_claim["state"] == "consumed_success"
    j_path = tmp_path / f"finalization/{preflight['authorization_id']}.finalization-journal.json"
    assert j_path.is_file()
    j_data = json.loads(j_path.read_text(encoding="utf-8"))
    assert j_data["state"] == "claim_committed"

    # Second finalization (idempotent repeat)
    fin_claim2, rec2, bun2 = finalize_consumption_and_write_receipt(
        preflight,
        claim_rec,
        claim_rel,
        agg,
        output_root=str(tmp_path),
        finalized_at="2026-07-23T00:35:00Z",
    )

    assert fin_claim2["state"] == "consumed_success"
    assert rec2["execution_receipt_hash"] == rec["execution_receipt_hash"]
    assert bun2["bundle_hash"] == bun["bundle_hash"]


def test_finalization_corrupted_artifact_fails_idempotent_check(tmp_path):
    from scripts.m8r_05b_03.controlled_dispatch import claim_and_dispatch_approved
    from scripts.m8r_05b_03.dispatch import RuntimeAdapterRegistry

    plan, authorization, binding, state = artifacts()
    preflight = build_valid_preflight(tmp_path)
    run_reg = RuntimeAdapterRegistry([default_mock_adapter_registration(plan)])

    disp_res = claim_and_dispatch_approved(
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
        operator_confirmation_reference="op-ref",
        confirm_network_execution=True,
    )

    claim_rec = disp_res["claim_record"]
    claim_rel = disp_res["claim_relative_path"]
    outcomes = disp_res["dispatch_outcomes"]
    agg = aggregate_dispatch_outcomes(preflight, outcomes)

    finalize_consumption_and_write_receipt(
        preflight,
        claim_rec,
        claim_rel,
        agg,
        output_root=str(tmp_path),
        finalized_at="2026-07-23T00:35:00Z",
    )

    # Corrupt receipt file on disk
    rec_path = tmp_path / f"receipts/{preflight['authorization_id']}.execution-receipt.json"
    rec_path.write_text("{corrupt json", encoding="utf-8")

    with pytest.raises(OrchestrationError, match="final_artifact_verification_failed"):
        finalize_consumption_and_write_receipt(
            preflight,
            claim_rec,
            claim_rel,
            agg,
            output_root=str(tmp_path),
            finalized_at="2026-07-23T00:35:00Z",
        )


def default_mock_adapter_registration(plan):
    from tests.unit.m8r_05b_03_test_helpers import runtime_registration
    return runtime_registration(plan, fake_adapter=False)
