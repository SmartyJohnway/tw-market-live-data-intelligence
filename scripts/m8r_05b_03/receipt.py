"""Commit 3 execution receipt materialization, evidence bundle generation, and crash-consistent CAS finalization.

Recovery contract:
    - Owner token is durably stored in the finalization journal on disk.
    - If a process crashes while journal.state == 'preparing', the owner token
      is recoverable from the journal file.
    - recover_controlled_finalization() reads the journal, extracts the owner,
      and completes the transaction without redispatching adapters or creating
      a second claim.
    - Phase hooks (FinalizationPhaseHook) are injectable for test-only failure
      injection; production default is no-op.
"""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from jsonschema import Draft202012Validator, FormatChecker

from scripts.m8r_filesystem_safety import (
    FilesystemSafetyError,
    atomic_create_text_exclusive,
    safe_destination,
)

from .canonical import canonical_json, sha256_json
from .errors import OrchestrationError


ROOT = Path(__file__).resolve().parents[2]
RECEIPT_SCHEMA_PATH = ROOT / "schemas" / "unified_market_evidence_execution_receipt.v1.schema.json"
BUNDLE_SCHEMA_PATH = ROOT / "schemas" / "unified_market_evidence_bundle.v1.schema.json"
CONSUMPTION_SCHEMA_PATH = ROOT / "schemas" / "unified_market_evidence_consumption_record.v1.schema.json"
JOURNAL_SCHEMA_PATH = ROOT / "schemas" / "unified_market_evidence_finalization_journal.v1.schema.json"

OWNER_ID_PATTERN = re.compile(r"^umefo-v1-[0-9a-f]{20}$")


# ---------------------------------------------------------------------------
# Phase hook protocol for test-only failure injection
# ---------------------------------------------------------------------------
class FinalizationPhaseHook:
    """Injectable hook called at named phases during finalization.

    Production default is no-op.  Tests inject a callable that raises at
    a specific phase to simulate a crash.
    """

    def __init__(self, hook: Callable[[str], None] | None = None):
        self._hook = hook

    def __call__(self, phase: str) -> None:
        if self._hook is not None:
            self._hook(phase)


# Named phases (constants so tests can reference them):
PHASE_AFTER_JOURNAL_ACQUIRED = "after_journal_acquired"
PHASE_AFTER_RECEIPT_STAGED = "after_receipt_staged"
PHASE_AFTER_BUNDLE_STAGED = "after_bundle_staged"
PHASE_AFTER_RECEIPT_PROMOTED = "after_receipt_promoted"
PHASE_AFTER_BUNDLE_PROMOTED = "after_bundle_promoted"
PHASE_AFTER_ARTIFACTS_COMMITTED = "after_artifacts_committed"
PHASE_AFTER_CLAIM_COMMITTED = "after_claim_committed_before_journal"

ALL_PHASES = [
    PHASE_AFTER_JOURNAL_ACQUIRED,
    PHASE_AFTER_RECEIPT_STAGED,
    PHASE_AFTER_BUNDLE_STAGED,
    PHASE_AFTER_RECEIPT_PROMOTED,
    PHASE_AFTER_BUNDLE_PROMOTED,
    PHASE_AFTER_ARTIFACTS_COMMITTED,
    PHASE_AFTER_CLAIM_COMMITTED,
]

_NOOP_HOOK = FinalizationPhaseHook()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def receipt_relative_path(authorization_id: str) -> str:
    return f"receipts/{authorization_id}.execution-receipt.json"


def bundle_relative_path(authorization_id: str) -> str:
    return f"bundles/{authorization_id}.evidence-bundle.json"


def journal_relative_path(authorization_id: str) -> str:
    return f"finalization/{authorization_id}.finalization-journal.json"


def generate_owner_id(finalized_at: str) -> str:
    return f"umefo-v1-{sha256_json({'u': str(uuid.uuid4()), 't': finalized_at})[:20]}"


def validate_owner_id(owner_id: str) -> None:
    """Validate owner token format before any durable mutation."""
    if not isinstance(owner_id, str) or not OWNER_ID_PATTERN.match(owner_id):
        raise OrchestrationError("finalization_owner_id_invalid")


