"""Offline deterministic Result-level composition for representative TPEx H1 evidence."""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, Draft7Validator, FormatChecker

from .errors import ProjectionError
from .phase_h_semantics import STATUS_TYPES, validate_trading_status_context_semantics

ROOT = Path(__file__).resolve().parents[2]
COMPOSITE_SCHEMA_PATH = ROOT / "schemas" / "trading_status_context_composite.v1.schema.json"
COMPONENT_ORDER = (
    ("H1-TPEX-ATTENTION-OPENAPI", "tpex_trading_warning_information", "attention"),
    ("H1-TPEX-DISPOSITION-OPENAPI", "tpex_disposal_information", "disposition"),
    ("H1-TPEX-CHANGED-TRADING-OPENAPI", "tpex_cmode", "cmode"),
)
# This is the composite's fixed source-authority boundary. Do not derive it
# from mutable routing, activation, or executor-registry state.
SOURCE_AUTHORITY = {
    "H1-TPEX-ATTENTION-OPENAPI": {
        "source_family": "TPEX_ATTENTION_OPEN_DATA",
        "source_contract_id": "tpex_trading_warning_information",
        "allowed_canonical_coverage": frozenset({"attention"}),
    },
    "H1-TPEX-DISPOSITION-OPENAPI": {
        "source_family": "TPEX_DISPOSITION_OPEN_DATA",
        "source_contract_id": "tpex_disposal_information",
        "allowed_canonical_coverage": frozenset({"disposition"}),
    },
    "H1-TPEX-CHANGED-TRADING-OPENAPI": {
        "source_family": "TPEX_CHANGED_TRADING_OPEN_DATA",
        "source_contract_id": "tpex_cmode",
        "allowed_canonical_coverage": frozenset(),
    },
}
_COMPONENT_ID = re.compile(r"^h1c-v1-[0-9a-f]{24}$")
_RELATIVE_PATH = re.compile(r"^(?!.*(?:^|/)\.{1,2}(?:/|$))[A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)*$")
_NATIVE_GUARD = "Source-native unresolved evidence is not a canonical trading-status conclusion."


