"""Server-owned, post-execution Mode C result materialization."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from scripts.m8r_05b_03.canonical import sha256_json
from scripts.m8r_05c.artifact_loader import load_projection_inputs
from scripts.m8r_05c.audit_package_builder import build_audit_package
from scripts.m8r_05c.containment import materialize_outputs
from scripts.m8r_05c.citation_builder import build_citation_index
from scripts.m8r_05c.errors import ProjectionError
from scripts.m8r_05c.lineage_resolver import build_lineage_map
from scripts.m8r_05c.markdown_renderer import render_result_markdown
from scripts.m8r_05c.result_builder import build_result
from scripts.m8r_05c.evidence_projector import CURRENT_PROJECTOR_VERSION, SUPPORTED_PROJECTOR_VERSIONS
from server.services.unified_mode_a import validate_mode_a_request
from server.services.unified_mode_b2 import CONTROL_ROOT
from server.services.watchlist_evidence_composer import (
    WatchlistEvidenceCompositionError,
    validate_selection_provenance,
)

_OUTPUT_PATHS = {
    "unified_market_evidence_result.v1": (
        "ai_context/unified_market_evidence_result.v1.json",
        "ai_context/unified_market_evidence_result.v1.md",
        "audit/unified_market_evidence_audit_package.v1.json",
        "unified_market_evidence_audit_package.v1",
    ),
    "unified_market_evidence_result.v2": (
        "ai_context/unified_market_evidence_result.v2.json",
        "ai_context/unified_market_evidence_result.v2.md",
        "audit/unified_market_evidence_audit_package.v2.json",
        "unified_market_evidence_audit_package.v2",
    ),
}
_RESULT, _MARKDOWN, _AUDIT, _AUDIT_SCHEMA = _OUTPUT_PATHS["unified_market_evidence_result.v1"]


class ModeCError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _read(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ModeCError("mode_c_artifact_unavailable") from exc
    if not isinstance(value, dict):
        raise ModeCError("mode_c_artifact_invalid")
    return value


def _find(directory: Path, id_key: str, value: str) -> Path:
    matches = [p for p in directory.glob("*.json") if _read(p).get(id_key) == value]
    if len(matches) != 1:
        raise ModeCError("mode_c_required_execution_artifact_missing")
    return matches[0]


def _verify_control(package: Path, control_id: str) -> dict[str, Path]:
    manifest = _read(package / "control" / "manifest.json")
    if manifest.get("authorization_id") != control_id:
        raise ModeCError("control_package_id_invalid")
    files = {
        "request": package / "control" / "request.json", "plan": package / "control" / "plan.json",
        "authorization": package / "control" / "authorization.json",
        "consumption_binding": package / "control" / "consumption_binding.json",
        "preflight": package / "control" / "preflight.json",
        "unused_consumption_state": package / "control" / "unused_consumption_state.json",
    }
    expected = manifest.get("artifact_hashes", {})
    if not isinstance(expected, dict):
        raise ModeCError("mode_c_control_integrity_failed")
    if "selection_provenance" in expected:
        files["selection_provenance"] = package / "control" / "selection_provenance.json"
    if set(expected) != set(files):
        raise ModeCError("mode_c_control_integrity_failed")
    for name, path in files.items():
        try:
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError as exc:
            raise ModeCError("mode_c_control_integrity_failed") from exc
        if actual != expected.get(name):
            raise ModeCError("mode_c_control_integrity_failed")
    return files


def _load_verified(control_id: str) -> tuple[Path, dict[str, Path], Path, Path, Path, Path]:
    if not isinstance(control_id, str) or not control_id.startswith("umea-v1-") or len(control_id) > 128:
        raise ModeCError("control_package_id_invalid")
    package = (CONTROL_ROOT / control_id).resolve()
    if package.parent != CONTROL_ROOT.resolve() or not package.is_dir():
        raise ModeCError("control_package_id_invalid")
    controls = _verify_control(package, control_id)
    claim_path = _find(package / "claims", "authorization_id", control_id)
    claim = _read(claim_path)
    if claim.get("state") not in {"consumed_success", "consumed_partial", "consumed_failed"}:
        raise ModeCError("mode_c_execution_not_finalized")
    receipt_path = _find(package / "receipts", "execution_receipt_id", claim.get("execution_receipt_id"))
    bundle_path = _find(package / "bundles", "claim_id", claim.get("claim_id"))
    return package, controls, claim_path, receipt_path, bundle_path, package / "mode_c" / "f3_validation.json"


def _f3(package: Path, controls: dict[str, Path], f3_path: Path) -> None:
    request = _read(controls["request"])
    plan = _read(controls["plan"])
    rebuilt = validate_mode_a_request(request)
    if sha256_json(rebuilt) != plan.get("input_bindings", {}).get("f3_validation_output_hash"):
        raise ModeCError("mode_c_f3_reconstruction_mismatch")
    encoded = json.dumps(rebuilt, ensure_ascii=False, sort_keys=True, indent=2)
    if f3_path.exists():
        if f3_path.read_text(encoding="utf-8") != encoded:
            raise ModeCError("mode_c_existing_output_inconsistent")
    else:
        f3_path.parent.mkdir(parents=True, exist_ok=True)
        f3_path.write_text(encoded, encoding="utf-8")


def _receipt_calculated_at(receipt_obj: dict[str, Any]) -> tuple[str | None, str]:
    if receipt_obj.get("finalized_at"):
        return receipt_obj["finalized_at"], "receipt.finalized_at"
    if receipt_obj.get("execution_completed_at"):
        return receipt_obj["execution_completed_at"], "receipt.execution_completed_at"
    return None, "explicit_calculated_at_input"


def _inputs(package: Path, c: dict[str, Path], claim: Path, receipt: Path, bundle: Path, f3: Path):
    calculated_at, calculated_at_source = _receipt_calculated_at(_read(receipt))
    try:
        return load_projection_inputs(request_path=str(c["request"]), f3_validation_path=str(f3), plan_path=str(c["plan"]), authorization_path=str(c["authorization"]), consumption_binding_path=str(c["consumption_binding"]), claim_path=str(claim), receipt_path=str(receipt), bundle_path=str(bundle), artifact_root=str(package), calculated_at=calculated_at, calculated_at_source=calculated_at_source)
    except ProjectionError as exc:
        raise ModeCError("mode_c_lineage_verification_failed") from exc


def _expected_outputs(
    inputs: Any,
    projector_version: str = CURRENT_PROJECTOR_VERSION,
    selection_provenance: dict[str, Any] | None = None,
    output_schema_version: str = "unified_market_evidence_result.v1",
) -> tuple[dict[str, Any], dict[str, Any], str]:
    """Rebuild the complete 05C projection from verified predecessors only."""
    try:
        result_path, _markdown_path, audit_path, audit_schema_version = _OUTPUT_PATHS[output_schema_version]
        result = build_result(inputs, projector_version=projector_version,
                              output_schema_version=output_schema_version)
        citation_index = build_citation_index(
            build_lineage_map(inputs), inputs.bundle, output_schema_version,
        )
        audit = build_audit_package(
            result=result,
            inputs=inputs,
            citation_index=citation_index,
            result_relative_path=result_path, projector_version=projector_version,
            selection_provenance=selection_provenance,
            output_schema_version=audit_schema_version,
        )
        return result, audit, render_result_markdown(result, projector_version=projector_version)
    except ProjectionError as exc:
        raise ModeCError("mode_c_lineage_verification_failed") from exc


def _persisted_output_version(package: Path) -> str | None:
    complete: list[str] = []
    partial = False
    for version, (result_rel, markdown_rel, audit_rel, _audit_schema) in _OUTPUT_PATHS.items():
        present = [(package / rel).exists() for rel in (result_rel, markdown_rel, audit_rel)]
        if all(present):
            complete.append(version)
        elif any(present):
            partial = True
    if partial or len(complete) > 1:
        raise ModeCError("mode_c_existing_output_inconsistent")
    return complete[0] if complete else None


def _read_verified_outputs(
    package: Path, output_schema_version: str,
    expected_result: dict[str, Any], expected_audit: dict[str, Any], expected_markdown: str,
) -> tuple[dict[str, Any], dict[str, Any], str] | None:
    result_rel, markdown_rel, audit_rel, _audit_schema = _OUTPUT_PATHS[output_schema_version]
    result_path, markdown_path, audit_path = package / result_rel, package / markdown_rel, package / audit_rel
    present = [path.exists() for path in (result_path, markdown_path, audit_path)]
    if not any(present):
        return None
    if not all(path.is_file() for path in (result_path, markdown_path, audit_path)):
        raise ModeCError("mode_c_existing_output_inconsistent")
    try:
        result, audit = _read(result_path), _read(audit_path)
        markdown = markdown_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ModeCError("mode_c_existing_output_inconsistent") from exc
    if result != expected_result or audit != expected_audit or markdown != expected_markdown:
        raise ModeCError("mode_c_existing_output_inconsistent")
    return result, audit, markdown


def build_mode_c_result_package(
    payload: dict[str, Any], *,
    output_schema_version: str = "unified_market_evidence_result.v1",
) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != {"control_package_id"}:
        raise ModeCError("invalid_api_envelope")
    if output_schema_version in {"v1", "v2"}:
        output_schema_version = f"unified_market_evidence_result.{output_schema_version}"
    if output_schema_version not in _OUTPUT_PATHS:
        raise ModeCError("unsupported_output_schema_version")
    package, controls, claim, receipt, bundle, f3 = _load_verified(payload["control_package_id"])
    persisted_version = _persisted_output_version(package)
    if persisted_version is not None:
        output_schema_version = persisted_version
        if not f3.is_file():
            raise ModeCError("mode_c_existing_output_inconsistent")
    else:
        _f3(package, controls, f3)
    inputs = _inputs(package, controls, claim, receipt, bundle, f3)
    selection_provenance = None
    if "selection_provenance" in controls:
        selection_provenance = _read(controls["selection_provenance"])
        try:
            validate_selection_provenance(selection_provenance, inputs.request)
        except WatchlistEvidenceCompositionError as exc:
            raise ModeCError("mode_c_control_integrity_failed") from exc
    result_rel, markdown_rel, audit_rel, _audit_schema = _OUTPUT_PATHS[output_schema_version]
    audit_path = package / audit_rel
    projector_version = CURRENT_PROJECTOR_VERSION
    if audit_path.is_file():
        projector_version = _read(audit_path).get("projector_metadata", {}).get("projector_version", CURRENT_PROJECTOR_VERSION)
        if projector_version not in SUPPORTED_PROJECTOR_VERSIONS:
            raise ModeCError("mode_c_existing_output_inconsistent")
    expected_result, expected_audit, expected_markdown = _expected_outputs(
        inputs, projector_version, selection_provenance, output_schema_version
    )
    existing = _read_verified_outputs(
        package, output_schema_version, expected_result, expected_audit, expected_markdown,
    )
    if existing is not None:
        result, audit, markdown = existing
        materialization = "existing_verified"
    else:
        try:
            materialize_outputs(output_root=str(package), result_json=expected_result, audit_package_json=expected_audit, result_markdown=expected_markdown, result_relative_path=result_rel, audit_relative_path=audit_rel, result_md_relative_path=markdown_rel)
        except ProjectionError as exc:
            raise ModeCError("mode_c_materialization_failed") from exc
        result, audit, markdown = expected_result, expected_audit, expected_markdown
        materialization = "newly_materialized"
    return {"result_id": result["result_id"], "result_hash": result["result_hash"], "result_status": result["status"], "request_summary": result["request_summary"], "targets": result["targets"], "request_caveats": result.get("request_caveats", []), "citation_references": [c for t in result["targets"] for c in t.get("citations", [])], "ai_ready_markdown": markdown, "canonical_result": result, "canonical_result_reference": result_rel, "audit_package_id": audit["audit_package_id"], "audit_reference": audit_rel, "selection_provenance_identity": audit.get("selection_provenance_identity"), "materialization": materialization, "external_market_network_executed": False, "output_schema_version": output_schema_version}


def read_mode_c_audit(control_package_id: str, output_schema_version: str = "unified_market_evidence_result.v1") -> dict[str, Any]:
    """Return a verified persisted audit only after the same post-execution checks."""
    package_result = build_mode_c_result_package(
        {"control_package_id": control_package_id}, output_schema_version=output_schema_version,
    )
    package, *_ = _load_verified(control_package_id)
    return _read(package / _OUTPUT_PATHS[package_result["output_schema_version"]][2])


def build_mode_c_ai_handoff(control_package_id: str, output_schema_version: str = "unified_market_evidence_result.v1") -> dict[str, Any]:
    """Return only verified, AI-safe Mode C material for a finalized package."""
    result_package = build_mode_c_result_package(
        {"control_package_id": control_package_id}, output_schema_version=output_schema_version,
    )
    audit = read_mode_c_audit(control_package_id, output_schema_version)
    citations = audit.get("citation_to_operation_map")
    if not isinstance(citations, list):
        raise ModeCError("mode_c_existing_output_inconsistent")
    fields = ("citation_id", "canonical_target_id", "capability_id", "executor_id", "artifact_relative_path", "artifact_hash")
    citation_references = []
    for citation in citations:
        if not isinstance(citation, dict) or any(field not in citation for field in fields):
            raise ModeCError("mode_c_existing_output_inconsistent")
        citation_references.append({field: citation[field] for field in fields})
    citation_references.sort(key=lambda item: tuple(str(item[field]) for field in fields))
    package, _, _, receipt_path, _, _ = _load_verified(control_package_id)
    receipt = _read(receipt_path)
    outcome = receipt.get("overall_status")
    if not isinstance(outcome, str):
        raise ModeCError("mode_c_existing_output_inconsistent")
    canonical_result = result_package["canonical_result"]
    request_summary = canonical_result.get("request_summary", {})
    return {
        "service_contract_version": "unified_market_evidence_local_service.v1",
        "control_package_id": control_package_id,
        "result_id": result_package["result_id"],
        "result_hash": result_package["result_hash"],
        "result_status": result_package["result_status"],
        "request_id": canonical_result.get("request_id"),
        "request_mode": request_summary.get("execution_mode"),
        "execution_outcome": outcome,
        "canonical_result": canonical_result,
        "ai_ready_markdown": result_package["ai_ready_markdown"],
        "citation_references": citation_references,
        "canonical_result_reference": result_package["canonical_result_reference"],
        "audit_package_id": result_package["audit_package_id"],
        "audit_reference": result_package["audit_reference"],
        "selection_provenance_identity": result_package.get("selection_provenance_identity"),
        "materialization": result_package["materialization"],
        "additional_market_network_executed": False,
    }