def validate_finalization_timestamps(claim_created_at: str, finalized_at: str) -> None:
    try:
        dt_claim = datetime.fromisoformat(claim_created_at.replace("Z", "+00:00"))
        dt_final = datetime.fromisoformat(finalized_at.replace("Z", "+00:00"))
    except (ValueError, AttributeError) as exc:
        raise OrchestrationError("finalization_timestamp_invalid") from exc
    if dt_claim.tzinfo is None or dt_final.tzinfo is None:
        raise OrchestrationError("finalization_timestamp_invalid")
    if dt_final < dt_claim:
        raise OrchestrationError("temporal_inversion_detected")


def initial_claim_hash(claim: dict[str, Any]) -> str:
    """Canonical claimed-state identity hash, invariant across state transitions."""
    base = dict(claim)
    base["state"] = "claimed"
    base["execution_receipt_id"] = None
    base["execution_receipt_hash"] = None
    base["finalized_at"] = None
    base["last_error_code"] = None
    return sha256_json(base)


def _load_schema(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_schema(instance: dict, schema: dict, error_code: str) -> None:
    if list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(instance)):
        raise OrchestrationError(error_code)


STATUS_TO_CLAIM_STATE = {
    "succeeded": "consumed_success",
    "partial_success": "consumed_partial",
    "failed": "consumed_failed",
}


# ---------------------------------------------------------------------------
# Build receipt and bundle
# ---------------------------------------------------------------------------
def build_execution_receipt(
    preflight: dict[str, Any],
    disk_claim: dict[str, Any],
    aggregation: dict[str, Any],
    *,
    finalized_at: str,
) -> dict[str, Any]:
    validate_finalization_timestamps(disk_claim["claim_created_at"], finalized_at)

    receipt_identity = {
        "preflight_id": preflight["preflight_id"],
        "preflight_identity_hash": preflight["preflight_identity_hash"],
        "preflight_artifact_hash": preflight["preflight_artifact_hash"],
        "claim_id": disk_claim["claim_id"],
        "claim_hash": initial_claim_hash(disk_claim),
        "overall_status": aggregation["overall_status"],
        "total_operations": aggregation["total_operations"],
        "succeeded_operations": aggregation["succeeded_operations"],
        "failed_operations": aggregation["failed_operations"],
        "operation_receipts": aggregation["operation_receipts"],
        "warnings": aggregation.get("warnings", []),
        "finalized_at": finalized_at,
    }
    receipt_hash = sha256_json(receipt_identity)
    receipt_id = "umerec-v1-" + receipt_hash[:20]

    receipt = {
        "schema_version": "unified_market_evidence_execution_receipt.v1",
        "execution_receipt_id": receipt_id,
        "execution_receipt_hash": receipt_hash,
        **receipt_identity,
        "created_by_component": "m8r_05b_03_execution_receipt",
    }
    _validate_schema(receipt, _load_schema(RECEIPT_SCHEMA_PATH), "execution_receipt_schema_invalid")
    return receipt


def build_evidence_bundle(
    preflight: dict[str, Any],
    disk_claim: dict[str, Any],
    receipt: dict[str, Any],
    aggregation: dict[str, Any],
    *,
    finalized_at: str,
) -> dict[str, Any]:
    validate_finalization_timestamps(disk_claim["claim_created_at"], finalized_at)

    bundle_identity = {
        "authorization_id": preflight["authorization_id"],
        "authorization_hash": preflight["authorization_hash"],
        "preflight_id": preflight["preflight_id"],
        "preflight_identity_hash": preflight["preflight_identity_hash"],
        "preflight_artifact_hash": preflight["preflight_artifact_hash"],
        "claim_id": disk_claim["claim_id"],
        "claim_hash": initial_claim_hash(disk_claim),
        "execution_receipt_id": receipt["execution_receipt_id"],
        "execution_receipt_hash": receipt["execution_receipt_hash"],
        "overall_status": receipt["overall_status"],
        "operation_order": preflight["approved_operation_order"],
        "operation_evidence_entries": aggregation["operation_evidence_entries"],
        "artifact_inventory": aggregation["artifact_inventory"],
        "total_item_count": aggregation["total_item_count"],
        "warnings": aggregation.get("warnings", []),
        "finalized_at": finalized_at,
    }
    bundle_hash = sha256_json(bundle_identity)
    bundle_id = "umeb-v1-" + bundle_hash[:20]

    bundle = {
        "schema_version": "unified_market_evidence_bundle.v1",
        "bundle_id": bundle_id,
        "bundle_hash": bundle_hash,
        **bundle_identity,
    }
    _validate_schema(bundle, _load_schema(BUNDLE_SCHEMA_PATH), "evidence_bundle_schema_invalid")
    return bundle


