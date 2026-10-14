"""Internal, read-only inspection of one retained finalized control package.

No Mode A lookup or Mode C materialization is invoked. Missing historical F3
bytes cannot be recreated from a hash alone and are treated as missing evidence.
Migration states are reserved: no installation-state version authority exists yet.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from scripts.m8r_05c.artifact_loader import load_projection_inputs, _SCHEMA_NAMES
from scripts.m8r_05c.errors import ProjectionError
from server.services import unified_mode_c as mode_c
from server.services.unified_contract_versions import REQUEST_SCHEMA_PATHS


class _InspectionFailure(Exception):
    def __init__(self, state: str, reason: str):
        self.state, self.reason = state, reason


def _version(value: Any) -> str | None:
    """Never expose arbitrary persisted bodies as version facts."""
    return value if isinstance(value, str) and len(value) <= 128 else None


def _contained_file(package: Path, path: Path) -> None:
    if package not in path.resolve().parents:
        raise _InspectionFailure("REPLAY_UNAVAILABLE_INTEGRITY_FAILED", "artifact_outside_package")
    if not path.is_file():
        raise _InspectionFailure("REPLAY_UNAVAILABLE_MISSING_ARTIFACT", "required_artifact_missing")


def _find_retained(directory: Path, key: str, value: Any) -> Path:
    try:
        return mode_c._find(directory, key, value)
    except mode_c.ModeCError as exc:
        if exc.code == "mode_c_required_execution_artifact_missing":
            matches = [p for p in directory.glob("*.json") if mode_c._read(p).get(key) == value]
            if len(matches) > 1:
                raise _InspectionFailure("REPLAY_UNAVAILABLE_INTEGRITY_FAILED", "ambiguous_execution_artifact") from exc
        raise


def inspect_finalized_package(control_package_id: str, *, control_root: Path | None = None) -> dict[str, Any]:
    """Return bounded facts only; the root override is an internal test seam.

    Historical F3 is loaded and cryptographically verified in memory by the
    existing projection loader. Nothing is reconstructed using current identity
    state, and no output is materialized.
    """
    facts = dict(control_package_id=None, request_schema_version=None,
                 result_schema_version=None, audit_schema_version=None,
                 projector_version=None, persisted_output_presence="unknown")
    try:
        if not isinstance(control_package_id, str) or not re.fullmatch(r"umea-v1-[A-Za-z0-9_-]{1,120}", control_package_id):
            raise _InspectionFailure("REPLAY_UNAVAILABLE_INTEGRITY_FAILED", "control_package_id_invalid")
        facts["control_package_id"] = control_package_id
        root = Path(control_root if control_root is not None else mode_c.CONTROL_ROOT).resolve()
        package = (root / control_package_id).resolve()
        if package.parent != root:
            raise _InspectionFailure("REPLAY_UNAVAILABLE_INTEGRITY_FAILED", "control_package_id_invalid")
        _contained_file(package, package / "control/manifest.json")
        manifest = mode_c._read(package / "control/manifest.json")
        if manifest.get("schema_version") != "m8r_06_03_control_package.v1":
            raise _InspectionFailure("REPLAY_UNAVAILABLE_UNSUPPORTED_VERSION", "unsupported_control_schema_version")
        # Check containment before any helper reads package members (including
        # symlinked control/claim/receipt/bundle/output directories).
        names = ["request", "plan", "authorization", "consumption_binding", "preflight", "unused_consumption_state"]
        if "selection_provenance" in manifest.get("artifact_hashes", {}):
            names.append("selection_provenance")
        for name in names:
            _contained_file(package, package / f"control/{name}.json")
        controls = mode_c._verify_control(package, control_package_id)
        for directory in ("claims", "receipts", "bundles", "ai_context", "audit", "mode_c"):
            parent = package / directory
            if parent.exists() and package not in parent.resolve().parents:
                raise _InspectionFailure("REPLAY_UNAVAILABLE_INTEGRITY_FAILED", "artifact_outside_package")
            for path in parent.glob("*.json"):
                _contained_file(package, path)
        facts["request_schema_version"] = _version(mode_c._read(controls["request"]).get("schema_version"))
        if facts["request_schema_version"] not in REQUEST_SCHEMA_PATHS:
            raise _InspectionFailure("REPLAY_UNAVAILABLE_UNSUPPORTED_VERSION", "unsupported_request_schema_version")
        claim = _find_retained(package / "claims", "authorization_id", control_package_id)
        claim_obj = mode_c._read(claim)
        if claim_obj.get("state") not in {"consumed_success", "consumed_partial", "consumed_failed"}:
            raise _InspectionFailure("REPLAY_UNAVAILABLE_INTEGRITY_FAILED", "execution_not_finalized")
        receipt = _find_retained(package / "receipts", "execution_receipt_id", claim_obj.get("execution_receipt_id"))
        bundle = _find_retained(package / "bundles", "claim_id", claim_obj.get("claim_id"))
        # Unknown output filenames must never be mistaken for absent outputs.
        known = {rel for paths in mode_c._OUTPUT_PATHS.values() for rel in paths[:3]}
        outputs = [p for directory in ("ai_context", "audit") for p in (package / directory).glob("unified_market_evidence_*")]
        facts["persisted_output_presence"] = "present" if outputs else "absent"
        for path in outputs:
            _contained_file(package, path)
            if path.relative_to(package).as_posix() not in known:
                raise _InspectionFailure("REPLAY_UNAVAILABLE_UNSUPPORTED_VERSION", "unsupported_output_schema_version")
        version = mode_c._persisted_output_version(package)
        if version:
            result_rel, _, audit_rel, _ = mode_c._OUTPUT_PATHS[version]
            facts["result_schema_version"] = _version(mode_c._read(package / result_rel).get("schema_version"))
            audit_obj = mode_c._read(package / audit_rel)
            facts["audit_schema_version"] = _version(audit_obj.get("schema_version"))
            if facts["result_schema_version"] != version or facts["audit_schema_version"] != mode_c._OUTPUT_PATHS[version][3]:
                raise _InspectionFailure("REPLAY_UNAVAILABLE_UNSUPPORTED_VERSION", "unsupported_output_schema_version")
            facts["projector_version"] = _version(audit_obj.get("projector_metadata", {}).get("projector_version"))
            if facts["projector_version"] not in mode_c.SUPPORTED_PROJECTOR_VERSIONS:
                raise _InspectionFailure("REPLAY_UNAVAILABLE_UNSUPPORTED_VERSION", "unsupported_projector_version")
        f3 = package / "mode_c/f3_validation.json"
        _contained_file(package, f3)
        predecessors = {name: controls[name] for name in ("plan", "authorization", "consumption_binding")}
        predecessors.update(f3_validation=f3, claim=claim, receipt=receipt, bundle=bundle)
        for name, path in predecessors.items():
            if mode_c._read(path).get("schema_version") != _SCHEMA_NAMES[name].removesuffix(".schema.json"):
                raise _InspectionFailure("REPLAY_UNAVAILABLE_UNSUPPORTED_VERSION", "unsupported_predecessor_schema_version")
        for entry in mode_c._read(bundle).get("artifact_inventory", []):
            # The loader resolves schema filenames from evidence_contract.
            # Reject path syntax before handing it any untrusted contract name.
            contract = entry.get("evidence_contract")
            if contract is not None and (not isinstance(contract, str) or not re.fullmatch(r"[A-Za-z0-9_]+\.v[0-9]+", contract)):
                raise _InspectionFailure("REPLAY_UNAVAILABLE_INTEGRITY_FAILED", "evidence_contract_invalid")
        calculated_at, source = mode_c._receipt_calculated_at(mode_c._read(receipt))
        inputs = load_projection_inputs(
            request_path=str(controls["request"]), f3_validation_path=str(f3),
            plan_path=str(controls["plan"]), authorization_path=str(controls["authorization"]),
            consumption_binding_path=str(controls["consumption_binding"]),
            claim_path=str(claim), receipt_path=str(receipt), bundle_path=str(bundle),
            artifact_root=str(package), calculated_at=calculated_at, calculated_at_source=source)
        selection = None
        if "selection_provenance" in controls:
            selection = mode_c._read(controls["selection_provenance"])
            mode_c.validate_selection_provenance(selection, inputs.request)
        projector = facts["projector_version"] or mode_c.CURRENT_PROJECTOR_VERSION
        expected = mode_c._expected_outputs(inputs, projector, selection, version or mode_c.PREFERRED_RESULT_SCHEMA_VERSION)
        if version:
            mode_c._read_verified_outputs(package, version, *expected)
        return facts | dict(state="EXISTING_VERIFIED" if version else "REPLAYABLE", reason_code="verified_retained_package")
    except _InspectionFailure as exc:
        return facts | dict(state=exc.state, reason_code=exc.reason)
    except ProjectionError as exc:
        code = exc.code.split(":", 1)[0]
        state = "REPLAY_UNAVAILABLE_MISSING_ARTIFACT" if code in {"artifact_not_found", "artifact_root_missing"} else "REPLAY_UNAVAILABLE_INTEGRITY_FAILED"
        if code in {"unsupported_request_schema_version", "missing_evidence_contract_schema"}:
            state = "REPLAY_UNAVAILABLE_UNSUPPORTED_VERSION"
        return facts | dict(state=state, reason_code=code)
    except mode_c.ModeCError as exc:
        state = "REPLAY_UNAVAILABLE_MISSING_ARTIFACT" if exc.code == "mode_c_required_execution_artifact_missing" else "REPLAY_UNAVAILABLE_INTEGRITY_FAILED"
        return facts | dict(state=state, reason_code=exc.code)
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return facts | dict(state="REPLAY_UNAVAILABLE_INTEGRITY_FAILED", reason_code="retained_package_invalid")