def _canonical_hash(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _component_id(target: Mapping[str, str], source_id: str, source_contract_id: str, schema_version: str, artifact_sha256: str) -> str:
    digest = _canonical_hash({
        "composition_schema_version": "trading_status_context_composite.v1",
        "canonical_target_id": target["canonical_target_id"],
        "market": target["market"],
        "security_code": target["security_code"],
        "source_id": source_id,
        "source_contract_id": source_contract_id,
        "evidence_schema_version": schema_version,
        "artifact_sha256": artifact_sha256,
    })
    return f"h1c-v1-{digest[:24]}"


def _validate_h1(evidence: Mapping[str, Any]) -> None:
    version = evidence.get("schema_version")
    if version not in {"trading_status_context_evidence.v1", "trading_status_context_evidence.v2"}:
        raise ProjectionError("composite_h1_schema_unsupported")
    schema_path = ROOT / "schemas" / f"{version}.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = list(Draft7Validator(schema, format_checker=FormatChecker()).iter_errors(evidence))
    if errors:
        raise ProjectionError("composite_h1_schema_invalid")
    try:
        validate_trading_status_context_semantics(evidence)
    except (TypeError, ValueError) as exc:
        raise ProjectionError("composite_h1_semantics_invalid") from exc


def _validate_component_shape(
    component: Mapping[str, Any], target: Mapping[str, str], expected: tuple[str, str, str],
) -> None:
    if set(component) != {
        "component_id", "source_id", "source_contract_id", "evidence_schema_version",
        "component_status", "artifact_reference", "evidence",
    }:
        raise ProjectionError("composite_component_shape_invalid")
    source_id, source_contract_id, _ = expected
    authority = SOURCE_AUTHORITY[source_id]
    if source_contract_id != authority["source_contract_id"]:
        raise ProjectionError("composite_component_source_identity_mismatch")
    if component.get("source_id") != source_id or component.get("source_contract_id") != source_contract_id:
        raise ProjectionError("composite_component_source_identity_mismatch")
    evidence = component.get("evidence")
    reference = component.get("artifact_reference")
    if not isinstance(evidence, Mapping) or not isinstance(reference, Mapping):
        raise ProjectionError("composite_component_evidence_missing")
    _validate_h1(evidence)
    if evidence.get("target") != dict(target):
        raise ProjectionError("composite_component_target_mismatch")
    source = evidence.get("source")
    if (not isinstance(source, Mapping)
            or source.get("source_family") != authority["source_family"]
            or source.get("source_contract_id") != authority["source_contract_id"]):
        raise ProjectionError("composite_component_source_identity_mismatch")
    covered = set(evidence["coverage"].get("covered_status_types", []))
    if not covered.issubset(authority["allowed_canonical_coverage"]):
        raise ProjectionError("composite_component_source_coverage_mismatch")
    version = evidence.get("schema_version")
    if component.get("evidence_schema_version") != version or component.get("component_status") != evidence.get("status"):
        raise ProjectionError("composite_component_contract_mismatch")
    path = reference.get("relative_path")
    digest = reference.get("sha256")
    if not isinstance(path, str) or not _RELATIVE_PATH.fullmatch(path) or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ProjectionError("composite_component_reference_invalid")
    expected_id = _component_id(target, source_id, source_contract_id, version, digest)
    if component.get("component_id") != expected_id:
        raise ProjectionError("composite_component_identity_mismatch")


def build_component_record(
    target: Mapping[str, str], source_id: str, evidence: Mapping[str, Any], artifact_reference: Mapping[str, str],
) -> dict[str, Any]:
    """Create the deterministic source component envelope for a validated H1 artifact."""
    expected = next((row for row in COMPONENT_ORDER if row[0] == source_id), None)
    if expected is None:
        raise ProjectionError("composite_component_source_unapproved")
    authority = SOURCE_AUTHORITY[source_id]
    source_contract_id = authority["source_contract_id"]
    version = evidence.get("schema_version")
    digest = artifact_reference.get("sha256")
    component = {
        "component_id": _component_id(target, source_id, source_contract_id, version, digest),
        "source_id": source_id,
        "source_contract_id": source_contract_id,
        "evidence_schema_version": version,
        "component_status": evidence.get("status"),
        "artifact_reference": dict(artifact_reference),
        "evidence": dict(evidence),
    }
    _validate_component_shape(component, target, expected)
    return component


def _usable(component: Mapping[str, Any]) -> bool:
    evidence = component["evidence"]
    coverage = evidence["coverage"]
    return (
        evidence.get("status") in {"available", "partial", "no_evidence_in_covered_scope"}
        and coverage.get("retrieval_succeeded") is True
        and coverage.get("source_contract_validated") is True
        and coverage.get("exact_target_search_succeeded") is True
    )


def _aggregate_status(components: Sequence[Mapping[str, Any]], covered: set[str]) -> str:
    if not any(_usable(component) for component in components):
        statuses = {component["component_status"] for component in components}
        if "binding_failed" in statuses:
            return "binding_failed"
        if "source_failed" in statuses:
            return "source_failed"
        if "unsupported" in statuses:
            return "unsupported"
        if statuses == {"not_applicable"}:
            return "not_applicable"
        return "unsupported"
    if covered == STATUS_TYPES and all(
        component["component_status"] in {"available", "no_evidence_in_covered_scope"}
        for component in components
    ):
        return "available"
    return "partial"


def compose_trading_status_context(
    target: Mapping[str, str],
    components: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Compose exactly the predeclared attention/disposition/cmode H1 component set.

    `components` are ordered mappings containing source_id, source_contract_id,
    evidence_schema_version, component_status, artifact_reference and complete
    schema-valid evidence. The artifact loader/lineage layer remains responsible
    for matching each reference hash to the persisted artifact bytes.
    """
    if not isinstance(target, Mapping) or set(target) != {"canonical_target_id", "market", "security_code"}:
        raise ProjectionError("composite_target_invalid")
    if target.get("market") != "TPEX" or any(not isinstance(target.get(k), str) or not target[k] for k in target):
        raise ProjectionError("composite_target_invalid")
    if target["canonical_target_id"] != f"TPEX:{target['security_code']}":
        raise ProjectionError("composite_target_identity_mismatch")
    if not isinstance(components, Sequence) or isinstance(components, (str, bytes)) or len(components) != len(COMPONENT_ORDER):
        raise ProjectionError("composite_component_set_invalid")

    built: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_sources: set[str] = set()
    seen_refs: set[tuple[str, str]] = set()
    for item, expected in zip(components, COMPONENT_ORDER, strict=True):
        if not isinstance(item, Mapping):
            raise ProjectionError("composite_component_invalid")
        source_id, source_contract_id, _ = expected
        reference = item.get("artifact_reference")
        evidence = item.get("evidence")
        if not isinstance(reference, Mapping) or not isinstance(evidence, Mapping):
            raise ProjectionError("composite_component_evidence_missing")
        _validate_component_shape(item, target, expected)
        source_key = item["source_contract_id"]
        ref_key = (reference["relative_path"], reference["sha256"])
        component_id = item["component_id"]
        if component_id in seen_ids or source_key in seen_sources or ref_key in seen_refs:
            raise ProjectionError("composite_duplicate_component_or_artifact")
        seen_ids.add(component_id)
        seen_sources.add(source_key)
        seen_refs.add(ref_key)
        if source_id == "H1-TPEX-CHANGED-TRADING-OPENAPI":
            native_only = evidence.get("status") == "partial" and not evidence.get("items") and bool(evidence.get("native_observations"))
            failed_without_payload = evidence.get("status") in {"source_failed", "binding_failed", "unsupported", "not_applicable"} and not evidence.get("items") and not evidence.get("native_observations")
            if not (native_only or failed_without_payload):
                raise ProjectionError("composite_cmode_native_only_contract_invalid")
        else:
            allowed_type = expected[2]
            if any(item.get("status_type") != allowed_type for item in evidence.get("items", [])):
                raise ProjectionError("composite_component_canonical_type_invalid")
        built.append({
            "component_id": component_id,
            "source_id": source_id,
            "source_contract_id": source_contract_id,
            "evidence_schema_version": evidence["schema_version"],
            "component_status": evidence["status"],
            "artifact_reference": dict(reference),
            "evidence": dict(evidence),
        })

    covered: set[str] = set()
    canonical_item_count = 0
    native_observation_count = 0
    citation_ids: set[str] = set()
    caveats: set[str] = set()
    for component in built:
        evidence = component["evidence"]
        if _usable(component):
            # _validate_component_shape has already constrained source identity
            # and subtype authority before any coverage enters the aggregate.
            covered.update(evidence["coverage"].get("covered_status_types", []))
        canonical_item_count += len(evidence.get("items", []))
        native_observation_count += int(evidence.get("native_observation_count", len(evidence.get("native_observations", []))))
        citation_ids.update(evidence.get("citation_ids", []))
        caveats.update(evidence.get("caveats", []))
        if evidence.get("native_observations"):
            caveats.add(_NATIVE_GUARD)

    uncovered = STATUS_TYPES - covered
    complete = not uncovered
    return {
        "schema_version": "trading_status_context_composite.v1",
        "status": _aggregate_status(built, covered),
        "target": dict(target),
        "components": built,
        "aggregate_coverage": {
            "status": "complete" if complete else "partial",
            "declared_scope_complete": complete,
            "declared_status_types": sorted(STATUS_TYPES),
            "covered_status_types": sorted(covered),
            "uncovered_status_types": sorted(uncovered),
        },
        "canonical_item_count": canonical_item_count,
        "native_observation_count": native_observation_count,
        "component_count": len(built),
        "caveats": sorted(caveats),
        "citation_ids": sorted(citation_ids),
    }


def validate_trading_status_context_composite(value: Mapping[str, Any]) -> None:
    if not isinstance(value, Mapping):
        raise ProjectionError("composite_invalid")
    schema = json.loads(COMPOSITE_SCHEMA_PATH.read_text(encoding="utf-8"))
    if list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value)):
        raise ProjectionError("composite_schema_invalid")
    target = value["target"]
    components = value["components"]
    expected_ids = [item[0] for item in COMPONENT_ORDER]
    if [item.get("source_id") for item in components] != expected_ids:
        raise ProjectionError("composite_component_order_or_set_invalid")
    rebuilt = compose_trading_status_context(target, components)
    if rebuilt != dict(value):
        raise ProjectionError("composite_aggregate_mismatch")


def validate_component_artifact_bindings(
    composite: Mapping[str, Any],
    artifacts_by_path: Mapping[str, Mapping[str, Any]],
    inventory_by_path: Mapping[str, Mapping[str, Any]],
) -> None:
    """Bind embedded component evidence to the exact verified bundle artifacts."""
    validate_trading_status_context_composite(composite)
    expected_paths: set[str] = set()
    for component in composite["components"]:
        reference = component["artifact_reference"]
        path = reference["relative_path"]
        obj = artifacts_by_path.get(path)
        inventory = inventory_by_path.get(path)
        if path in expected_paths or not isinstance(obj, Mapping) or not isinstance(inventory, Mapping):
            raise ProjectionError("composite_component_reference_missing_or_duplicate")
        if (dict(obj) != component["evidence"]
                or reference["sha256"] != inventory.get("sha256")
                or component["evidence_schema_version"] != inventory.get("schema_version")
                or component["evidence_schema_version"] != inventory.get("evidence_contract")
                or inventory.get("artifact_role") != "component_evidence"
                or inventory.get("item_count") != len(obj.get("items", []))):
            raise ProjectionError("composite_component_reference_mismatch")
        expected_paths.add(path)