# ---------------------------------------------------------------------------
# Read and validate durable disk claim
# ---------------------------------------------------------------------------
def _read_and_validate_disk_claim(
    output_root: str,
    claim_relative_path: str,
    preflight: dict[str, Any],
    caller_claim: dict[str, Any],
) -> tuple[Any, dict, dict]:
    """Returns (claim_dest, disk_claim, claim_schema)."""
    claim_schema = _load_schema(CONSUMPTION_SCHEMA_PATH)
    try:
        claim_dest = safe_destination(output_root, claim_relative_path, create_parent=False)
        if not claim_dest.path.is_file():
            raise OrchestrationError("consumption_record_missing")
        disk_claim = json.loads(claim_dest.path.read_text(encoding="utf-8"))
    except (FilesystemSafetyError, json.JSONDecodeError) as exc:
        raise OrchestrationError("consumption_record_read_failed") from exc

    _validate_schema(disk_claim, claim_schema, "consumption_record_schema_invalid")

    if disk_claim.get("authorization_id") != preflight["authorization_id"]:
        raise OrchestrationError("consumption_authorization_mismatch")
    if disk_claim.get("authorization_hash") != preflight["authorization_hash"]:
        raise OrchestrationError("consumption_authorization_hash_mismatch")
    if disk_claim.get("preflight_id") != preflight["preflight_id"]:
        raise OrchestrationError("preflight_id_mismatch")
    if disk_claim.get("preflight_identity_hash") != preflight["preflight_identity_hash"]:
        raise OrchestrationError("preflight_identity_hash_mismatch")
    if disk_claim.get("preflight_artifact_hash") != preflight["preflight_artifact_hash"]:
        raise OrchestrationError("preflight_artifact_hash_mismatch")
    if disk_claim.get("claim_id") != caller_claim.get("claim_id"):
        raise OrchestrationError("claim_id_mismatch")
    if initial_claim_hash(caller_claim) != initial_claim_hash(disk_claim):
        raise OrchestrationError("claim_content_mismatch")

    return claim_dest, disk_claim, claim_schema


