"""Tests for finalization receipt, recovery contract, failure injection, and true concurrency."""
from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

from scripts.m8r_05b_03.canonical import sha256_json
from scripts.m8r_05b_03.controlled_dispatch import claim_and_dispatch_approved
from scripts.m8r_05b_03.dispatch import RuntimeAdapterRegistry
from scripts.m8r_05b_03.errors import OrchestrationError
from scripts.m8r_05b_03.evidence_aggregation import aggregate_dispatch_outcomes
from scripts.m8r_05b_03.receipt import (
    ALL_PHASES,
    FinalizationPhaseHook,
    PHASE_AFTER_ARTIFACTS_COMMITTED,
    PHASE_AFTER_BUNDLE_PROMOTED,
    PHASE_AFTER_BUNDLE_STAGED,
    PHASE_AFTER_CLAIM_COMMITTED,
    PHASE_AFTER_JOURNAL_ACQUIRED,
    PHASE_AFTER_RECEIPT_PROMOTED,
    PHASE_AFTER_RECEIPT_STAGED,
    build_evidence_bundle,
    build_execution_receipt,
    finalize_consumption_and_write_receipt,
    generate_owner_id,
    initial_claim_hash,
    journal_relative_path,
    recover_controlled_finalization,
    validate_finalization_timestamps,
    validate_owner_id,
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


FINALIZED_AT = "2026-07-23T00:35:00Z"


# ===========================================================================
# Basic tests
# ===========================================================================
class TestBasicFinalization:
    def test_validate_finalization_timestamps_rejects_inversion(self):
        with pytest.raises(OrchestrationError, match="temporal_inversion_detected"):
            validate_finalization_timestamps("2026-07-23T00:30:00Z", "2026-07-23T00:29:59Z")

    def test_build_receipt_and_bundle_with_warnings(self, tmp_path):
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

        rec = build_execution_receipt(preflight, claim_rec, agg, finalized_at=FINALIZED_AT)
        assert rec["warnings"] == ["warning_1", "warning_2"]

        bun = build_evidence_bundle(preflight, claim_rec, rec, agg, finalized_at=FINALIZED_AT)
        assert bun["warnings"] == ["warning_1", "warning_2"]
        assert "schema_version" in bun["artifact_inventory"][0]

    def test_normal_finalization_and_idempotent_repeat(self, tmp_path):
        _, preflight, claim_rec, claim_rel, agg = setup_dispatch_environment(tmp_path)

        fin_claim, rec, bun = finalize_consumption_and_write_receipt(
            preflight, claim_rec, claim_rel, agg,
            output_root=str(tmp_path), finalized_at=FINALIZED_AT,
        )

        assert fin_claim["state"] == "consumed_success"
        j_path = tmp_path / f"finalization/{preflight['authorization_id']}.finalization-journal.json"
        assert j_path.is_file()
        j_data = json.loads(j_path.read_text(encoding="utf-8"))
        assert j_data["state"] == "claim_committed"
        assert "finalization_owner_id" in j_data

        # Idempotent repeat
        fin_claim2, rec2, bun2 = finalize_consumption_and_write_receipt(
            preflight, claim_rec, claim_rel, agg,
            output_root=str(tmp_path), finalized_at=FINALIZED_AT,
        )
        assert fin_claim2["state"] == "consumed_success"
        assert rec2["execution_receipt_hash"] == rec["execution_receipt_hash"]
        assert bun2["bundle_hash"] == bun["bundle_hash"]


# ===========================================================================
# Owner token validation
# ===========================================================================
class TestOwnerTokenValidation:
    def test_valid_owner_id_accepted(self):
        validate_owner_id("umefo-v1-0123456789abcdef0123")

    @pytest.mark.parametrize("bad_id", [
        "umefo-v1-ZZZZZZZZZZZZZZZZZZZZ",
        "umefo-v1-short",
        "umefo-v1-toolongtoolongtoolongt",
        "bad-prefix-01234567890123456789",
        12345,
    ])
    def test_invalid_owner_id_rejected_before_mutation(self, bad_id, tmp_path):
        _, preflight, claim_rec, claim_rel, agg = setup_dispatch_environment(tmp_path)

        with pytest.raises(OrchestrationError, match="finalization_owner_id_invalid"):
            finalize_consumption_and_write_receipt(
                preflight, claim_rec, claim_rel, agg,
                output_root=str(tmp_path), finalized_at=FINALIZED_AT,
                finalization_owner_id=bad_id,
            )

        # Prove no journal was created
        j_path = tmp_path / f"finalization/{preflight['authorization_id']}.finalization-journal.json"
        assert not j_path.exists(), "Journal must not exist after invalid owner rejection"


# ===========================================================================
# Real failure injection tests using phase hooks
# ===========================================================================
class TestRealFailureInjection:
    """Inject a synthetic exception at each named phase, then recover using
    the formal recovery API and verify durable state."""

    @pytest.mark.parametrize("crash_phase", ALL_PHASES)
    def test_crash_at_phase_then_recover(self, crash_phase, tmp_path):
        _, preflight, claim_rec, claim_rel, agg = setup_dispatch_environment(tmp_path)

        # Create a hook that raises at the specified phase
        class CrashError(Exception):
            pass

        def crash_hook(phase: str) -> None:
            if phase == crash_phase:
                raise CrashError(f"Simulated crash at {phase}")

        hook = FinalizationPhaseHook(crash_hook)

        # First attempt: crashes at the specified phase
        with pytest.raises(CrashError, match=f"Simulated crash at {crash_phase}"):
            finalize_consumption_and_write_receipt(
                preflight, claim_rec, claim_rel, agg,
                output_root=str(tmp_path), finalized_at=FINALIZED_AT,
                phase_hook=hook,
            )

        auth_id = preflight["authorization_id"]
        j_path = tmp_path / f"finalization/{auth_id}.finalization-journal.json"
        rec_path = tmp_path / f"receipts/{auth_id}.execution-receipt.json"
        bun_path = tmp_path / f"bundles/{auth_id}.evidence-bundle.json"

        # Verify durable state at crash point
        if crash_phase == PHASE_AFTER_JOURNAL_ACQUIRED:
            assert j_path.is_file(), "Journal must exist after acquisition"
            j = json.loads(j_path.read_text(encoding="utf-8"))
            assert j["state"] == "preparing"
            assert not rec_path.is_file()
            assert not bun_path.is_file()

        elif crash_phase in (PHASE_AFTER_RECEIPT_STAGED, PHASE_AFTER_BUNDLE_STAGED):
            j = json.loads(j_path.read_text(encoding="utf-8"))
            assert j["state"] == "preparing"

        elif crash_phase == PHASE_AFTER_RECEIPT_PROMOTED:
            j = json.loads(j_path.read_text(encoding="utf-8"))
            assert j["state"] == "preparing"
            assert rec_path.is_file(), "Receipt must be promoted"

        elif crash_phase == PHASE_AFTER_BUNDLE_PROMOTED:
            j = json.loads(j_path.read_text(encoding="utf-8"))
            assert j["state"] == "preparing"
            assert rec_path.is_file()
            assert bun_path.is_file()

        elif crash_phase == PHASE_AFTER_ARTIFACTS_COMMITTED:
            j = json.loads(j_path.read_text(encoding="utf-8"))
            assert j["state"] == "artifacts_committed"
            assert rec_path.is_file()
            assert bun_path.is_file()

        elif crash_phase == PHASE_AFTER_CLAIM_COMMITTED:
            j = json.loads(j_path.read_text(encoding="utf-8"))
            # Claim was committed but journal wasn't updated to claim_committed yet
            assert j["state"] == "artifacts_committed"
            # Claim is already terminal
            claim_path = tmp_path / f"claims/{auth_id}.consumption-record.json"
            claim_data = json.loads(claim_path.read_text(encoding="utf-8"))
            assert claim_data["state"] == "consumed_success"

        # Recovery: use the formal recovery API (no-op hook this time)
        fin_claim, rec, bun = recover_controlled_finalization(
            preflight, claim_rec, claim_rel, agg,
            output_root=str(tmp_path), finalized_at=FINALIZED_AT,
        )

        # Verify complete recovery
        assert fin_claim["state"] == "consumed_success"
        assert rec_path.is_file()
        assert bun_path.is_file()

        j_final = json.loads(j_path.read_text(encoding="utf-8"))
        assert j_final["state"] == "claim_committed"


# ===========================================================================
# Recovery contract tests
# ===========================================================================
class TestRecoveryContract:
    def test_recovery_when_no_journal_exists(self, tmp_path):
        _, preflight, claim_rec, claim_rel, agg = setup_dispatch_environment(tmp_path)

        with pytest.raises(OrchestrationError, match="recovery_journal_not_found"):
            recover_controlled_finalization(
                preflight, claim_rec, claim_rel, agg,
                output_root=str(tmp_path), finalized_at=FINALIZED_AT,
            )

    def test_recovery_when_journal_already_complete(self, tmp_path):
        _, preflight, claim_rec, claim_rel, agg = setup_dispatch_environment(tmp_path)

        # First: complete normally
        finalize_consumption_and_write_receipt(
            preflight, claim_rec, claim_rel, agg,
            output_root=str(tmp_path), finalized_at=FINALIZED_AT,
        )

        with pytest.raises(OrchestrationError, match="recovery_journal_already_complete"):
            recover_controlled_finalization(
                preflight, claim_rec, claim_rel, agg,
                output_root=str(tmp_path), finalized_at=FINALIZED_AT,
            )

    def test_recovery_does_not_redispatch_adapters(self, tmp_path):
        """Prove that recovery only completes finalization, does not invoke adapters."""
        _, preflight, claim_rec, claim_rel, agg = setup_dispatch_environment(tmp_path)

        # Crash after journal
        class CrashError(Exception):
            pass

        hook = FinalizationPhaseHook(lambda p: (_ for _ in ()).throw(CrashError()) if p == PHASE_AFTER_JOURNAL_ACQUIRED else None)

        with pytest.raises(CrashError):
            finalize_consumption_and_write_receipt(
                preflight, claim_rec, claim_rel, agg,
                output_root=str(tmp_path), finalized_at=FINALIZED_AT,
                phase_hook=hook,
            )

        # Record evidence files before recovery
        evidence_files_before = set()
        evidence_dir = tmp_path / "evidence"
        if evidence_dir.is_dir():
            evidence_files_before = {f.name for f in evidence_dir.iterdir()}

        # Record claim files before recovery
        claims_dir = tmp_path / "claims"
        claim_files_before = set()
        if claims_dir.is_dir():
            claim_files_before = {f.name for f in claims_dir.iterdir() if not f.name.startswith(".tmp-")}

        # Recover
        fin_claim, rec, bun = recover_controlled_finalization(
            preflight, claim_rec, claim_rel, agg,
            output_root=str(tmp_path), finalized_at=FINALIZED_AT,
        )

        # Evidence files unchanged (no adapter redispatch)
        evidence_files_after = {f.name for f in evidence_dir.iterdir()} if evidence_dir.is_dir() else set()
        assert evidence_files_after == evidence_files_before, "Recovery must not create new evidence files"

        # Only one claim file (the original, now terminal)
        final_claim_files = {f.name for f in claims_dir.iterdir() if not f.name.startswith(".tmp-")}
        assert len(final_claim_files) == len(claim_files_before), "Recovery must not create a second claim"

        assert fin_claim["state"] == "consumed_success"

    def test_recovery_does_not_create_second_claim(self, tmp_path):
        _, preflight, claim_rec, claim_rel, agg = setup_dispatch_environment(tmp_path)

        class CrashError(Exception):
            pass

        hook = FinalizationPhaseHook(lambda p: (_ for _ in ()).throw(CrashError()) if p == PHASE_AFTER_ARTIFACTS_COMMITTED else None)

        with pytest.raises(CrashError):
            finalize_consumption_and_write_receipt(
                preflight, claim_rec, claim_rel, agg,
                output_root=str(tmp_path), finalized_at=FINALIZED_AT,
                phase_hook=hook,
            )

        # Count claim files
        claims_dir = tmp_path / "claims"
        claim_count_before = len([f for f in claims_dir.iterdir() if not f.name.startswith(".tmp-")])

        # Recover
        recover_controlled_finalization(
            preflight, claim_rec, claim_rel, agg,
            output_root=str(tmp_path), finalized_at=FINALIZED_AT,
        )

        claim_count_after = len([f for f in claims_dir.iterdir() if not f.name.startswith(".tmp-")])
        assert claim_count_after == claim_count_before

    def test_recovery_does_not_change_operation_results(self, tmp_path):
        _, preflight, claim_rec, claim_rel, agg = setup_dispatch_environment(tmp_path)

        class CrashError(Exception):
            pass

        hook = FinalizationPhaseHook(lambda p: (_ for _ in ()).throw(CrashError()) if p == PHASE_AFTER_BUNDLE_PROMOTED else None)

        with pytest.raises(CrashError):
            finalize_consumption_and_write_receipt(
                preflight, claim_rec, claim_rel, agg,
                output_root=str(tmp_path), finalized_at=FINALIZED_AT,
                phase_hook=hook,
            )

        # Recovery
        fin_claim, rec, bun = recover_controlled_finalization(
            preflight, claim_rec, claim_rel, agg,
            output_root=str(tmp_path), finalized_at=FINALIZED_AT,
        )

        # Operation results match original aggregation
        assert rec["overall_status"] == agg["overall_status"]
        assert rec["total_operations"] == agg["total_operations"]
        assert rec["succeeded_operations"] == agg["succeeded_operations"]


# ===========================================================================
# True concurrent finalization test using threads
# ===========================================================================
class TestTrueConcurrentFinalization:
    def test_two_threads_single_mutation_owner(self, tmp_path):
        """Two threads simultaneously attempt finalization on the same authorization.

        Supported contract:
        - Exactly one transaction owner performs journal acquisition, staging,
          promotion, and claim mutation.
        - A second caller either receives finalization_in_progress, or if the
          first transaction already completed, returns verified idempotent success.

        Instrumentation proves every mutation phase executes exactly once via
        phase hook counters.
        """
        _, preflight, claim_rec, claim_rel, agg = setup_dispatch_environment(tmp_path)

        barrier = threading.Barrier(2, timeout=5)
        results = [None, None]

        # Shared mutation counters (thread-safe via lock)
        mutation_counts = {phase: 0 for phase in ALL_PHASES}
        counter_lock = threading.Lock()

        def counting_hook(phase: str) -> None:
            with counter_lock:
                mutation_counts[phase] += 1

        hook = FinalizationPhaseHook(counting_hook)

        def finalize_thread(idx: int, owner_id: str):
            try:
                barrier.wait()  # Both threads start simultaneously
                result = finalize_consumption_and_write_receipt(
                    preflight, claim_rec, claim_rel, agg,
                    output_root=str(tmp_path), finalized_at=FINALIZED_AT,
                    finalization_owner_id=owner_id,
                    phase_hook=hook,
                )
                results[idx] = ("success", result)
            except OrchestrationError as exc:
                results[idx] = ("error", exc.code)
            except Exception as exc:
                results[idx] = ("unexpected", str(exc))

        owner_a = "umefo-v1-aaaaaaaaaaaaaaaaaaa0"
        owner_b = "umefo-v1-bbbbbbbbbbbbbbbbbbb0"

        t1 = threading.Thread(target=finalize_thread, args=(0, owner_a))
        t2 = threading.Thread(target=finalize_thread, args=(1, owner_b))
        t1.start()
        t2.start()
        t1.join(timeout=10)
        t2.join(timeout=10)

        assert results[0] is not None, "Thread 0 must have a result"
        assert results[1] is not None, "Thread 1 must have a result"

        # Both callers must resolve (not hang or crash unexpectedly)
        statuses = [r[0] for r in results]
        for i, (status, detail) in enumerate(results):
            assert status in ("success", "error"), f"Thread {i} unexpected: {status}={detail}"
            if status == "error":
                assert detail in ("finalization_in_progress", "finalization_ownership_conflict"), \
                    f"Thread {i} unexpected error code: {detail}"

        # At least one caller succeeded
        success_count = statuses.count("success")
        assert success_count >= 1, f"At least one must succeed: {results}"

        # --- Mutation-once proof ---
        # Every mutation phase that was reached must have executed exactly once.
        # The winner thread executes all 7 phases. The loser thread executes 0 phases
        # (blocked at journal acquisition) or arrives after completion (idempotent verify,
        # which does not enter the preparing-state mutation path and thus fires 0 hooks).
        for phase in ALL_PHASES:
            assert mutation_counts[phase] == 1, \
                f"Phase {phase} executed {mutation_counts[phase]} times, expected exactly 1"

        # --- Final artifact integrity ---
        auth_id = preflight["authorization_id"]
        j_path = tmp_path / f"finalization/{auth_id}.finalization-journal.json"
        rec_path = tmp_path / f"receipts/{auth_id}.execution-receipt.json"
        bun_path = tmp_path / f"bundles/{auth_id}.evidence-bundle.json"
        claim_path = tmp_path / f"claims/{auth_id}.consumption-record.json"

        assert j_path.is_file(), "Journal must exist"
        assert rec_path.is_file(), "Receipt must exist"
        assert bun_path.is_file(), "Bundle must exist"
        assert claim_path.is_file(), "Claim must exist"

        j_data = json.loads(j_path.read_text(encoding="utf-8"))
        rec_data = json.loads(rec_path.read_text(encoding="utf-8"))
        bun_data = json.loads(bun_path.read_text(encoding="utf-8"))
        claim_data = json.loads(claim_path.read_text(encoding="utf-8"))

        assert j_data["state"] == "claim_committed"
        assert claim_data["state"] == "consumed_success"
        assert claim_data["execution_receipt_id"] == rec_data["execution_receipt_id"]
        assert claim_data["execution_receipt_hash"] == rec_data["execution_receipt_hash"]
        assert bun_data["execution_receipt_id"] == rec_data["execution_receipt_id"]
        assert bun_data["execution_receipt_hash"] == rec_data["execution_receipt_hash"]
        assert j_data["execution_receipt_id"] == rec_data["execution_receipt_id"]
        assert j_data["bundle_id"] == bun_data["bundle_id"]
        assert j_data["bundle_hash"] == bun_data["bundle_hash"]

        # --- No temp file races ---
        for subdir in ("finalization", "receipts", "bundles", "claims"):
            d = tmp_path / subdir
            if d.is_dir():
                tmp_files = [f for f in d.iterdir() if f.name.startswith(".tmp-")]
                assert len(tmp_files) == 0, f"Temp files in {subdir} must be cleaned: {tmp_files}"


# ===========================================================================
# Comprehensive corruption and cross-link mismatch tests
# ===========================================================================
class TestCorruptionAndMismatch:
    def _setup_completed(self, tmp_path):
        _, preflight, claim_rec, claim_rel, agg = setup_dispatch_environment(tmp_path)
        finalize_consumption_and_write_receipt(
            preflight, claim_rec, claim_rel, agg,
            output_root=str(tmp_path), finalized_at=FINALIZED_AT,
        )
        auth_id = preflight["authorization_id"]
        return preflight, claim_rec, claim_rel, agg, auth_id

    def test_corrupted_receipt(self, tmp_path):
        pf, cr, cl, agg, aid = self._setup_completed(tmp_path)
        (tmp_path / f"receipts/{aid}.execution-receipt.json").write_text("{corrupt", encoding="utf-8")
        with pytest.raises(OrchestrationError, match="final_artifact_verification_failed"):
            finalize_consumption_and_write_receipt(pf, cr, cl, agg, output_root=str(tmp_path), finalized_at=FINALIZED_AT)

    def test_corrupted_bundle(self, tmp_path):
        pf, cr, cl, agg, aid = self._setup_completed(tmp_path)
        (tmp_path / f"bundles/{aid}.evidence-bundle.json").write_text("{corrupt", encoding="utf-8")
        with pytest.raises(OrchestrationError, match="final_artifact_verification_failed"):
            finalize_consumption_and_write_receipt(pf, cr, cl, agg, output_root=str(tmp_path), finalized_at=FINALIZED_AT)

    def test_corrupted_journal(self, tmp_path):
        pf, cr, cl, agg, aid = self._setup_completed(tmp_path)
        (tmp_path / f"finalization/{aid}.finalization-journal.json").write_text("{corrupt", encoding="utf-8")
        with pytest.raises(OrchestrationError, match="finalization_journal_corrupt|final_artifact_verification_failed"):
            finalize_consumption_and_write_receipt(pf, cr, cl, agg, output_root=str(tmp_path), finalized_at=FINALIZED_AT)

    def test_missing_receipt(self, tmp_path):
        pf, cr, cl, agg, aid = self._setup_completed(tmp_path)
        (tmp_path / f"receipts/{aid}.execution-receipt.json").unlink()
        with pytest.raises(OrchestrationError, match="final_artifact_verification_failed"):
            finalize_consumption_and_write_receipt(pf, cr, cl, agg, output_root=str(tmp_path), finalized_at=FINALIZED_AT)

    def test_missing_bundle(self, tmp_path):
        pf, cr, cl, agg, aid = self._setup_completed(tmp_path)
        (tmp_path / f"bundles/{aid}.evidence-bundle.json").unlink()
        with pytest.raises(OrchestrationError, match="final_artifact_verification_failed"):
            finalize_consumption_and_write_receipt(pf, cr, cl, agg, output_root=str(tmp_path), finalized_at=FINALIZED_AT)

    def test_corrupted_claim(self, tmp_path):
        pf, cr, cl, agg, aid = self._setup_completed(tmp_path)
        claim_path = tmp_path / f"claims/{aid}.consumption-record.json"
        claim_path.write_text("{corrupt", encoding="utf-8")
        with pytest.raises(OrchestrationError, match="consumption_record_read_failed|final_artifact_verification_failed"):
            finalize_consumption_and_write_receipt(pf, cr, cl, agg, output_root=str(tmp_path), finalized_at=FINALIZED_AT)

    def test_terminal_claim_receipt_hash_mismatch(self, tmp_path):
        pf, cr, cl, agg, aid = self._setup_completed(tmp_path)
        claim_path = tmp_path / f"claims/{aid}.consumption-record.json"
        claim_data = json.loads(claim_path.read_text(encoding="utf-8"))
        claim_data["execution_receipt_hash"] = "f" * 64
        claim_path.write_text(json.dumps(claim_data), encoding="utf-8")
        with pytest.raises(OrchestrationError, match="final_artifact_verification_failed"):
            finalize_consumption_and_write_receipt(pf, cr, cl, agg, output_root=str(tmp_path), finalized_at=FINALIZED_AT)

    def test_bundle_receipt_id_mismatch(self, tmp_path):
        pf, cr, cl, agg, aid = self._setup_completed(tmp_path)
        bun_path = tmp_path / f"bundles/{aid}.evidence-bundle.json"
        bun_data = json.loads(bun_path.read_text(encoding="utf-8"))
        bun_data["execution_receipt_id"] = "umerec-v1-00000000000000000000"
        bun_path.write_text(json.dumps(bun_data), encoding="utf-8")
        with pytest.raises(OrchestrationError, match="final_artifact_verification_failed"):
            finalize_consumption_and_write_receipt(pf, cr, cl, agg, output_root=str(tmp_path), finalized_at=FINALIZED_AT)

    def test_journal_receipt_mismatch(self, tmp_path):
        pf, cr, cl, agg, aid = self._setup_completed(tmp_path)
        j_path = tmp_path / f"finalization/{aid}.finalization-journal.json"
        j_data = json.loads(j_path.read_text(encoding="utf-8"))
        j_data["execution_receipt_hash"] = "e" * 64
        j_path.write_text(json.dumps(j_data), encoding="utf-8")
        with pytest.raises(OrchestrationError, match="final_artifact_verification_failed|finalization_journal_schema_invalid|finalization_ownership_conflict"):
            finalize_consumption_and_write_receipt(pf, cr, cl, agg, output_root=str(tmp_path), finalized_at=FINALIZED_AT)

    def test_journal_bundle_hash_mismatch(self, tmp_path):
        pf, cr, cl, agg, aid = self._setup_completed(tmp_path)
        j_path = tmp_path / f"finalization/{aid}.finalization-journal.json"
        j_data = json.loads(j_path.read_text(encoding="utf-8"))
        j_data["bundle_hash"] = "d" * 64
        j_path.write_text(json.dumps(j_data), encoding="utf-8")
        with pytest.raises(OrchestrationError, match="final_artifact_verification_failed|finalization_journal_schema_invalid|finalization_ownership_conflict"):
            finalize_consumption_and_write_receipt(pf, cr, cl, agg, output_root=str(tmp_path), finalized_at=FINALIZED_AT)
