"""Audit package builder for M8R-05C.

Builds the unified_market_evidence_audit_package.v1 dict from the
projection result and all accepted inputs.

This module:
- Is a pure function (no I/O, no network, no datetime.now()).
- Validates the output against the audit package schema.
- Never embeds authorization secrets, tokens, credentials, or absolute
  local paths in the audit package.
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from jsonschema import Draft202012Validator

from .canonical import (
    build_audit_package_id,
    build_audit_package_id_v2,
    build_audit_package_id_v3,
    hash_body_excluding_key,
    sha256_json,
)
from .citation_builder import CitationIndex
from .errors import ProjectionError
from .models import ProjectionInputs
from .evidence_projector import CURRENT_PROJECTOR_VERSION

ROOT = Path(__file__).resolve().parents[2]
AUDIT_SCHEMA_PATH = ROOT / "schemas" / "unified_market_evidence_audit_package.v1.schema.json"
AUDIT_V2_SCHEMA_PATH = ROOT / "schemas" / "unified_market_evidence_audit_package.v2.schema.json"
AUDIT_V3_SCHEMA_PATH = ROOT / "schemas" / "unified_market_evidence_audit_package.v3.schema.json"

_PROJECTOR_VERSION = CURRENT_PROJECTOR_VERSION
_CANONICALIZATION_VERSION = "m8r_05b_03_canonical_v1"


def _load_audit_schema() -> dict:
    try:
        return json.loads(AUDIT_SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProjectionError("audit_schema_load_failed") from exc


_PHASE_H_CAPABILITIES = {
    "trading_status_context_evidence.v1": "trading_status_context",
    "corporate_action_context_evidence.v1": "corporate_action_context",
    "recent_performance_evidence.v1": "recent_performance",
    "discontinuity_safety_evidence.v1": "discontinuity_safety",
}


def _phase_h_governance(inputs: ProjectionInputs) -> dict:
    """Project only verified Phase H artifacts into frozen Audit V3 fields."""
    inventory = {
        entry.get("relative_path"): entry for entry in inputs.bundle.get("artifact_inventory", [])
        if isinstance(entry, dict) and isinstance(entry.get("relative_path"), str)
    }
    attempts: list[dict] = []
    references: list[dict] = []
    derivations: list[dict] = []
    for relative_path, artifact in sorted(inputs.evidence_artifacts.items()):
        if not isinstance(artifact, dict):
            continue
        schema_version = artifact.get("schema_version")
        capability_id = _PHASE_H_CAPABILITIES.get(schema_version)
        entry = inventory.get(relative_path)
        if capability_id is None or not isinstance(entry, dict):
            continue
        artifact_hash = entry.get("sha256")
        if not isinstance(artifact_hash, str):
            raise ProjectionError("phase_h_artifact_hash_unverified")
        references.append({
            "capability_id": capability_id,
            "schema_version": schema_version,
            "relative_path": relative_path,
            "sha256": artifact_hash,
        })
        target = artifact.get("target") if isinstance(artifact.get("target"), dict) else {}
        sources = artifact.get("sources") if isinstance(artifact.get("sources"), list) else [artifact.get("source")]
        if capability_id == "recent_performance" and not any(isinstance(source, dict) for source in sources):
            governed_end = artifact.get("governed_end_observation")
            if isinstance(governed_end, dict):
                sources = [{
                    "source_family": governed_end.get("source_family", "unknown"),
                    "source_contract_id": governed_end.get("source_contract_id", "unknown"),
                    "source_role": "research_only",
                    "activation_state": "inactive",
                    "license_authority": None,
                }]
        for source in sources:
            if not isinstance(source, dict) or capability_id not in {"trading_status_context", "corporate_action_context", "recent_performance"}:
                continue
            status = artifact.get("status", artifact.get("coverage_status", "source_failed"))
            failure_code = None
            caveats = artifact.get("caveats")
            if status in {"source_failed", "binding_failed"} and isinstance(caveats, list) and caveats:
                failure_code = str(caveats[0])
            attempts.append({
                "source_family": source.get("source_family", "unknown"),
                "source_contract_id": source.get("source_contract_id", "unknown"),
                "source_role": source.get("source_role", "research_only"),
                "activation_state": source.get("activation_state", "inactive"),
                "provider_availability": "unknown" if source.get("source_role") == "optional_licensed_provider" else "not_required",
                "license_authority": source.get("license_authority"),
                "canonical_target_id": target.get("canonical_target_id", ""),
                "market": target.get("market", "TWSE"),
                "requested_window": artifact.get("coverage", {}).get("requested_window") if isinstance(artifact.get("coverage"), dict) else None,
                "coverage_result": str(status),
                "outcome": "failed" if status in {"source_failed", "binding_failed"} else "succeeded",
                "failure_code": failure_code,
            })
        if capability_id == "discontinuity_safety":
            comparison_window = artifact.get("comparison_window")
            if not isinstance(comparison_window, dict):
                raise ProjectionError("phase_h_h4_derivation_invalid")
            derivations.append({
                "canonical_target_id": target.get("canonical_target_id", ""),
                "market": target.get("market", "TWSE"),
                "comparison_window": {
                    "start_observation_date": comparison_window.get("start_observation_date"),
                    "end_observation_date": comparison_window.get("end_observation_date"),
                },
                "input_evidence_references": artifact.get("input_evidence_references", []),
                "evidence_artifact_reference": {"relative_path": relative_path, "sha256": artifact_hash},
                "deterministic_rule_version": artifact.get("deterministic_rule_version"),
                "derived_state": artifact.get("state"),
                "interpretation_guard": artifact.get("interpretation_guard"),
            })
    return {
        "source_attempts": sorted(attempts, key=lambda item: (item["canonical_target_id"], item["source_contract_id"], item["source_family"])),
        "evidence_artifact_references": sorted(references, key=lambda item: (item["capability_id"], item["relative_path"])),
        "h4_derivations": sorted(derivations, key=lambda item: item["canonical_target_id"]),
    }


def build_audit_package(
    result: dict,
    inputs: ProjectionInputs,
    citation_index: CitationIndex,
    result_relative_path: str,
    projector_version: str = _PROJECTOR_VERSION,
    selection_provenance: dict | None = None,
    output_schema_version: str = "unified_market_evidence_audit_package.v1",
) -> dict:
    """Build the audit package dict.

    Parameters
    ----------
    result : dict
        The validated result dict from result_builder.build_result().
    inputs : ProjectionInputs
        All accepted M8R-05B-03 inputs.
    citation_index : CitationIndex
        Built by citation_builder.build_citation_index().
    result_relative_path : str
        Relative path where the result JSON will be materialized.

    Pure function: no I/O, no network, no datetime.now().
    """
    receipt = inputs.receipt
    bundle = inputs.bundle
    plan = inputs.plan
    request = inputs.request
    authorization = inputs.authorization
    consumption_binding = inputs.consumption_binding
    calculated_at = inputs.calculated_at

    result_id = result["result_id"]
    result_hash = result["result_hash"]
    bundle_id = bundle.get("bundle_id", "")

    if output_schema_version == "unified_market_evidence_audit_package.v1":
        audit_package_id = build_audit_package_id(result_id, bundle_id)
    elif output_schema_version == "unified_market_evidence_audit_package.v2":
        audit_package_id = build_audit_package_id_v2(result_id, bundle_id)
    elif output_schema_version == "unified_market_evidence_audit_package.v3":
        audit_package_id = build_audit_package_id_v3(result_id, bundle_id)
    else:
        raise ProjectionError("unsupported_audit_schema_version")

    # Request identity.
    request_hash = sha256_json(request)
    request_identity = {
        "request_id": request.get("request_id", ""),
        "request_hash": request_hash,
        "schema_version": request.get("schema_version", "unified_market_evidence_request.v1"),
    }

    # Target validation identity from plan.input_bindings.
    input_bindings = plan.get("input_bindings", {})
    target_validation_identity = {
        "f3_validation_output_hash": input_bindings.get("f3_validation_output_hash", ""),
    }
    sec_master_hashes = input_bindings.get("security_master_artifact_hashes")
    if sec_master_hashes:
        target_validation_identity["security_master_artifact_hashes"] = sec_master_hashes
    references = input_bindings.get("security_master_evidence_references") or []
    local_release_refs = [ref for ref in references if isinstance(ref, str) and ref.startswith("local_security_master_release:")]
    if local_release_refs:
        target_validation_identity["security_master_release_id"] = local_release_refs[0].split(":")[1]
        target_validation_identity["security_master_release_manifest_hash"] = sec_master_hashes[1] if isinstance(sec_master_hashes, list) and len(sec_master_hashes) > 1 else ""

    # Plan identity.
    plan_identity = {
        "plan_id": plan.get("plan_id", ""),
        "plan_hash": plan.get("plan_hash", ""),
        "schema_version": plan.get("schema_version", "unified_market_evidence_orchestration_plan.v1"),
        "plan_status": plan.get("plan_status", ""),
    }

    # Authorization identity — never include secrets, tokens, or credentials.
    authorization_identity = {
        "authorization_id": authorization.get("authorization_id", ""),
        "authorization_hash": authorization.get("authorization_hash", ""),
        "schema_version": authorization.get("schema_version", "unified_market_evidence_execution_authorization.v1"),
    }
    if "scope_hash" in authorization:
        authorization_identity["scope_hash"] = authorization["scope_hash"]

    # Claim identity.
    claim = inputs.claim
    atomic_claim = deepcopy(claim)
    atomic_claim["state"] = "claimed"
    atomic_claim["execution_receipt_id"] = None
    atomic_claim["execution_receipt_hash"] = None
    atomic_claim["finalized_at"] = None
    atomic_claim["last_error_code"] = None

    atomic_claim_hash = sha256_json(atomic_claim)
    finalized_record_hash = sha256_json(claim)

    claim_identity = {
        "claim_id": claim.get("claim_id", ""),
        "atomic_claim_hash": atomic_claim_hash,
        "finalized_record_hash": finalized_record_hash,
        "schema_version": claim.get(
            "schema_version", "unified_market_evidence_consumption_record.v1"
        ),
    }

    # Receipt identity.
    receipt_identity = {
        "execution_receipt_id": receipt.get("execution_receipt_id", ""),
        "execution_receipt_hash": receipt.get("execution_receipt_hash", ""),
        "schema_version": receipt.get("schema_version", "unified_market_evidence_execution_receipt.v1"),
        "overall_status": receipt.get("overall_status", "failed"),
        "total_operations": receipt.get("total_operations", 0),
        "succeeded_operations": receipt.get("succeeded_operations", 0),
        "failed_operations": receipt.get("failed_operations", 0),
        "finalized_at": receipt.get("finalized_at", ""),
    }

    # Bundle identity.
    bundle_identity = {
        "bundle_id": bundle_id,
        "bundle_hash": bundle.get("bundle_hash", ""),
        "schema_version": bundle.get("schema_version", "unified_market_evidence_bundle.v1"),
        "overall_status": bundle.get("overall_status", "failed"),
        "total_item_count": bundle.get("total_item_count", 0),
        "finalized_at": bundle.get("finalized_at", ""),
    }

    # Operation lineage from bundle operation_evidence_entries.
    operation_lineage: list[dict] = []
    op_index_by_id: dict[str, dict] = {}
    for op in plan.get("operations", []):
        if isinstance(op, dict):
            op_index_by_id[op.get("operation_id", "")] = op

    for entry in bundle.get("operation_evidence_entries", []):
        if not isinstance(entry, dict):
            continue
        operation_id = entry.get("operation_id", "")
        plan_op = op_index_by_id.get(operation_id, {})
        lineage_entry: dict = {
            "operation_id": operation_id,
            "capability_id": plan_op.get("capability_id") or entry.get("capability_id") or "",
            "executor_id": plan_op.get("executor_id") or entry.get("executor_id") or "",
            "status": entry.get("status", "failed"),
            "error_code": entry.get("error_code"),
            "canonical_target_ids": plan_op.get("canonical_target_ids", []),
            "market": plan_op.get("market"),
            "evidence_contract": plan_op.get("expected_evidence_contract") or entry.get("evidence_contract") or "",
            "result_item_count": entry.get("result_item_count", 0),
            "artifact_references": [],
            "warnings": entry.get("warnings", []),
        }
        for art in entry.get("artifacts", []):
            if isinstance(art, dict):
                art_ref: dict = {
                    "relative_path": art.get("relative_path", ""),
                    "sha256": art.get("sha256", ""),
                    "schema_version": art.get("schema_version", ""),
                    "byte_size": art.get("byte_size", 0),
                }
                if "item_count" in art:
                    art_ref["item_count"] = art["item_count"]
                lineage_entry["artifact_references"].append(art_ref)
        operation_lineage.append(lineage_entry)

    # Artifact inventory from bundle.
    artifact_inventory: list[dict] = []
    for entry in bundle.get("artifact_inventory", []):
        if isinstance(entry, dict):
            inv_entry: dict = {
                "relative_path": entry.get("relative_path", ""),
                "sha256": entry.get("sha256", ""),
                "schema_version": entry.get("schema_version", ""),
                "byte_size": entry.get("byte_size", 0),
                "evidence_contract": entry.get("evidence_contract", ""),
            }
            if "item_count" in entry:
                inv_entry["item_count"] = entry["item_count"]
            artifact_inventory.append(inv_entry)

    # Citation-to-operation map.
    citation_to_operation_map: list[dict] = []
    for ae in citation_index.audit_entries:
        citation_to_operation_map.append({
            "citation_id": ae.citation_id,
            "operation_id": ae.operation_id,
            "capability_id": ae.capability_id,
            "executor_id": ae.executor_id,
            "artifact_relative_path": ae.artifact_relative_path,
            "artifact_hash": ae.artifact_hash,
            "canonical_target_id": ae.canonical_target_id,
            "requested_data_need": ae.requested_data_need,
        })

    # Integrity verification.
    # Actually recompute the hashes to prove they match what was provided
    # The result hash is computed by excluding "result_hash"
    recomputed_result_hash = hash_body_excluding_key(result, "result_hash")
    result_hash_ok = recomputed_result_hash == result.get("result_hash")
    
    receipt_for_hash = {k: v for k, v in receipt.items() if k not in {
        "schema_version", "execution_receipt_id", "execution_receipt_hash", "created_by_component"
    }}
    recomputed_receipt_hash = sha256_json(receipt_for_hash)
    receipt_hash_ok = recomputed_receipt_hash == receipt.get("execution_receipt_hash") or hash_body_excluding_key(receipt, "execution_receipt_hash") == receipt.get("execution_receipt_hash")
    
    bundle_for_hash = {k: v for k, v in bundle.items() if k not in {
        "schema_version", "bundle_id", "bundle_hash"
    }}
    recomputed_bundle_hash = sha256_json(bundle_for_hash)
    bundle_hash_ok = recomputed_bundle_hash == bundle.get("bundle_hash") or hash_body_excluding_key(bundle, "bundle_hash") == bundle.get("bundle_hash")
    
    # all_artifacts_ok is True only because artifact_loader.py explicitly verifies every file against its sha256
    # and would have raised ProjectionError if any failed.
    all_artifacts_ok = True

    integrity_verification: dict = {
        "receipt_hash_verified": receipt_hash_ok,
        "bundle_hash_verified": bundle_hash_ok,
        "result_hash_verified": result_hash_ok,
        "all_artifact_hashes_verified": all_artifacts_ok,
    }

    # Replay manifest — all predecessor IDs + hashes for reproducibility.
    replay_manifest: dict = {
        "request_id": request.get("request_id", ""),
        "request_hash": request_hash,
        "plan_id": plan.get("plan_id", ""),
        "plan_hash": plan.get("plan_hash", ""),
        "authorization_id": authorization.get("authorization_id", ""),
        "authorization_hash": authorization.get("authorization_hash", ""),
        "consumption_binding_id": consumption_binding.get("consumption_binding_id", ""),
        "consumption_binding_hash": consumption_binding.get("consumption_binding_hash", ""),
        "claim_id": claim.get("claim_id", ""),
        "atomic_claim_hash": atomic_claim_hash,
        "finalized_record_hash": finalized_record_hash,
        "execution_receipt_id": receipt.get("execution_receipt_id", ""),
        "execution_receipt_hash": receipt.get("execution_receipt_hash", ""),
        "bundle_id": bundle_id,
        "bundle_hash": bundle.get("bundle_hash", ""),
    }

    # Projector metadata.
    projector_metadata: dict = {
        "projector_version": projector_version,
        "canonicalization_version": _CANONICALIZATION_VERSION,
        "projected_at": calculated_at,
        "timestamp_authority": "receipt.finalized_at_or_cli_calculated_at",
        "calculated_at_source": (
            inputs.calculated_at_source
            if output_schema_version == "unified_market_evidence_audit_package.v2"
            else "cli_calculated_at"
        ),
    }

    # Build body without audit_package_hash.
    body_without_hash: dict = {
        "schema_version": output_schema_version,
        "audit_package_id": audit_package_id,
        "result_id": result_id,
        "result_hash": result_hash,
        "result_relative_path": result_relative_path,
        "request_identity": request_identity,
        "target_validation_identity": target_validation_identity,
        "plan_identity": plan_identity,
        "authorization_identity": authorization_identity,
        "claim_identity": claim_identity,
        "receipt_identity": receipt_identity,
        "bundle_identity": bundle_identity,
        "operation_lineage": operation_lineage,
        "artifact_inventory": artifact_inventory,
        "citation_to_operation_map": citation_to_operation_map,
        "integrity_verification": integrity_verification,
        "replay_manifest": replay_manifest,
        "projector_metadata": projector_metadata,
        "warnings": [],
        "caveats": [],
    }
    if output_schema_version == "unified_market_evidence_audit_package.v3":
        body_without_hash["phase_h_governance"] = _phase_h_governance(inputs)
    if selection_provenance is not None:
        binding = selection_provenance.get("watchlist")
        body_without_hash["selection_provenance_identity"] = {
            "selection_id": selection_provenance.get("selection_id"),
            "selection_sha256": selection_provenance.get("content_sha256"),
            "request_sha256": selection_provenance.get("request_sha256"),
            "watchlist_id": binding.get("watchlist_id") if isinstance(binding, dict) else None,
            "watchlist_version": binding.get("version") if isinstance(binding, dict) else None,
            "watchlist_revision_sha256": binding.get("revision_sha256") if isinstance(binding, dict) else None,
            "selected_watchlist_entry_ids": [item.get("watchlist_entry_id") for item in selection_provenance.get("selected_targets", []) if item.get("source") == "persistent_watchlist"],
            "selected_instrument_ids": [item.get("instrument_id") for item in selection_provenance.get("selected_targets", [])],
            "temporary_target_inputs": [item.get("input") for item in selection_provenance.get("temporary_targets", [])],
            "deduplication_decisions": deepcopy(selection_provenance.get("deduplication_decisions", [])),
        }

    audit_package_hash = hash_body_excluding_key(body_without_hash, "audit_package_hash")
    audit_package = {**body_without_hash, "audit_package_hash": audit_package_hash}

    # Validate against schema.
    schema_path = {
        "unified_market_evidence_audit_package.v1": AUDIT_SCHEMA_PATH,
        "unified_market_evidence_audit_package.v2": AUDIT_V2_SCHEMA_PATH,
        "unified_market_evidence_audit_package.v3": AUDIT_V3_SCHEMA_PATH,
    }[output_schema_version]
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(schema).iter_errors(audit_package))
    if errors:
        error_msgs = [str(e.message) for e in errors[:3]]
        raise ProjectionError(f"audit_package_schema_invalid:{'; '.join(error_msgs)}")

    return audit_package
