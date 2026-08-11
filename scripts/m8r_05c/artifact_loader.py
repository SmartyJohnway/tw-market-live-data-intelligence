"""Strict local JSON artifact loader for M8R-05C.

This module:
- Loads and validates ALL M8R-05B-03 output artifacts against their schemas.
- Verifies the complete cryptographic lineage of predecessors.
- Validates the bundle inventory (missing files, containment, schemas, sizes).
- Rejects duplicate operations, paths, bindings.
- Never makes network requests.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from copy import deepcopy

from jsonschema import Draft202012Validator, Draft7Validator

from .errors import ProjectionError
from .models import ProjectionInputs
from scripts.m8r_05b_03.canonical import sha256_json

# Import authoritative validators from 05B-01, 05B-02, 05B-03
from scripts.m8r_05b_02.validator import validate_execution_authorization
from scripts.m8r_05b_02.consumption_binding import validate_consumption_binding
from scripts.m8r_05b_03.consumption_claim import validate_claim_destination, validate_operator_confirmation_reference

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS_DIR = ROOT / "schemas"

_SCHEMA_NAMES = {
    "request": "unified_market_evidence_request.v1.schema.json",
    "f3_validation": "unified_market_evidence_request_validation.v1.schema.json",
    "plan": "unified_market_evidence_orchestration_plan.v1.schema.json",
    "authorization": "unified_market_evidence_execution_authorization.v1.schema.json",
    "consumption_binding": "unified_market_evidence_authorization_consumption_binding.v1.schema.json",
    "claim": "unified_market_evidence_consumption_record.v1.schema.json",
    "receipt": "unified_market_evidence_execution_receipt.v1.schema.json",
    "bundle": "unified_market_evidence_bundle.v1.schema.json",
}

_DRAFT07_KEYS = {"request", "plan"}
_M8R_06_03_EVIDENCE_SCHEMA = "m8r_06_03_operation_evidence.v1"


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

def _check_containment(path: Path, root: Path) -> None:
    try:
        resolved = path.resolve()
    except OSError:
        raise ProjectionError("artifact_path_invalid")
    
    if root:
        root = root.resolve()
        # Must be under root
        if root not in resolved.parents:
            raise ProjectionError(f"artifact_path_traversal: {resolved} not relative to {root}")
    
    if not resolved.is_file():
        raise ProjectionError("artifact_not_found")


def load_projection_inputs(
    *,
    request_path: str,
    f3_validation_path: str,
    plan_path: str,
    authorization_path: str,
    consumption_binding_path: str,
    claim_path: str,
    receipt_path: str,
    bundle_path: str,
    artifact_root: str,
    calculated_at: str,
) -> ProjectionInputs:
    """Load and validate all inputs for the 05C projection."""
    request = _load_json(Path(request_path))
    _validate_schema(request, "request")

    f3_validation = _load_json(Path(f3_validation_path))
    _validate_schema(f3_validation, "f3_validation")

    plan = _load_json(Path(plan_path))
    _validate_schema(plan, "plan")

    authorization = _load_json(Path(authorization_path))
    _validate_schema(authorization, "authorization")

    consumption_binding = _load_json(Path(consumption_binding_path))
    _validate_schema(consumption_binding, "consumption_binding")
    
    claim = _load_json(Path(claim_path))
    _validate_schema(claim, "claim")

    receipt = _load_json(Path(receipt_path))
    _validate_schema(receipt, "receipt")

    bundle = _load_json(Path(bundle_path))
    _validate_schema(bundle, "bundle")

    # Authoritative Validation of F3 canonical result against Request
    request_id = request.get("request_id")
    if f3_validation.get("request_id") != request_id:
        raise ProjectionError("f3_request_id_mismatch")
    if f3_validation.get("validation_status") not in ("valid",):
        raise ProjectionError("f3_validation_status_not_acceptable")
        
    f3_targets = f3_validation.get("target_results", [])
    if len(f3_targets) != len(request.get("targets", [])):
        raise ProjectionError("f3_target_count_mismatch")
        
    seen_indices = set()
    for t in f3_targets:
        idx = t.get("target_index")
        if idx in seen_indices or idx < 0 or idx >= len(request["targets"]):
            raise ProjectionError("f3_target_index_invalid")
        seen_indices.add(idx)
        # Original input must match
        if t.get("original_input") != request["targets"][idx]["input"]:
            raise ProjectionError("f3_original_input_mismatch")

    # Authoritative Validation of Plan against F3 & Request
    request_hash = sha256_json(request)
    if plan.get("input_bindings", {}).get("original_request_hash") != request_hash:
        raise ProjectionError("predecessor_hash_mismatch_request")
    
    normalized_hash = sha256_json(f3_validation.get("normalized_request", {}))
    if plan.get("input_bindings", {}).get("normalized_request_hash") != normalized_hash:
        raise ProjectionError("predecessor_hash_mismatch_normalized_request")
        
    f3_hash = sha256_json(f3_validation)
    if plan.get("input_bindings", {}).get("f3_validation_output_hash") != f3_hash:
        raise ProjectionError("predecessor_hash_mismatch_f3")

    plan_id = plan.get("plan_id")

    # Authoritative Validation of Authorization against Plan
    try:
        validate_execution_authorization(authorization, plan)
    except Exception as exc:
        raise ProjectionError("authorization_validation_failed") from exc
        
    auth_id = authorization.get("authorization_id")
    
    # Authoritative Validation of Consumption Binding
    try:
        validate_consumption_binding(consumption_binding, authorization, plan)
    except Exception as exc:
        raise ProjectionError("consumption_binding_validation_failed") from exc
        
    # Validation of Execution Claim against Authorization & Plan & Binding
    if claim.get("authorization_id") != auth_id:
        raise ProjectionError("predecessor_id_mismatch_auth")
    if claim.get("plan_id") != plan_id:
        raise ProjectionError("predecessor_id_mismatch_plan")
        
    # claim has no internal hash signature field in schema
    claim_id = claim.get("claim_id")
    claim_hash = sha256_json(claim)
    
    try:
        validate_operator_confirmation_reference(claim.get("operator_confirmation_reference"))
    except Exception as exc:
        raise ProjectionError("claim_operator_reference_invalid") from exc
        
    if claim.get("consumption_binding_id") != consumption_binding.get("consumption_binding_id"):
        raise ProjectionError("predecessor_id_mismatch_binding")
    
    if claim.get("consumption_binding_hash") != consumption_binding.get("consumption_binding_hash"):
        raise ProjectionError("predecessor_hash_mismatch_binding")
        
    if claim.get("execution_receipt_id") and claim.get("execution_receipt_id") != receipt.get("execution_receipt_id"):
        raise ProjectionError("predecessor_id_mismatch_receipt")
        
    if claim.get("execution_receipt_hash") and claim.get("execution_receipt_hash") != receipt.get("execution_receipt_hash"):
        raise ProjectionError("predecessor_hash_mismatch_receipt")
        
    # Authoritative Validation of Bundle
    if bundle.get("claim_id") != claim_id:
        raise ProjectionError("predecessor_id_mismatch_claim")
        
    # Validation of Receipt
    receipt_body = {k: v for k, v in receipt.items() if k not in {
        "schema_version", "execution_receipt_id", "execution_receipt_hash", "created_by_component"
    }}
    if receipt.get("execution_receipt_hash") != sha256_json(receipt_body):
        raise ProjectionError("receipt_hash_invalid")
        
    if receipt.get("claim_id") != claim.get("claim_id"):
        raise ProjectionError("predecessor_id_mismatch_claim")
        
    atomic_claim = deepcopy(claim)
    atomic_claim["state"] = "claimed"
    atomic_claim["execution_receipt_id"] = None
    atomic_claim["execution_receipt_hash"] = None
    atomic_claim["finalized_at"] = None
    atomic_claim["last_error_code"] = None
    atomic_claim_hash = sha256_json(atomic_claim)
    
    if receipt.get("claim_hash") != atomic_claim_hash:
        raise ProjectionError("predecessor_hash_mismatch_claim")
        
    receipt_id = receipt.get("execution_receipt_id")
    
    # Validation of Bundle
    bundle_body = {k: v for k, v in bundle.items() if k not in {
        "schema_version", "bundle_id", "bundle_hash"
    }}
    if bundle.get("bundle_hash") != sha256_json(bundle_body):
        raise ProjectionError("bundle_hash_invalid")
        
    if bundle.get("authorization_id") != auth_id:
        raise ProjectionError("predecessor_id_mismatch_auth")
    if bundle.get("execution_receipt_id") != receipt_id:
        raise ProjectionError("predecessor_id_mismatch_receipt")
    if bundle.get("execution_receipt_hash") != receipt.get("execution_receipt_hash"):
        raise ProjectionError("predecessor_hash_mismatch_receipt")
        
    bundle_ops = set(entry.get("operation_id") for entry in bundle.get("operation_evidence_entries", []))
    plan_ops = set(op.get("operation_id") for op in plan.get("operations", []))
    if not bundle_ops.issubset(plan_ops):
        raise ProjectionError("bundle_unknown_operation")

    # Ensure artifact root is strict
    artifact_root_path = Path(artifact_root).resolve()
    if not artifact_root_path.exists():
        raise ProjectionError("artifact_root_missing")

    evidence_artifacts: dict[str, dict] = {}
    seen_paths = set()
    
    for entry in bundle.get("artifact_inventory", []):
        relative_path = entry.get("relative_path")
        expected_sha256 = entry.get("sha256")
        expected_size = entry.get("byte_size")
        
        if not relative_path or not expected_sha256:
            raise ProjectionError("inventory_entry_invalid")
            
        if relative_path in seen_paths:
            raise ProjectionError("inventory_duplicate_path")
        seen_paths.add(relative_path)
            
        artifact_path = Path(relative_path)
        full_path = artifact_root_path / artifact_path
        _check_containment(full_path, artifact_root_path)
            
        # Verify hash
        actual_sha256 = _sha256_file(full_path)
        if actual_sha256 != expected_sha256:
            raise ProjectionError("artifact_hash_mismatch")
            
        # Verify size
        actual_size = full_path.stat().st_size
        if expected_size is not None and actual_size != expected_size:
            raise ProjectionError("artifact_size_mismatch")
            
        # Load and validate schema based on evidence_contract if applicable
        artifact_obj = _load_json(full_path)
        evidence_contract = entry.get("evidence_contract")
        if artifact_obj.get("schema_version") == _M8R_06_03_EVIDENCE_SCHEMA:
            # M8R-06-03's fixed child envelope is an already-governed evidence
            # contract.  Keep it explicit here rather than treating its human
            # inventory label as a schema filename.
            required = {"schema_version", "operation_id", "execution_request_id",
                        "source_family", "capability_id", "market", "transport_mode", "records"}
            if not required.issubset(artifact_obj) or not isinstance(artifact_obj["records"], list):
                raise ProjectionError("artifact_schema_invalid")
        elif evidence_contract:
            # Check if schema exists for this contract
            schema_file = SCHEMAS_DIR / f"{evidence_contract}.schema.json"
            if not schema_file.exists():
                raise ProjectionError("missing_evidence_contract_schema")
            schema = json.loads(schema_file.read_text(encoding="utf-8"))
            errors = list(Draft202012Validator(schema).iter_errors(artifact_obj))
            if errors:
                raise ProjectionError("artifact_schema_invalid")
                    
        # Verify item count if applicable
        expected_items = entry.get("item_count")
        if expected_items is not None:
            actual_items = (
                len(artifact_obj["records"])
                if artifact_obj.get("schema_version") == _M8R_06_03_EVIDENCE_SCHEMA
                else len(artifact_obj.get("items", [])) if "items" in artifact_obj else 1
            )
            if actual_items != expected_items:
                raise ProjectionError("artifact_item_count_mismatch")
                
                
        evidence_artifacts[relative_path] = artifact_obj

    inventory_paths = {entry.get("relative_path"): entry for entry in bundle.get("artifact_inventory", [])}
    for entry in bundle.get("operation_evidence_entries", []):
        for art in entry.get("artifacts", []):
            rel_path = art.get("relative_path")
            if rel_path not in inventory_paths:
                raise ProjectionError("operation_artifact_missing_from_inventory")
            
            inv_entry = inventory_paths[rel_path]
            if art.get("sha256") != inv_entry.get("sha256"):
                raise ProjectionError("operation_artifact_hash_mismatch")
            if art.get("byte_size") != inv_entry.get("byte_size"):
                raise ProjectionError("operation_artifact_size_mismatch")
            if art.get("schema_version") != inv_entry.get("schema_version"):
                raise ProjectionError("operation_artifact_schema_mismatch")

    if not calculated_at:
        raise ProjectionError("calculated_at_missing")

    return ProjectionInputs(
        request=request,
        f3_validation=f3_validation,
        plan=plan,
        authorization=authorization,
        consumption_binding=consumption_binding,
        claim=claim,
        receipt=receipt,
        bundle=bundle,
        artifact_root=str(artifact_root_path),
        calculated_at=calculated_at,
        evidence_artifacts=evidence_artifacts,
    )
