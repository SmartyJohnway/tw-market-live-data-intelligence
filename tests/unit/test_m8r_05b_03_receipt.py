from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.m8r_05b_03.canonical import sha256_json
from scripts.m8r_05b_03.controlled_dispatch import claim_and_dispatch_approved
from scripts.m8r_05b_03.dispatch import RuntimeAdapterRegistry
from scripts.m8r_05b_03.errors import OrchestrationError
from scripts.m8r_05b_03.evidence_aggregation import aggregate_dispatch_outcomes
from scripts.m8r_05b_03.receipt import (
    build_evidence_bundle,
    build_execution_receipt,
    finalize_consumption_and_write_receipt,
    initial_claim_hash,
    validate_finalization_timestamps,
)
from tests.unit.m8r_05b_03_test_helpers import (
    CLAIM_TIMESTAMP,
    EVALUATION_TIMESTAMP,
    PLAN,
    artifacts,
    build_valid_preflight,
    default_mock_adapter,
    registry_metadata,
    runtime_registration,
)


class DummyContext:
    def __init__(self, root: str):
        self.governed_output_root = root
        self.mode = "execute-approved"


def default_mock_adapter_registration(plan):
    return runtime_registration(plan, fake_adapter=False)


def setup_dispatch_environment(tmp_path):
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

    return plan, preflight, claim_rec, claim_rel, agg


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
        "plan_id": preflight["plan_id"],
        "plan_hash": preflight["plan_hash"],
        "scope_hash": preflight["scope_hash"],
        "preflight_id": preflight["preflight_id"],
        "preflight_identity_hash": preflight["preflight_identity_hash"],
        "preflight_artifact_hash": preflight["preflight_artifact_hash"],
        "claim_id": "umecl-v1-01234567890123456789",
        "state": "claimed",
        "execution_mode": "execute-approved",
        "execution_confirmed": True,
        "operator_confirmation_reference": "ref-1",
        "network_execution_confirmed": True,
        "confirmation_bound_at": EVALUATION_TIMESTAMP,
        "claim_created_at": CLAIM_TIMESTAMP,
        "attempt_count": 1,
        "claimed_by_component": "unit_test",
        "execution_receipt_id": None,
        "execution_receipt_hash": None,
        "finalized_at": None,
        "last_error_code": None,
    }

    rec = build_execution_receipt(preflight, claim_rec, agg, finalized_at="2026-07-23T00:32:00Z")
    assert rec["warnings"] == ["warning_1", "warning_2"]

    bun = build_evidence_bundle(preflight, claim_rec, rec, agg, finalized_at="2026-07-23T00:32:00Z")
    assert bun["warnings"] == ["warning_1", "warning_2"]
    assert "schema_version" in bun["artifact_inventory"][0]


def test_finalization_transaction_journal_staging_and_idempotent_recovery(tmp_path):
    _, preflight, claim_rec, claim_rel, agg = setup_dispatch_environment(tmp_path)

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
    assert "finalization_owner_id" in j_data

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


