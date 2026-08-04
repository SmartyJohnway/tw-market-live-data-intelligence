"""Atomic single-use authorization claim for Commit 2 & 3."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from scripts.m8r_filesystem_safety import (
    FilesystemSafetyError,
    atomic_create_text_exclusive,
    safe_destination,
)

from .canonical import canonical_json, sha256_json
from .errors import OrchestrationError


ROOT = Path(__file__).resolve().parents[2]
CONSUMPTION_SCHEMA_PATH = ROOT / "schemas" / "unified_market_evidence_consumption_record.v1.schema.json"
CLAIMED_OR_CONSUMED_STATES = frozenset(
    {"claimed", "consumed_success", "consumed_partial", "consumed_failed", "consumed"}
)


def claim_relative_path(authorization_id: str) -> str:
    return f"claims/{authorization_id}.consumption-record.json"


def _validate_timestamp(value: str) -> None:
    if not isinstance(value, str):
        raise OrchestrationError("claim_timestamp_invalid")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise OrchestrationError("claim_timestamp_invalid") from exc
    if parsed.tzinfo is None:
        raise OrchestrationError("claim_timestamp_invalid")


def validate_operator_confirmation_reference(ref: str) -> str:
    if not isinstance(ref, str):
        raise OrchestrationError("operator_confirmation_reference_invalid")
    trimmed = ref.strip()
    if not trimmed or len(trimmed) > 128:
        raise OrchestrationError("operator_confirmation_reference_invalid")
    if any(ord(c) < 32 or ord(c) == 127 for c in ref):
        raise OrchestrationError("operator_confirmation_reference_invalid")
    return trimmed


def _validate_supplied_unused_state(state: dict, preflight: dict) -> None:
    if state is None:
        raise OrchestrationError("consumption_record_missing")
    if isinstance(state, list):
        raise OrchestrationError("consumption_state_ambiguous")
    if not isinstance(state, dict):
        raise OrchestrationError("consumption_state_schema_invalid")
    if state.get("state") in CLAIMED_OR_CONSUMED_STATES:
        raise OrchestrationError("authorization_already_claimed")
    expected_fields = {
        "authorization_id",
        "authorization_hash",
        "consumption_binding_id",
        "consumption_binding_hash",
        "registry_contract_version",
        "state",
    }
    if set(state) != expected_fields or state.get("state") != "unused":
        raise OrchestrationError("consumption_state_schema_invalid")
    if (
        state["authorization_id"] != preflight["authorization_id"]
        or state["authorization_hash"] != preflight["authorization_hash"]
    ):
        raise OrchestrationError("consumption_authorization_mismatch")
    if (
        state["consumption_binding_id"] != preflight["consumption_binding_id"]
        or state["consumption_binding_hash"] != preflight["consumption_binding_hash"]
    ):
        raise OrchestrationError("consumption_binding_state_mismatch")
    if state["registry_contract_version"] != "m8r_05b_03.v1":
        raise OrchestrationError("registry_contract_mismatch")


def build_claim_record(
    preflight: dict,
    supplied_consumption_state: dict,
    *,
    claim_created_at: str,
    operator_confirmation_reference: str,
    network_execution_confirmed: bool = False,
    confirmation_bound_at: str | None = None,
) -> dict:
    _validate_supplied_unused_state(supplied_consumption_state, preflight)
    _validate_timestamp(claim_created_at)
    if type(network_execution_confirmed) is not bool:
        raise OrchestrationError("network_execution_confirmation_invalid")
    valid_ref = validate_operator_confirmation_reference(operator_confirmation_reference)
    bound_at = confirmation_bound_at or claim_created_at
    _validate_timestamp(bound_at)

    claim_identity = {
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
        "execution_mode": "execute-approved",
        "execution_confirmed": True,
        "operator_confirmation_reference": valid_ref,
        "network_execution_confirmed": network_execution_confirmed,
        "confirmation_bound_at": bound_at,
        "claim_created_at": claim_created_at,
    }
    record = {
        "schema_version": "unified_market_evidence_consumption_record.v1",
        **{key: claim_identity[key] for key in (
            "authorization_id",
            "authorization_hash",
            "consumption_binding_id",
            "consumption_binding_hash",
            "plan_id",
            "plan_hash",
            "scope_hash",
            "preflight_id",
            "preflight_identity_hash",
            "preflight_artifact_hash",
            "execution_mode",
            "execution_confirmed",
            "operator_confirmation_reference",
            "network_execution_confirmed",
            "confirmation_bound_at",
        )},
        "state": "claimed",
        "claim_id": "umecl-v1-" + sha256_json(claim_identity)[:20],
        "claim_created_at": claim_created_at,
        "claimed_by_component": "m8r_05b_03_atomic_claim",
        "attempt_count": 1,
        "execution_receipt_id": None,
        "execution_receipt_hash": None,
        "finalized_at": None,
        "last_error_code": None,
    }
    schema = json.loads(CONSUMPTION_SCHEMA_PATH.read_text(encoding="utf-8"))
    if list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(record)):
        raise OrchestrationError("consumption_record_schema_invalid")
    return record


def validate_claim_destination(output_root: str, authorization_id: str) -> str:
    relative_path = claim_relative_path(authorization_id)
    try:
        safe_destination(output_root, relative_path, create_parent=False)
    except FilesystemSafetyError as exc:
        raise OrchestrationError(exc.code) from exc
    return relative_path


def atomic_claim_authorization(
    preflight: dict,
    supplied_consumption_state: dict,
    *,
    output_root: str,
    claim_created_at: str,
    operator_confirmation_reference: str,
    network_execution_confirmed: bool = False,
    confirmation_bound_at: str | None = None,
) -> tuple[dict, str]:
    relative_path = validate_claim_destination(output_root, preflight["authorization_id"])
    record = build_claim_record(
        preflight,
        supplied_consumption_state,
        claim_created_at=claim_created_at,
        operator_confirmation_reference=operator_confirmation_reference,
        network_execution_confirmed=network_execution_confirmed,
        confirmation_bound_at=confirmation_bound_at,
    )
    try:
        atomic_create_text_exclusive(
            output_root,
            relative_path,
            canonical_json(record) + "\n",
        )
    except FilesystemSafetyError as exc:
        if exc.code == "already_consumed_or_replayed":
            raise OrchestrationError("authorization_already_claimed") from exc
        raise OrchestrationError(exc.code) from exc
    return record, relative_path
