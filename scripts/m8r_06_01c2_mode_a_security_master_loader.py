"""Governed Mode A selection and loading of the accepted C1B compact index."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jsonschema

from scripts.m8r_06_01c1b_compact_runtime_identity_index import (
    CompactArtifactValidationError,
    build_lookup_from_compact_index,
    compute_coverage,
    load_and_validate_compact_artifacts,
    sha256_file,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
POINTER_SCHEMA_VERSION = "m8r_06_mode_a_security_master_pointer.v1"
POINTER_PATH = REPO_ROOT / "config" / "m8r_06_mode_a_security_master_pointer.json"
POINTER_SCHEMA_PATH = (
    REPO_ROOT
    / "docs"
    / "contracts"
    / "schemas"
    / "m8r_06_mode_a_security_master_pointer.v1.schema.json"
)
IMMUTABLE_SEAL_RELATIVE_PATH = Path(
    "docs/reviews/m8r06-01c1b-runtime-index-manifest/immutable_manifest.json"
)


class ModeASecurityMasterUnavailable(FileNotFoundError):
    """Expected production availability/integrity failure with a private code."""

    def __init__(self, reason_code: str):
        self.reason_code = reason_code
        super().__init__("canonical_dependency_missing: security_master_snapshot")


@dataclass(frozen=True)
class ValidatedModeASecurityMaster:
    pointer: dict[str, Any]
    immutable_seal: dict[str, Any]
    index: dict[str, Any]
    manifest: dict[str, Any]
    lookup: dict[str, Any]
    validation: dict[str, Any]


def _fail(code: str) -> None:
    raise ModeASecurityMasterUnavailable(code)


def _load_dict(path: Path, *, missing_code: str, invalid_code: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        _fail(missing_code)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        _fail(invalid_code)
    if not isinstance(value, dict):
        _fail(invalid_code)
    return value


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _resolve_governed_path(
    value: Any,
    *,
    repo_root: Path,
    allowed_root: Path,
    invalid_code: str,
) -> Path:
    if not isinstance(value, str) or not value:
        _fail(invalid_code)
    relative = Path(value)
    if relative.is_absolute() or relative.anchor or relative.drive or ".." in relative.parts:
        _fail(invalid_code)
    resolved_repo = repo_root.resolve()
    resolved_allowed = allowed_root.resolve()
    resolved = (resolved_repo / relative).resolve()
    if not _is_relative_to(resolved, resolved_repo) or not _is_relative_to(
        resolved, resolved_allowed
    ):
        _fail(invalid_code)
    return resolved


def _validate_pointer(pointer: dict[str, Any]) -> None:
    if pointer.get("schema_version") != POINTER_SCHEMA_VERSION:
        _fail("unsupported_pointer_schema_version")
    schema = _load_dict(
        POINTER_SCHEMA_PATH,
        missing_code="pointer_schema_missing",
        invalid_code="pointer_schema_malformed",
    )
    try:
        jsonschema.Draft202012Validator(schema).validate(pointer)
    except (jsonschema.SchemaError, jsonschema.ValidationError):
        _fail("pointer_schema_invalid")


def _validate_pointer_seal_binding(
    pointer: dict[str, Any], seal: dict[str, Any]
) -> None:
    if seal.get("schema_version") != "m8r_06_01c1b_immutable_candidate_seal.v1":
        _fail("immutable_seal_schema_invalid")
    bindings = {
        "source_bundle_id": "source_bundle_id",
        "source_snapshot_id": "source_snapshot_id",
        "source_snapshot_sha256": "source_snapshot_sha256",
        "source_skill_contract_hash": "source_skill_contract_hash",
        "compact_index_sha256": "compact_index_sha256",
        "compact_manifest_sha256": "compact_manifest_sha256",
        "compact_index_schema_sha256": "compact_index_schema_sha256",
        "compact_manifest_schema_sha256": "compact_manifest_schema_sha256",
        "record_count": "record_count",
        "knowledge_universe_count": "knowledge_universe_count",
        "runtime_eligible_count": "runtime_eligible_count",
        "quarantined_count": "quarantined_count",
        "artifact_persisted_in_git": "artifact_persisted_in_git",
    }
    for pointer_field, seal_field in bindings.items():
        if pointer.get(pointer_field) != seal.get(seal_field):
            _fail(f"pointer_seal_{pointer_field}_mismatch")
    if pointer.get("index_id") != seal.get("compact_index_id"):
        _fail("pointer_seal_index_id_mismatch")
    if seal.get("reproduction_semantics") != "REQUIRES_ORIGINAL_SEALED_01B_BUNDLE":
        _fail("immutable_seal_reproduction_semantics_mismatch")
    if seal.get("fresh_reprobe_equivalence") is not False:
        _fail("immutable_seal_fresh_reprobe_policy_mismatch")


def load_mode_a_security_master(
    pointer_path: Path | str = POINTER_PATH,
    *,
    repo_root: Path | str | None = None,
) -> ValidatedModeASecurityMaster:
    """Load the pointer-selected compact index or fail closed without fallback."""
    root = Path(repo_root).resolve() if repo_root is not None else REPO_ROOT.resolve()
    pointer_file = Path(pointer_path)
    pointer = _load_dict(
        pointer_file,
        missing_code="pointer_missing",
        invalid_code="pointer_malformed",
    )
    _validate_pointer(pointer)

    runtime_root = root / "data" / "security_master" / "runtime_identity_indexes"
    index_path = _resolve_governed_path(
        pointer["index_path"],
        repo_root=root,
        allowed_root=runtime_root,
        invalid_code="index_path_not_authorized",
    )
    manifest_path = _resolve_governed_path(
        pointer["manifest_path"],
        repo_root=root,
        allowed_root=runtime_root,
        invalid_code="manifest_path_not_authorized",
    )
    seal_path = _resolve_governed_path(
        pointer["immutable_seal_path"],
        repo_root=root,
        allowed_root=root / "docs" / "reviews",
        invalid_code="immutable_seal_path_not_authorized",
    )

    expected_index = Path(
        f"data/security_master/runtime_identity_indexes/{pointer['index_id']}/index.json"
    )
    expected_manifest = expected_index.with_name("manifest.json")
    if Path(pointer["index_path"]) != expected_index:
        _fail("pointer_index_path_mismatch")
    if Path(pointer["manifest_path"]) != expected_manifest:
        _fail("pointer_manifest_path_mismatch")
    if Path(pointer["immutable_seal_path"]) != IMMUTABLE_SEAL_RELATIVE_PATH:
        _fail("pointer_immutable_seal_path_mismatch")

    seal = _load_dict(
        seal_path,
        missing_code="immutable_seal_missing",
        invalid_code="immutable_seal_malformed",
    )
    _validate_pointer_seal_binding(pointer, seal)

    if not index_path.is_file():
        _fail("candidate_index_missing")
    if not manifest_path.is_file():
        _fail("candidate_manifest_missing")
    if sha256_file(index_path) != pointer["compact_index_sha256"]:
        _fail("pointer_index_sha256_mismatch")
    if sha256_file(manifest_path) != pointer["compact_manifest_sha256"]:
        _fail("pointer_manifest_sha256_mismatch")

    lineage = {
        "source_bundle_id": pointer["source_bundle_id"],
        "source_snapshot_id": pointer["source_snapshot_id"],
        "source_snapshot_artifact": "dryrun_snapshot.json",
        "source_snapshot_sha256": pointer["source_snapshot_sha256"],
        "source_skill_contract_hash": pointer["source_skill_contract_hash"],
    }
    validation_started = time.perf_counter()
    try:
        index, manifest = load_and_validate_compact_artifacts(
            index_path,
            manifest_path,
            expected_lineage=lineage,
        )
    except CompactArtifactValidationError as exc:
        _fail(f"compact_candidate_invalid:{exc}")
    strict_validation_seconds = time.perf_counter() - validation_started

    manifest_bindings = {
        "index_id": "index_id",
        "source_bundle_id": "source_bundle_id",
        "source_snapshot_id": "source_snapshot_id",
        "source_snapshot_sha256": "source_snapshot_sha256",
        "source_skill_contract_hash": "source_skill_contract_hash",
        "compact_index_sha256": "compact_index_sha256",
        "compact_index_schema_sha256": "compact_index_schema_sha256",
        "compact_manifest_schema_sha256": "compact_manifest_schema_sha256",
        "record_count": "record_count",
    }
    for pointer_field, manifest_field in manifest_bindings.items():
        if pointer.get(pointer_field) != manifest.get(manifest_field):
            _fail(f"pointer_manifest_{pointer_field}_mismatch")

    coverage = compute_coverage(index)
    if manifest.get("coverage") != coverage:
        _fail("manifest_coverage_mismatch")
    for field in (
        "knowledge_universe_count",
        "runtime_eligible_count",
        "quarantined_count",
    ):
        if pointer.get(field) != coverage[field]:
            _fail(f"pointer_coverage_{field}_mismatch")
    if any(
        (record.get("observation") or {}).get("status") == "fixture_observation_only"
        for record in index.get("records") or []
    ):
        _fail("fixture_compact_candidate_rejected_in_production")

    lookup_started = time.perf_counter()
    lookup = build_lookup_from_compact_index(index)
    lookup_build_seconds = time.perf_counter() - lookup_started
    return ValidatedModeASecurityMaster(
        pointer=pointer,
        immutable_seal=seal,
        index=index,
        manifest=manifest,
        lookup=lookup,
        validation={
            "valid": True,
            "selection_id": pointer["selection_id"],
            "strict_validation_seconds": strict_validation_seconds,
            "lookup_build_seconds": lookup_build_seconds,
        },
    )