# ---------------------------------------------------------------------------
# Core finalization transaction
# ---------------------------------------------------------------------------
def _execute_finalization_transaction(
    preflight: dict[str, Any],
    disk_claim: dict[str, Any],
    claim_dest: Any,
    claim_schema: dict,
    receipt: dict[str, Any],
    bundle: dict[str, Any],
    aggregation: dict[str, Any],
    *,
    output_root: str,
    finalized_at: str,
    current_owner_id: str,
    phase_hook: FinalizationPhaseHook,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Execute the finalization transaction from journal acquisition through verification."""
    journal_schema = _load_schema(JOURNAL_SCHEMA_PATH)
    journal_rel = journal_relative_path(preflight["authorization_id"])
    journal_dest = safe_destination(output_root, journal_rel, create_parent=True)

    journal_identity = {
        "authorization_id": preflight["authorization_id"],
        "authorization_hash": preflight["authorization_hash"],
        "claim_id": disk_claim["claim_id"],
        "claim_hash": initial_claim_hash(disk_claim),
        "preflight_id": preflight["preflight_id"],
        "preflight_identity_hash": preflight["preflight_identity_hash"],
        "preflight_artifact_hash": preflight["preflight_artifact_hash"],
        "execution_receipt_id": receipt["execution_receipt_id"],
        "execution_receipt_hash": receipt["execution_receipt_hash"],
        "bundle_id": bundle["bundle_id"],
        "bundle_hash": bundle["bundle_hash"],
    }
    journal_hash = sha256_json(journal_identity)
    journal_id = f"umefj-v1-{journal_hash[:20]}"

    journal = {
        "schema_version": "unified_market_evidence_finalization_journal.v1",
        "journal_id": journal_id,
        "finalization_owner_id": current_owner_id,
        **journal_identity,
        "state": "preparing",
        "created_at": finalized_at,
        "updated_at": finalized_at,
    }

    # --- Step 3: Acquire or recover finalization ownership journal ---
    try:
        atomic_create_text_exclusive(output_root, journal_rel, canonical_json(journal) + "\n")
    except FilesystemSafetyError as exc:
        if exc.code == "already_consumed_or_replayed":
            if not journal_dest.path.is_file():
                raise OrchestrationError("finalization_journal_read_failed") from exc
            try:
                journal = json.loads(journal_dest.path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as err:
                raise OrchestrationError("finalization_journal_corrupt") from err

            _validate_schema(journal, journal_schema, "finalization_journal_schema_invalid")

            # Verify journal transaction identity
            if (
                journal.get("authorization_id") != preflight["authorization_id"]
                or journal.get("claim_id") != disk_claim["claim_id"]
                or journal.get("claim_hash") != initial_claim_hash(disk_claim)
                or journal.get("execution_receipt_hash") != receipt["execution_receipt_hash"]
                or journal.get("bundle_hash") != bundle["bundle_hash"]
            ):
                raise OrchestrationError("finalization_ownership_conflict")

            # Enforce single active owner check
            if journal.get("state") == "preparing":
                if journal.get("finalization_owner_id") == current_owner_id:
                    pass  # same owner recovery
                else:
                    raise OrchestrationError("finalization_in_progress")
            else:
                current_owner_id = journal.get("finalization_owner_id", current_owner_id)
        else:
            raise OrchestrationError("finalization_journal_creation_failed") from exc

    phase_hook(PHASE_AFTER_JOURNAL_ACQUIRED)

    rec_rel = receipt_relative_path(preflight["authorization_id"])
    rec_dest = safe_destination(output_root, rec_rel, create_parent=True)
    bun_rel = bundle_relative_path(preflight["authorization_id"])
    bun_dest = safe_destination(output_root, bun_rel, create_parent=True)

    owner_slug = current_owner_id.replace("umefo-v1-", "")

    # --- Step 4: Temporary file staging & atomic promotion ---
    if journal["state"] == "preparing":
        tmp_rec_rel = f"receipts/.tmp-{preflight['authorization_id']}-{owner_slug}.json"
        tmp_bun_rel = f"bundles/.tmp-{preflight['authorization_id']}-{owner_slug}.json"
        tmp_rec_dest = safe_destination(output_root, tmp_rec_rel, create_parent=True)
        tmp_bun_dest = safe_destination(output_root, tmp_bun_rel, create_parent=True)

        # Stage receipt
        tmp_rec_dest.path.write_text(canonical_json(receipt) + "\n", encoding="utf-8")
        staged_rec_json = json.loads(tmp_rec_dest.path.read_bytes().decode("utf-8"))
        _validate_schema(staged_rec_json, _load_schema(RECEIPT_SCHEMA_PATH), "receipt_staging_schema_invalid")
        if sha256_json(staged_rec_json) != sha256_json(receipt):
            raise OrchestrationError("receipt_staging_hash_mismatch")

        phase_hook(PHASE_AFTER_RECEIPT_STAGED)

        # Stage bundle
        tmp_bun_dest.path.write_text(canonical_json(bundle) + "\n", encoding="utf-8")
        staged_bun_json = json.loads(tmp_bun_dest.path.read_bytes().decode("utf-8"))
        _validate_schema(staged_bun_json, _load_schema(BUNDLE_SCHEMA_PATH), "bundle_staging_schema_invalid")
        if sha256_json(staged_bun_json) != sha256_json(bundle):
            raise OrchestrationError("bundle_staging_hash_mismatch")

        phase_hook(PHASE_AFTER_BUNDLE_STAGED)

        # Promote receipt
        tmp_rec_dest.path.replace(rec_dest.path)
        phase_hook(PHASE_AFTER_RECEIPT_PROMOTED)

        # Promote bundle
        tmp_bun_dest.path.replace(bun_dest.path)
        phase_hook(PHASE_AFTER_BUNDLE_PROMOTED)

        # Advance journal to artifacts_committed
        journal["state"] = "artifacts_committed"
        journal["updated_at"] = finalized_at
        _atomic_replace_json(output_root, journal_rel, journal, owner_slug, preflight["authorization_id"], "finalization")

        phase_hook(PHASE_AFTER_ARTIFACTS_COMMITTED)

    # --- Step 5: Terminal claim state update ---
    if journal["state"] in ("preparing", "artifacts_committed"):
        new_state = STATUS_TO_CLAIM_STATE[aggregation["overall_status"]]

        # Terminal CAS guard: re-read current claim
        try:
            current_disk_claim = json.loads(claim_dest.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise OrchestrationError("consumption_record_read_failed") from exc

        _validate_schema(current_disk_claim, claim_schema, "consumption_record_schema_invalid")

        if current_disk_claim.get("state") == "claimed":
            # Normal path: claim still in claimed state
            if (
                current_disk_claim.get("claim_id") != disk_claim["claim_id"]
                or current_disk_claim.get("authorization_id") != preflight["authorization_id"]
                or initial_claim_hash(current_disk_claim) != journal["claim_hash"]
            ):
                raise OrchestrationError("finalization_cas_mismatch")

            if journal.get("finalization_owner_id") != current_owner_id or journal.get("state") != "artifacts_committed":
                raise OrchestrationError("finalization_cas_mismatch")

            final_claim_record = dict(current_disk_claim)
            final_claim_record["state"] = new_state
            final_claim_record["execution_receipt_id"] = receipt["execution_receipt_id"]
            final_claim_record["execution_receipt_hash"] = receipt["execution_receipt_hash"]
            final_claim_record["finalized_at"] = finalized_at
            _validate_schema(final_claim_record, claim_schema, "consumption_record_schema_invalid")

            temp_claim_rel = f"claims/.tmp-claim-{preflight['authorization_id']}-{owner_slug}.json"
            temp_claim_dest = safe_destination(output_root, temp_claim_rel, create_parent=True)
            temp_claim_dest.path.write_text(canonical_json(final_claim_record) + "\n", encoding="utf-8")
            temp_claim_dest.path.replace(claim_dest.path)

            phase_hook(PHASE_AFTER_CLAIM_COMMITTED)
        elif current_disk_claim.get("state") == new_state:
            # Recovery path: claim already terminal from a prior crash after claim commit
            # Verify cross-links match before proceeding to journal update
            if (
                current_disk_claim.get("execution_receipt_id") != receipt["execution_receipt_id"]
                or current_disk_claim.get("execution_receipt_hash") != receipt["execution_receipt_hash"]
            ):
                raise OrchestrationError("finalization_cas_mismatch")
        else:
            raise OrchestrationError("finalization_cas_mismatch")

        # Advance journal to claim_committed
        journal["state"] = "claim_committed"
        journal["updated_at"] = finalized_at
        _atomic_replace_json(output_root, journal_rel, journal, owner_slug, preflight["authorization_id"], "finalization")

    # --- Step 6: Complete durable cross-link verification ---
    return _verify_durable_cross_links(
        output_root, preflight, receipt, bundle, claim_dest, rec_dest, bun_dest, journal_dest,
        claim_schema, journal_schema,
    )


def _atomic_replace_json(output_root: str, rel_path: str, obj: dict, owner_slug: str, auth_id: str, subdir: str) -> None:
    """Write JSON to a temp file then atomically replace the target."""
    dest = safe_destination(output_root, rel_path, create_parent=True)
    tmp_rel = f"{subdir}/.tmp-{Path(rel_path).stem}-{auth_id}-{owner_slug}.json"
    tmp_dest = safe_destination(output_root, tmp_rel, create_parent=True)
    tmp_dest.path.write_text(canonical_json(obj) + "\n", encoding="utf-8")
    tmp_dest.path.replace(dest.path)


def _verify_durable_cross_links(
    output_root: str,
    preflight: dict,
    receipt: dict,
    bundle: dict,
    claim_dest: Any,
    rec_dest: Any,
    bun_dest: Any,
    journal_dest: Any,
    claim_schema: dict,
    journal_schema: dict,
) -> tuple[dict, dict, dict]:
    """Read all four artifacts from disk and verify schemas and cross-links."""
    for dest in (claim_dest, rec_dest, bun_dest, journal_dest):
        if not dest.path.is_file():
            raise OrchestrationError("final_artifact_verification_failed")

    try:
        final_claim = json.loads(claim_dest.path.read_text(encoding="utf-8"))
        disk_rec = json.loads(rec_dest.path.read_text(encoding="utf-8"))
        disk_bun = json.loads(bun_dest.path.read_text(encoding="utf-8"))
        disk_journal = json.loads(journal_dest.path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise OrchestrationError("final_artifact_verification_failed") from exc

    rec_schema = _load_schema(RECEIPT_SCHEMA_PATH)
    bun_schema = _load_schema(BUNDLE_SCHEMA_PATH)

    for obj, schema in [
        (final_claim, claim_schema),
        (disk_journal, journal_schema),
        (disk_rec, rec_schema),
        (disk_bun, bun_schema),
    ]:
        _validate_schema(obj, schema, "final_artifact_verification_failed")

    # Full cross-link checks
    checks = [
        (disk_rec.get("execution_receipt_hash"), receipt["execution_receipt_hash"]),
        (sha256_json(disk_rec), sha256_json(receipt)),
        (disk_bun.get("bundle_hash"), bundle["bundle_hash"]),
        (sha256_json(disk_bun), sha256_json(bundle)),
        (final_claim.get("execution_receipt_id"), receipt["execution_receipt_id"]),
        (final_claim.get("execution_receipt_hash"), receipt["execution_receipt_hash"]),
        (disk_bun.get("execution_receipt_id"), receipt["execution_receipt_id"]),
        (disk_bun.get("execution_receipt_hash"), receipt["execution_receipt_hash"]),
        (disk_journal.get("execution_receipt_id"), receipt["execution_receipt_id"]),
        (disk_journal.get("execution_receipt_hash"), receipt["execution_receipt_hash"]),
        (disk_journal.get("bundle_id"), bundle["bundle_id"]),
        (disk_journal.get("bundle_hash"), bundle["bundle_hash"]),
        (disk_journal.get("state"), "claim_committed"),
        (final_claim.get("state"), STATUS_TO_CLAIM_STATE[disk_rec["overall_status"]]),
    ]
    for actual, expected in checks:
        if actual != expected:
            raise OrchestrationError("final_artifact_verification_failed")

    return final_claim, disk_rec, disk_bun


# ---------------------------------------------------------------------------
# Public API: finalize_consumption_and_write_receipt
# ---------------------------------------------------------------------------
def finalize_consumption_and_write_receipt(
    preflight: dict[str, Any],
    claim_record: dict[str, Any],
    claim_relative_path: str,
    aggregation: dict[str, Any],
    *,
    output_root: str,
    finalized_at: str,
    finalization_owner_id: str | None = None,
    phase_hook: FinalizationPhaseHook | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Finalize a claimed authorization: build receipt/bundle, stage, promote, commit claim."""
    claim_dest, disk_claim, claim_schema = _read_and_validate_disk_claim(
        output_root, claim_relative_path, preflight, claim_record,
    )

    receipt = build_execution_receipt(preflight, disk_claim, aggregation, finalized_at=finalized_at)
    bundle = build_evidence_bundle(preflight, disk_claim, receipt, aggregation, finalized_at=finalized_at)

    current_owner_id = finalization_owner_id or generate_owner_id(finalized_at)
    validate_owner_id(current_owner_id)

    return _execute_finalization_transaction(
        preflight, disk_claim, claim_dest, claim_schema, receipt, bundle, aggregation,
        output_root=output_root,
        finalized_at=finalized_at,
        current_owner_id=current_owner_id,
        phase_hook=phase_hook or _NOOP_HOOK,
    )


# ---------------------------------------------------------------------------
# Public API: recover_controlled_finalization
# ---------------------------------------------------------------------------
def recover_controlled_finalization(
    preflight: dict[str, Any],
    claim_record: dict[str, Any],
    claim_relative_path: str,
    aggregation: dict[str, Any],
    *,
    output_root: str,
    finalized_at: str,
    phase_hook: FinalizationPhaseHook | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Recover a stuck finalization transaction.

    Recovery contract:
    - Reads the existing journal from disk to extract the durable owner token.
    - Does NOT redispatch any adapters.
    - Does NOT create a second authorization claim.
    - Continues finalization using the existing journal transaction identity.
    - Only completes staging/promotion/claim-commit from durable state.

    Raises OrchestrationError with stable codes:
    - 'recovery_journal_not_found': no journal exists (nothing to recover).
    - 'recovery_journal_already_complete': journal is already claim_committed.
    - 'finalization_journal_corrupt': journal is unreadable.
    - 'finalization_journal_schema_invalid': journal doesn't match schema.
    """
    journal_schema = _load_schema(JOURNAL_SCHEMA_PATH)
    journal_rel = journal_relative_path(preflight["authorization_id"])
    journal_dest = safe_destination(output_root, journal_rel, create_parent=False)

    if not journal_dest.path.is_file():
        raise OrchestrationError("recovery_journal_not_found")

    try:
        journal = json.loads(journal_dest.path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise OrchestrationError("finalization_journal_corrupt") from exc

    _validate_schema(journal, journal_schema, "finalization_journal_schema_invalid")

    if journal["state"] == "claim_committed":
        raise OrchestrationError("recovery_journal_already_complete")

    # Extract the durable owner token from the journal
    recovered_owner_id = journal["finalization_owner_id"]

    # Re-run finalization with the recovered owner
    return finalize_consumption_and_write_receipt(
        preflight,
        claim_record,
        claim_relative_path,
        aggregation,
        output_root=output_root,
        finalized_at=finalized_at,
        finalization_owner_id=recovered_owner_id,
        phase_hook=phase_hook,
    )
