"""Commit 3 execution receipt materialization, evidence bundle generation, and crash-consistent CAS finalization."""
from __future__ import annotations

import json
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


def receipt_relative_path(authorization_id: str) -> str:
    return f"receipts/{authorization_id}.execution-receipt.json"


def bundle_relative_path(authorization_id: str) -> str:
    return f"bundles/{authorization_id}.evidence-bundle.json"


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


def build_execution_receipt(
    preflight: dict[str, Any],
    claim_record: dict[str, Any],
    aggregation: dict[str, Any],
    *,
    finalized_at: str,
) -> dict[str, Any]:
    validate_finalization_timestamps(claim_record["claim_created_at"], finalized_at)

    receipt_identity = {
        "preflight_id": preflight["preflight_id"],
        "preflight_identity_hash": preflight["preflight_identity_hash"],
        "preflight_artifact_hash": preflight["preflight_artifact_hash"],
        "claim_id": claim_record["claim_id"],
        "claim_hash": sha256_json(claim_record),
        "overall_status": aggregation["overall_status"],
        "total_operations": aggregation["total_operations"],
        "succeeded_operations": aggregation["succeeded_operations"],
        "failed_operations": aggregation["failed_operations"],
        "operation_receipts": aggregation["operation_receipts"],
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
        "claim_id": claim_record["claim_id"],
        "claim_hash": sha256_json(claim_record),
        "overall_status": aggregation["overall_status"],
        "total_operations": aggregation["total_operations"],
        "succeeded_operations": aggregation["succeeded_operations"],
        "failed_operations": aggregation["failed_operations"],
        "operation_receipts": aggregation["operation_receipts"],
        "finalized_at": finalized_at,
        "created_by_component": "m8r_05b_03_execution_receipt",
    }
    schema = json.loads(RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))
    if list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(receipt)):
        raise OrchestrationError("execution_receipt_schema_invalid")
    return receipt


def build_evidence_bundle(
    preflight: dict[str, Any],
    claim_record: dict[str, Any],
    receipt: dict[str, Any],
    aggregation: dict[str, Any],
    *,
    finalized_at: str,
) -> dict[str, Any]:
    validate_finalization_timestamps(claim_record["claim_created_at"], finalized_at)

    bundle_identity = {
        "authorization_id": preflight["authorization_id"],
        "authorization_hash": preflight["authorization_hash"],
        "preflight_id": preflight["preflight_id"],
        "preflight_identity_hash": preflight["preflight_identity_hash"],
        "preflight_artifact_hash": preflight["preflight_artifact_hash"],
        "claim_id": claim_record["claim_id"],
        "claim_hash": sha256_json(claim_record),
        "execution_receipt_id": receipt["execution_receipt_id"],
        "execution_receipt_hash": receipt["execution_receipt_hash"],
        "overall_status": receipt["overall_status"],
        "operation_order": preflight["approved_operation_order"],
        "operation_evidence_entries": aggregation["operation_evidence_entries"],
        "artifact_inventory": aggregation["artifact_inventory"],
        "total_item_count": aggregation["total_item_count"],
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
        "claim_id": claim_record["claim_id"],
        "claim_hash": sha256_json(claim_record),
        "execution_receipt_id": receipt["execution_receipt_id"],
        "execution_receipt_hash": receipt["execution_receipt_hash"],
        "overall_status": receipt["overall_status"],
        "operation_order": preflight["approved_operation_order"],
        "operation_evidence_entries": aggregation["operation_evidence_entries"],
        "artifact_inventory": aggregation["artifact_inventory"],
        "total_item_count": aggregation["total_item_count"],
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
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    # CAS Check: Read durable claim from disk
    try:
        claim_dest = safe_destination(output_root, claim_relative_path, create_parent=False)
        if not claim_dest.path.is_file():
            raise OrchestrationError("consumption_record_missing")
        disk_claim = json.loads(claim_dest.path.read_text(encoding="utf-8"))
    except (FilesystemSafetyError, json.JSONDecodeError) as exc:
        raise OrchestrationError("consumption_record_read_failed") from exc

    if disk_claim.get("authorization_id") != preflight["authorization_id"]:
        raise OrchestrationError("consumption_authorization_mismatch")
    if disk_claim.get("claim_id") != claim_record["claim_id"]:
        raise OrchestrationError("claim_id_mismatch")

    receipt = build_execution_receipt(preflight, claim_record, aggregation, finalized_at=finalized_at)
    bundle = build_evidence_bundle(preflight, claim_record, receipt, aggregation, finalized_at=finalized_at)

    current_state = disk_claim.get("state")
    if current_state in {"consumed_success", "consumed_partial", "consumed_failed"}:
        if (
            disk_claim.get("execution_receipt_id") == receipt["execution_receipt_id"]
            and disk_claim.get("execution_receipt_hash") == receipt["execution_receipt_hash"]
        ):
            # Idempotent success
            return disk_claim, receipt, bundle
        raise OrchestrationError("authorization_already_finalized")

    if current_state != "claimed":
        raise OrchestrationError("claim_state_invalid")

    status_map = {
        "succeeded": "consumed_success",
        "partial_success": "consumed_partial",
        "failed": "consumed_failed",
    }
    new_state = status_map[aggregation["overall_status"]]

    final_claim_record = dict(disk_claim)
    final_claim_record["state"] = new_state
    final_claim_record["execution_receipt_id"] = receipt["execution_receipt_id"]
    final_claim_record["execution_receipt_hash"] = receipt["execution_receipt_hash"]
    final_claim_record["finalized_at"] = finalized_at

    schema = json.loads(CONSUMPTION_SCHEMA_PATH.read_text(encoding="utf-8"))
    if list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(final_claim_record)):
        raise OrchestrationError("consumption_record_schema_invalid")

    # Transactional Materialization: Write receipt & bundle atomically first
    rec_rel = receipt_relative_path(preflight["authorization_id"])
    bun_rel = bundle_relative_path(preflight["authorization_id"])

    try:
        rec_dest = atomic_create_text_exclusive(output_root, rec_rel, canonical_json(receipt) + "\n")
        bun_dest = atomic_create_text_exclusive(output_root, bun_rel, canonical_json(bundle) + "\n")
    except FilesystemSafetyError as exc:
        if exc.code == "already_consumed_or_replayed":
            raise OrchestrationError("authorization_already_finalized") from exc
        raise OrchestrationError(exc.code) from exc

    # Final Atomic Commit: Update durable claim record state atomically via temp file replace
    try:
        temp_claim_rel = f"claims/.tmp-{preflight['authorization_id']}.json"
        temp_dest = safe_destination(output_root, temp_claim_rel, create_parent=True)
        temp_dest.path.write_text(canonical_json(final_claim_record) + "\n", encoding="utf-8")
        temp_dest.path.replace(claim_dest.path)
    except (FilesystemSafetyError, OSError) as exc:
        raise OrchestrationError("finalization_commit_failed") from exc

    return final_claim_record, receipt, bundle
