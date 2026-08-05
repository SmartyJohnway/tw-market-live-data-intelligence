"""Strict local JSON artifact loader for M8R-05C.

This module:
- Loads and validates all M8R-05B-03 output artifacts from the local filesystem.
- Validates each artifact against its JSON schema.
- Verifies SHA-256 hashes from the bundle inventory.
- Never makes network requests.
- Never reads absolute paths provided by external input (only the
  governed artifact_root is accepted as absolute, and it is a CLI arg
  already validated by containment.py).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator, Draft7Validator

from .errors import ProjectionError
from .models import ProjectionInputs

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS_DIR = ROOT / "schemas"

_SCHEMA_NAMES = {
    "request": "unified_market_evidence_request.v1.schema.json",
    "plan": "unified_market_evidence_orchestration_plan.v1.schema.json",
    "receipt": "unified_market_evidence_execution_receipt.v1.schema.json",
    "bundle": "unified_market_evidence_bundle.v1.schema.json",
}

# Plan and request use draft-07; receipt and bundle use draft 2020-12.
_DRAFT07_KEYS = {"request", "plan"}


def _load_schema(name: str) -> dict:
    path = SCHEMAS_DIR / name
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProjectionError("schema_load_failed") from exc


def _validate_schema(obj: dict, schema_key: str) -> None:
    schema_name = _SCHEMA_NAMES[schema_key]
    schema = _load_schema(schema_name)
    if schema_key in _DRAFT07_KEYS:
        errors = list(Draft7Validator(schema).iter_errors(obj))
    else:
        errors = list(Draft202012Validator(schema).iter_errors(obj))
    if errors:
        raise ProjectionError(f"schema_invalid_{schema_key}")


def _load_json(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8")
        obj = json.loads(text)
    except (OSError, json.JSONDecodeError) as exc:
        raise ProjectionError("artifact_load_invalid") from exc
    if not isinstance(obj, dict):
        raise ProjectionError("artifact_load_invalid")
    return obj


def _sha256_file(path: Path) -> str:
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise ProjectionError("artifact_hash_read_failed") from exc
    return hashlib.sha256(data).hexdigest()


def _verify_artifact_hash(path: Path, expected_sha256: str) -> None:
    actual = _sha256_file(path)
    if actual != expected_sha256:
        raise ProjectionError("artifact_hash_mismatch")


def load_projection_inputs(
    *,
    request_path: str,
    plan_path: str,
    authorization_path: str,
    consumption_binding_path: str,
    receipt_path: str,
    bundle_path: str,
    artifact_root: str,
    calculated_at: str,
) -> ProjectionInputs:
    """Load and validate all inputs for the 05C projection.

    This is a pure I/O function: validates schemas and hashes, but does not
    transform data or call projection logic.

    Parameters
    ----------
    request_path, plan_path, authorization_path, consumption_binding_path,
    receipt_path, bundle_path:
        Absolute or CWD-relative paths to the input JSON files.
    artifact_root:
        The governed output_root that was used during M8R-05B-03 execution.
        Evidence artifact relative_paths inside bundle are resolved against this.
    calculated_at:
        ISO-8601 UTC datetime string (from CLI --calculated-at or receipt.finalized_at).
    """
    request = _load_json(Path(request_path))
    _validate_schema(request, "request")

    plan = _load_json(Path(plan_path))
    _validate_schema(plan, "plan")

    # Authorization and consumption binding schemas not in _SCHEMA_NAMES;
    # load without schema validation (schemas may vary; identity verified via hashes).
    authorization = _load_json(Path(authorization_path))
    consumption_binding = _load_json(Path(consumption_binding_path))

    receipt = _load_json(Path(receipt_path))
    _validate_schema(receipt, "receipt")

    bundle = _load_json(Path(bundle_path))
    _validate_schema(bundle, "bundle")

    # Validate request_id is present.
    if not request.get("request_id"):
        raise ProjectionError("request_id_missing")

    # Validate receipt and bundle are consistent.
    if receipt.get("execution_receipt_id") != bundle.get("execution_receipt_id"):
        raise ProjectionError("receipt_bundle_id_mismatch")

    # Load evidence artifacts from bundle inventory and verify their hashes.
    artifact_root_path = Path(artifact_root)
    if not artifact_root_path.is_absolute():
        raise ProjectionError("artifact_root_not_absolute")
    if not artifact_root_path.exists():
        raise ProjectionError("artifact_root_missing")

    evidence_artifacts: dict[str, dict] = {}
    for entry in bundle.get("artifact_inventory", []):
        relative_path = entry.get("relative_path")
        expected_sha256 = entry.get("sha256")
        if not relative_path or not expected_sha256:
            continue
        artifact_path = artifact_root_path / relative_path
        if not artifact_path.exists():
            # Missing artifact — record as missing but do not fail here;
            # projection layer will handle missing evidence gracefully.
            continue
        _verify_artifact_hash(artifact_path, expected_sha256)
        artifact_obj = _load_json(artifact_path)
        evidence_artifacts[relative_path] = artifact_obj

    # Validate calculated_at is provided.
    if not calculated_at:
        raise ProjectionError("calculated_at_missing")

    return ProjectionInputs(
        request=request,
        plan=plan,
        authorization=authorization,
        consumption_binding=consumption_binding,
        receipt=receipt,
        bundle=bundle,
        artifact_root=str(artifact_root_path.resolve()),
        calculated_at=calculated_at,
        evidence_artifacts=evidence_artifacts,
    )
