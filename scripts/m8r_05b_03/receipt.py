"""Commit 3 execution receipt materialization & consumption finalization."""
from __future__ import annotations

import json
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


def build_execution_receipt(
    preflight: dict[str, Any],
    claim_record: dict[str, Any],
    aggregation: dict[str, Any],
    *,
    finalized_at: str,
) -> dict[str, Any]:
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
    *,
    finalized_at: str,
) -> dict[str, Any]:
    bundle_identity = {
        "authorization_id": preflight["authorization_id"],
        "preflight_id": preflight["preflight_id"],
        "claim_id": claim_record["claim_id"],
        "execution_receipt_id": receipt["execution_receipt_id"],
        "overall_status": receipt["overall_status"],
        "finalized_at": finalized_at,
    }
    bundle_hash = sha256_json(bundle_identity)
    bundle_id = "umeb-v1-" + bundle_hash[:20]
    manifest_path = bundle_relative_path(preflight["authorization_id"])

    bundle = {
        "schema_version": "unified_market_evidence_bundle.v1",
        "bundle_id": bundle_id,
        "bundle_hash": bundle_hash,
        "authorization_id": preflight["authorization_id"],
        "preflight_id": preflight["preflight_id"],
        "claim_id": claim_record["claim_id"],
        "execution_receipt_id": receipt["execution_receipt_id"],
        "overall_status": receipt["overall_status"],
        "manifest_relative_path": manifest_path,
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
    receipt = build_execution_receipt(preflight, claim_record, aggregation, finalized_at=finalized_at)
    bundle = build_evidence_bundle(preflight, claim_record, receipt, finalized_at=finalized_at)

    status_map = {
        "succeeded": "consumed_success",
        "partial_success": "consumed_partial",
        "failed": "consumed_failed",
    }
    new_state = status_map[aggregation["overall_status"]]

    final_claim_record = dict(claim_record)
    final_claim_record["state"] = new_state
    final_claim_record["execution_receipt_id"] = receipt["execution_receipt_id"]
    final_claim_record["execution_receipt_hash"] = receipt["execution_receipt_hash"]
    final_claim_record["finalized_at"] = finalized_at

    schema = json.loads(CONSUMPTION_SCHEMA_PATH.read_text(encoding="utf-8"))
    if list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(final_claim_record)):
        raise OrchestrationError("consumption_record_schema_invalid")

    # Write finalized claim record back to disk safely
    try:
        dest = safe_destination(output_root, claim_relative_path, create_parent=False)
        dest.path.write_text(canonical_json(final_claim_record) + "\n", encoding="utf-8")
    except FilesystemSafetyError as exc:
        raise OrchestrationError(exc.code) from exc

    # Materialize receipt
    rec_rel = receipt_relative_path(preflight["authorization_id"])
    try:
        atomic_create_text_exclusive(output_root, rec_rel, canonical_json(receipt) + "\n")
    except FilesystemSafetyError as exc:
        raise OrchestrationError(exc.code) from exc

    # Materialize bundle
    bun_rel = bundle_relative_path(preflight["authorization_id"])
    try:
        atomic_create_text_exclusive(output_root, bun_rel, canonical_json(bundle) + "\n")
    except FilesystemSafetyError as exc:
        raise OrchestrationError(exc.code) from exc

    return final_claim_record, receipt, bundle