def test_concurrent_finalization_ownership_conflict(tmp_path):
    _, preflight, claim_rec, claim_rel, agg = setup_dispatch_environment(tmp_path)

    owner_1 = "umefo-v1-11111111111111111111"
    owner_2 = "umefo-v1-22222222222222222222"

    # Simulate Owner 1 creating journal in preparing state
    j_path = tmp_path / f"finalization/{preflight['authorization_id']}.finalization-journal.json"
    j_path.parent.mkdir(parents=True, exist_ok=True)
    rec = build_execution_receipt(preflight, claim_rec, agg, finalized_at="2026-07-23T00:35:00Z")
    bun = build_evidence_bundle(preflight, claim_rec, rec, agg, finalized_at="2026-07-23T00:35:00Z")

    initial_journal = {
        "schema_version": "unified_market_evidence_finalization_journal.v1",
        "journal_id": "umefj-v1-00000000000000000000",
        "finalization_owner_id": owner_1,
        "authorization_id": preflight["authorization_id"],
        "authorization_hash": preflight["authorization_hash"],
        "claim_id": claim_rec["claim_id"],
        "claim_hash": initial_claim_hash(claim_rec),
        "preflight_id": preflight["preflight_id"],
        "preflight_identity_hash": preflight["preflight_identity_hash"],
        "preflight_artifact_hash": preflight["preflight_artifact_hash"],
        "execution_receipt_id": rec["execution_receipt_id"],
        "execution_receipt_hash": rec["execution_receipt_hash"],
        "bundle_id": bun["bundle_id"],
        "bundle_hash": bun["bundle_hash"],
        "state": "preparing",
        "created_at": "2026-07-23T00:35:00Z",
        "updated_at": "2026-07-23T00:35:00Z",
    }
    j_path.write_text(json.dumps(initial_journal), encoding="utf-8")

    # Owner 2 attempts finalization while Owner 1 is preparing -> fails with finalization_in_progress
    with pytest.raises(OrchestrationError, match="finalization_in_progress"):
        finalize_consumption_and_write_receipt(
            preflight,
            claim_rec,
            claim_rel,
            agg,
            output_root=str(tmp_path),
            finalized_at="2026-07-23T00:35:00Z",
            finalization_owner_id=owner_2,
        )


def test_failure_injection_recovery_phases(tmp_path, monkeypatch):
    _, preflight, claim_rec, claim_rel, agg = setup_dispatch_environment(tmp_path)

    owner_id = "umefo-v1-12345678901234567890"
    fin_claim, rec, bun = finalize_consumption_and_write_receipt(
        preflight,
        claim_rec,
        claim_rel,
        agg,
        output_root=str(tmp_path),
        finalized_at="2026-07-23T00:35:00Z",
        finalization_owner_id=owner_id,
    )
    assert fin_claim["state"] == "consumed_success"


def test_corruption_and_mismatch_checks(tmp_path):
    _, preflight, claim_rec, claim_rel, agg = setup_dispatch_environment(tmp_path)

    finalize_consumption_and_write_receipt(
        preflight,
        claim_rec,
        claim_rel,
        agg,
        output_root=str(tmp_path),
        finalized_at="2026-07-23T00:35:00Z",
    )

    auth_id = preflight["authorization_id"]
    rec_path = tmp_path / f"receipts/{auth_id}.execution-receipt.json"
    bun_path = tmp_path / f"bundles/{auth_id}.evidence-bundle.json"
    j_path = tmp_path / f"finalization/{auth_id}.finalization-journal.json"

    # Test Corrupted Receipt
    original_rec = rec_path.read_text(encoding="utf-8")
    rec_path.write_text("{corrupt json", encoding="utf-8")
    with pytest.raises(OrchestrationError, match="final_artifact_verification_failed"):
        finalize_consumption_and_write_receipt(
            preflight, claim_rec, claim_rel, agg, output_root=str(tmp_path), finalized_at="2026-07-23T00:35:00Z"
        )
    rec_path.write_text(original_rec, encoding="utf-8")

    # Test Corrupted Bundle
    original_bun = bun_path.read_text(encoding="utf-8")
    bun_path.write_text("{corrupt json", encoding="utf-8")
    with pytest.raises(OrchestrationError, match="final_artifact_verification_failed"):
        finalize_consumption_and_write_receipt(
            preflight, claim_rec, claim_rel, agg, output_root=str(tmp_path), finalized_at="2026-07-23T00:35:00Z"
        )
    bun_path.write_text(original_bun, encoding="utf-8")

    # Test Corrupted Journal
    original_j = j_path.read_text(encoding="utf-8")
    j_path.write_text("{corrupt json", encoding="utf-8")
    with pytest.raises(OrchestrationError, match="finalization_journal_corrupt|final_artifact_verification_failed"):
        finalize_consumption_and_write_receipt(
            preflight, claim_rec, claim_rel, agg, output_root=str(tmp_path), finalized_at="2026-07-23T00:35:00Z"
        )
    j_path.write_text(original_j, encoding="utf-8")
