"""Commit 3 execution receipt materialization, evidence bundle generation, and crash-consistent CAS finalization."""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

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


def receipt_relative_path(authorization_id: str) -> str:
    return f"receipts/{authorization_id}.execution-receipt.json"


def bundle_relative_path(authorization_id: str) -> str:
    return f"bundles/{authorization_id}.evidence-bundle.json"


def journal_relative_path(authorization_id: str) -> str:
    return f"finalization/{authorization_id}.finalization-journal.json"


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
    base = dict(claim)
    base["state"] = "claimed"
    base["execution_receipt_id"] = None
    base["execution_receipt_hash"] = None
    base["finalized_at"] = None
    base["last_error_code"] = None
    return sha256_json(base)


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
        "created_by_component": "m8r_05b_03_execution_receipt",
    }
    schema = json.loads(RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))
    if list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(receipt)):
        raise OrchestrationError("execution_receipt_schema_invalid")
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
    schema = json.loads(BUNDLE_SCHEMA_PATH.read_text(encoding="utf-8"))
    if list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(bundle)):
        raise OrchestrationError("evidence_bundle_schema_invalid")
    return bundle


def finalize_consumption_and_write_receipt(
    preflight: dict[str, Any],
    claim_record: dict[str, Any],
    claim_relative_path: str,
    aggregation: dict[str, Any],
    *,
    output_root: str,
    finalized_at: str,
    finalization_owner_id: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    # Step 1: Read durable disk claim and validate schema and preflight binding
    try:
        claim_dest = safe_destination(output_root, claim_relative_path, create_parent=False)
        if not claim_dest.path.is_file():
            raise OrchestrationError("consumption_record_missing")
        disk_claim = json.loads(claim_dest.path.read_text(encoding="utf-8"))
    except (FilesystemSafetyError, json.JSONDecodeError) as exc:
        raise OrchestrationError("consumption_record_read_failed") from exc

    claim_schema = json.loads(CONSUMPTION_SCHEMA_PATH.read_text(encoding="utf-8"))
    if list(Draft202012Validator(claim_schema, format_checker=FormatChecker()).iter_errors(disk_claim)):
        raise OrchestrationError("consumption_record_schema_invalid")

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
    if disk_claim.get("claim_id") != claim_record.get("claim_id"):
        raise OrchestrationError("claim_id_mismatch")

    if initial_claim_hash(claim_record) != initial_claim_hash(disk_claim):
        raise OrchestrationError("claim_content_mismatch")

    # Step 2: Build receipt and bundle using disk_claim as sole authority
    receipt = build_execution_receipt(preflight, disk_claim, aggregation, finalized_at=finalized_at)
    bundle = build_evidence_bundle(preflight, disk_claim, receipt, aggregation, finalized_at=finalized_at)

    current_owner_id = finalization_owner_id or f"umefo-v1-{sha256_json({'u': str(uuid.uuid4()), 't': finalized_at})[:20]}"
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
        "state": "preparing",
        "created_at": finalized_at,
        "updated_at": finalized_at,
    }

    journal_schema = json.loads(JOURNAL_SCHEMA_PATH.read_text(encoding="utf-8"))

    # Step 3: Acquire or recover finalization ownership journal
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

            if list(Draft202012Validator(journal_schema, format_checker=FormatChecker()).iter_errors(journal)):
                raise OrchestrationError("finalization_journal_schema_invalid")

            # Verify journal transaction identity
            if (
                journal.get("authorization_id") != preflight["authorization_id"]
                or journal.get("claim_id") != disk_claim["claim_id"]
                or journal.get("claim_hash") != initial_claim_hash(disk_claim)
                or journal.get("execution_receipt_hash") != receipt["execution_receipt_hash"]
                or journal.get("bundle_hash") != bundle["bundle_hash"]
            ):
                raise OrchestrationError("finalization_ownership_conflict")

            # Enforce single active owner check if journal is in preparing state
            if journal.get("state") == "preparing":
                if finalization_owner_id is not None and journal.get("finalization_owner_id") == finalization_owner_id:
                    current_owner_id = finalization_owner_id
                else:
                    raise OrchestrationError("finalization_in_progress")
            else:
                current_owner_id = journal.get("finalization_owner_id", current_owner_id)
        else:
            raise OrchestrationError("finalization_journal_creation_failed") from exc

    rec_rel = receipt_relative_path(preflight["authorization_id"])
    rec_dest = safe_destination(output_root, rec_rel, create_parent=True)
    bun_rel = bundle_relative_path(preflight["authorization_id"])
    bun_dest = safe_destination(output_root, bun_rel, create_parent=True)

    owner_slug = current_owner_id.replace("umefo-v1-", "")

    # Step 4: Temporary File Staging & Atomic Promotion (if state is preparing)
    if journal["state"] == "preparing":
        tmp_rec_rel = f"receipts/.tmp-{preflight['authorization_id']}-{owner_slug}.json"
        tmp_bun_rel = f"bundles/.tmp-{preflight['authorization_id']}-{owner_slug}.json"
        tmp_rec_dest = safe_destination(output_root, tmp_rec_rel, create_parent=True)
        tmp_bun_dest = safe_destination(output_root, tmp_bun_rel, create_parent=True)

        # Stage receipt
        tmp_rec_dest.path.write_text(canonical_json(receipt) + "\n", encoding="utf-8")
        staged_rec_bytes = tmp_rec_dest.path.read_bytes()
        rec_schema = json.loads(RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))
        try:
            staged_rec_json = json.loads(staged_rec_bytes.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise OrchestrationError("receipt_staging_failed") from exc
        if list(Draft202012Validator(rec_schema, format_checker=FormatChecker()).iter_errors(staged_rec_json)):
            raise OrchestrationError("receipt_staging_schema_invalid")
        if sha256_json(staged_rec_json) != sha256_json(receipt):
            raise OrchestrationError("receipt_staging_hash_mismatch")

        # Stage bundle
        tmp_bun_dest.path.write_text(canonical_json(bundle) + "\n", encoding="utf-8")
        staged_bun_bytes = tmp_bun_dest.path.read_bytes()
        bun_schema = json.loads(BUNDLE_SCHEMA_PATH.read_text(encoding="utf-8"))
        try:
            staged_bun_json = json.loads(staged_bun_bytes.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise OrchestrationError("bundle_staging_failed") from exc
        if list(Draft202012Validator(bun_schema, format_checker=FormatChecker()).iter_errors(staged_bun_json)):
            raise OrchestrationError("bundle_staging_schema_invalid")
        if sha256_json(staged_bun_json) != sha256_json(bundle):
            raise OrchestrationError("bundle_staging_hash_mismatch")

        # Promote receipt & bundle
        tmp_rec_dest.path.replace(rec_dest.path)
        tmp_bun_dest.path.replace(bun_dest.path)

        # Advance journal state to artifacts_committed
        journal["state"] = "artifacts_committed"
        journal["updated_at"] = finalized_at
        tmp_j_rel = f"finalization/.tmp-journal-{preflight['authorization_id']}-{owner_slug}.json"
        tmp_j_dest = safe_destination(output_root, tmp_j_rel, create_parent=True)
        tmp_j_dest.path.write_text(canonical_json(journal) + "\n", encoding="utf-8")
        tmp_j_dest.path.replace(journal_dest.path)

    # Step 5: Terminal Claim State Update (if state is preparing or artifacts_committed)
    if journal["state"] in ("preparing", "artifacts_committed"):
        status_map = {
            "succeeded": "consumed_success",
            "partial_success": "consumed_partial",
            "failed": "consumed_failed",
        }
        new_state = status_map[aggregation["overall_status"]]

        # Re-read claim and perform Terminal CAS Guard
        try:
            current_disk_claim = json.loads(claim_dest.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise OrchestrationError("consumption_record_read_failed") from exc

        if list(Draft202012Validator(claim_schema, format_checker=FormatChecker()).iter_errors(current_disk_claim)):
            raise OrchestrationError("consumption_record_schema_invalid")

        if (
            current_disk_claim.get("state") != "claimed"
            or current_disk_claim.get("claim_id") != disk_claim["claim_id"]
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

        if list(Draft202012Validator(claim_schema, format_checker=FormatChecker()).iter_errors(final_claim_record)):
            raise OrchestrationError("consumption_record_schema_invalid")

        temp_claim_rel = f"claims/.tmp-claim-{preflight['authorization_id']}-{owner_slug}.json"
        temp_claim_dest = safe_destination(output_root, temp_claim_rel, create_parent=True)
        temp_claim_dest.path.write_text(canonical_json(final_claim_record) + "\n", encoding="utf-8")
        temp_claim_dest.path.replace(claim_dest.path)

        journal["state"] = "claim_committed"
        journal["updated_at"] = finalized_at
        tmp_j_rel = f"finalization/.tmp-journal-{preflight['authorization_id']}-{owner_slug}.json"
        tmp_j_dest = safe_destination(output_root, tmp_j_rel, create_parent=True)
        tmp_j_dest.path.write_text(canonical_json(journal) + "\n", encoding="utf-8")
        tmp_j_dest.path.replace(journal_dest.path)

    # Step 6: Complete Durable Cross-Link Verification
    if not claim_dest.path.is_file() or not rec_dest.path.is_file() or not bun_dest.path.is_file() or not journal_dest.path.is_file():
        raise OrchestrationError("final_artifact_verification_failed")

    try:
        final_claim = json.loads(claim_dest.path.read_text(encoding="utf-8"))
        disk_rec = json.loads(rec_dest.path.read_text(encoding="utf-8"))
        disk_bun = json.loads(bun_dest.path.read_text(encoding="utf-8"))
        disk_journal = json.loads(journal_dest.path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise OrchestrationError("final_artifact_verification_failed") from exc

    rec_schema = json.loads(RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))
    bun_schema = json.loads(BUNDLE_SCHEMA_PATH.read_text(encoding="utf-8"))

    if list(Draft202012Validator(claim_schema, format_checker=FormatChecker()).iter_errors(final_claim)):
        raise OrchestrationError("final_artifact_verification_failed")
    if list(Draft202012Validator(journal_schema, format_checker=FormatChecker()).iter_errors(disk_journal)):
        raise OrchestrationError("final_artifact_verification_failed")
    if list(Draft202012Validator(rec_schema, format_checker=FormatChecker()).iter_errors(disk_rec)):
        raise OrchestrationError("final_artifact_verification_failed")
    if list(Draft202012Validator(bun_schema, format_checker=FormatChecker()).iter_errors(disk_bun)):
        raise OrchestrationError("final_artifact_verification_failed")

    # Full cross-link checks
    if disk_rec.get("execution_receipt_hash") != receipt["execution_receipt_hash"] or sha256_json(disk_rec) != sha256_json(receipt):
        raise OrchestrationError("final_artifact_verification_failed")
    if disk_bun.get("bundle_hash") != bundle["bundle_hash"] or sha256_json(disk_bun) != sha256_json(bundle):
        raise OrchestrationError("final_artifact_verification_failed")
    if final_claim.get("execution_receipt_id") != receipt["execution_receipt_id"]:
        raise OrchestrationError("final_artifact_verification_failed")
    if final_claim.get("execution_receipt_hash") != receipt["execution_receipt_hash"]:
        raise OrchestrationError("final_artifact_verification_failed")
    if disk_bun.get("execution_receipt_id") != receipt["execution_receipt_id"]:
        raise OrchestrationError("final_artifact_verification_failed")
    if disk_bun.get("execution_receipt_hash") != receipt["execution_receipt_hash"]:
        raise OrchestrationError("final_artifact_verification_failed")
    if disk_journal.get("execution_receipt_id") != receipt["execution_receipt_id"]:
        raise OrchestrationError("final_artifact_verification_failed")
    if disk_journal.get("execution_receipt_hash") != receipt["execution_receipt_hash"]:
        raise OrchestrationError("final_artifact_verification_failed")
    if disk_journal.get("bundle_id") != bundle["bundle_id"]:
        raise OrchestrationError("final_artifact_verification_failed")
    if disk_journal.get("bundle_hash") != bundle["bundle_hash"]:
        raise OrchestrationError("final_artifact_verification_failed")
    if disk_claim.get("authorization_id") != preflight["authorization_id"]:
        raise OrchestrationError("final_artifact_verification_failed")
    if disk_journal.get("state") != "claim_committed":
        raise OrchestrationError("final_artifact_verification_failed")

    status_map = {
        "succeeded": "consumed_success",
        "partial_success": "consumed_partial",
        "failed": "consumed_failed",
    }
    if final_claim.get("state") != status_map[disk_rec["overall_status"]]:
        raise OrchestrationError("final_artifact_verification_failed")

    return final_claim, disk_rec, disk_bun
