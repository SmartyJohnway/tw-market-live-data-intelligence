"""Bounded internal migration lifecycle layered on frozen A4/A5 authority.

Migration inputs are verified A4 packages classified by A5. A5 restore semantics
are not changed. The production registry intentionally has no executable path:
the only current migration ID lacks an authoritative source/target transform.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Mapping, Sequence

from server.services import unified_backup as backup
from server.services import unified_restore as restore

PLAN_SCHEMA = "tw_market_migration_plan.v1"
MIGRATION_RECEIPT = "migration-receipt.json"
MIGRATION_RECEIPT_SCHEMA = "tw_market_migration_receipt.v1"
ROLLBACK_RECEIPT = "rollback-receipt.json"
ROLLBACK_RECEIPT_SCHEMA = "tw_market_rollback_receipt.v1"
MIGRATION_SOURCE_SCOPE = "EXPLICIT_DECLARED_MEMBERS_ONLY"
CHECKPOINT_KIND = "SOURCE_A4_BACKUP"
WATCHLIST_V0_TO_V1 = "watchlist-schema-v0-to-v1"
_HASH = re.compile(r"^[0-9a-f]{64}$")
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class MigrationError(RuntimeError):
    """Typed fail-closed migration lifecycle outcome."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class MigrationDefinition:
    migration_id: str
    state_family: str
    source_version: str
    target_version: str
    implementation_status: str
    authority: str
    required_member_ids: tuple[str, ...] = ()
    transformer: Callable[[Mapping[str, bytes]], Mapping[str, bytes]] | None = None

    def authority_record(self) -> dict[str, str]:
        return {"migration_id": self.migration_id, "state_family": self.state_family,
                "source_version": self.source_version, "target_version": self.target_version,
                "implementation_status": self.implementation_status, "authority": self.authority,
                "required_member_ids": ",".join(sorted(self.required_member_ids))}


# A5 classifies the path but no v0 schema, historical fixture, or transformation
# contract exists. Keep it discoverable and explicitly non-executable.
MIGRATION_REGISTRY: tuple[MigrationDefinition, ...] = (
    MigrationDefinition(WATCHLIST_V0_TO_V1,
                        "persistent_watchlists_and_revision_database", "0", "1",
                        "KNOWN_NOT_IMPLEMENTED",
                        "A5 classification identifier only; no authoritative v0 schema or transform"),
)


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _require_utc(value: str) -> None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError) as exc:
        raise MigrationError("MIGRATION_PLAN_INVALID") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise MigrationError("MIGRATION_PLAN_INVALID")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _integrity(payload: Mapping[str, Any], field: str) -> dict[str, str]:
    body = dict(payload)
    body.pop(field, None)
    return {"algorithm": "SHA-256", "coverage": f"canonical UTF-8 JSON excluding {field}",
            "sha256": _digest(body)}


def _registry_rows(registry: Sequence[MigrationDefinition]) -> list[dict[str, str]]:
    return [item.authority_record() for item in sorted(registry, key=lambda row: row.migration_id)]


def _attestation_hash(attestation: restore.CompatibilityAttestation) -> str:
    return _digest({"backup_manifest_sha256": attestation.backup_manifest_sha256,
                    "state_family_versions": dict(sorted(attestation.state_family_versions.items()))})


def _manifest(backup_path: Path, *, max_total_bytes: int) -> tuple[dict[str, Any], str]:
    try:
        verified = backup.verify_backup(backup_path, max_total_bytes=max_total_bytes)
        path = Path(backup_path).resolve(strict=True) / backup.MANIFEST_NAME
        manifest = json.loads(path.read_text(encoding="utf-8"),
                              object_pairs_hook=backup._strict_object)
    except backup.BackupError as exc:
        if exc.code == "BACKUP_RESOURCE_LIMIT_EXCEEDED":
            raise MigrationError("MIGRATION_RESOURCE_LIMIT_EXCEEDED") from exc
        raise MigrationError("MIGRATION_SOURCE_UNVERIFIED") from exc
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise MigrationError("MIGRATION_SOURCE_UNVERIFIED") from exc
    digest = verified.get("manifest_sha256")
    if not isinstance(digest, str) or not _HASH.fullmatch(digest):
        raise MigrationError("MIGRATION_SOURCE_UNVERIFIED")
    return manifest, digest


def _ensure_source_location(backup_path: Path, forbidden_roots: Sequence[Path]) -> Path:
    if not isinstance(forbidden_roots, Sequence) or isinstance(forbidden_roots, (str, bytes)):
        raise MigrationError("MIGRATION_SOURCE_UNVERIFIED")
    try:
        package = Path(backup_path).resolve(strict=True)
        repo = Path(__file__).resolve().parents[2]
        protected = [repo, *(Path(item).resolve(strict=True) for item in forbidden_roots)]
        if any(package == root or package in root.parents or root in package.parents for root in protected):
            raise MigrationError("MIGRATION_SOURCE_UNVERIFIED")
        return package
    except MigrationError:
        raise
    except (OSError, RuntimeError, ValueError) as exc:
        raise MigrationError("MIGRATION_SOURCE_UNVERIFIED") from exc


def _inventory(root: Path, *, include_receipts: bool = False) -> dict[str, tuple[int, str]]:
    result: dict[str, tuple[int, str]] = {}
    for item in root.rglob("*"):
        if backup._is_reparse_or_symlink(item):
            raise MigrationError("MIGRATION_TARGET_UNSAFE")
        if item.is_file():
            relative = item.relative_to(root).as_posix()
            if not include_receipts and relative in {MIGRATION_RECEIPT, ROLLBACK_RECEIPT}:
                continue
            size, digest = backup._hash_file(item)
            result[relative] = (size, digest)
    return result


def _inventory_sha(inventory: Mapping[str, tuple[int, str]]) -> str:
    return _digest({key: {"size_bytes": value[0], "sha256": value[1]}
                    for key, value in sorted(inventory.items())})


def _has_exact_directories(root: Path, member_paths: Sequence[str], *, receipt_name: str) -> bool:
    expected: set[str] = set()
    for name in [*member_paths, receipt_name]:
        parent = PurePosixPath(name).parent
        while parent.as_posix() not in {".", ""}:
            expected.add(parent.as_posix())
            parent = parent.parent
    actual: set[str] = set()
    folded: set[str] = set()
    for path in root.rglob("*"):
        if backup._is_reparse_or_symlink(path):
            raise MigrationError("MIGRATION_TARGET_UNSAFE")
        relative = path.relative_to(root).as_posix()
        if relative.casefold() in folded:
            raise MigrationError("MIGRATION_TARGET_UNSAFE")
        folded.add(relative.casefold())
        if path.is_dir():
            actual.add(relative)
    return actual == expected


def _safe_root(root: Path, *, backup_path: Path, forbidden_roots: Sequence[Path]) -> Path:
    candidate = Path(root)
    try:
        backup._reject_reparse_components(candidate)
        resolved = candidate.resolve(strict=True)
        if not resolved.is_dir():
            raise MigrationError("MIGRATION_SOURCE_UNVERIFIED")
        repo = Path(__file__).resolve().parents[2]
        protected = [repo, Path(backup_path).resolve(strict=True),
                     *(Path(path).resolve(strict=True) for path in forbidden_roots)]
        if any(resolved == item or resolved in item.parents or item in resolved.parents for item in protected):
            raise MigrationError("MIGRATION_TARGET_UNSAFE")
        return resolved
    except MigrationError:
        raise
    except (OSError, RuntimeError, ValueError) as exc:
        raise MigrationError("MIGRATION_SOURCE_UNVERIFIED") from exc


def _derive(*, backup_path: Path, compatibility: restore.CompatibilityAttestation,
            contract: restore.RestoreCompatibilityContract,
            max_total_bytes: int, max_member_count: int,
            forbidden_roots: Sequence[Path] = (),
            registry: Sequence[MigrationDefinition] = MIGRATION_REGISTRY) -> dict[str, Any]:
    if (not isinstance(max_total_bytes, int) or isinstance(max_total_bytes, bool) or max_total_bytes <= 0
            or not isinstance(max_member_count, int) or isinstance(max_member_count, bool) or max_member_count <= 0):
        raise MigrationError("MIGRATION_RESOURCE_LIMIT_EXCEEDED")
    _ensure_source_location(backup_path, forbidden_roots)
    manifest, manifest_sha = _manifest(backup_path, max_total_bytes=max_total_bytes)
    if len(manifest.get("members", [])) > max_member_count:
        raise MigrationError("MIGRATION_RESOURCE_LIMIT_EXCEEDED")
    if (not isinstance(compatibility, restore.CompatibilityAttestation)
            or compatibility.backup_manifest_sha256 != manifest_sha):
        raise MigrationError("MIGRATION_SOURCE_UNVERIFIED")
    try:
        inspected = restore.inspect_restore(
            backup_path=backup_path, compatibility=compatibility, contract=contract,
            max_total_bytes=max_total_bytes, max_member_count=max_member_count)
    except restore.RestoreError as exc:
        raise MigrationError("MIGRATION_SOURCE_UNVERIFIED") from exc
    status = inspected.get("status")
    if status == "DIRECT_RESTORE_COMPATIBLE":
        return {"status": "MIGRATION_NOT_REQUIRED", "migration_paths": [],
                "manifest": manifest, "manifest_sha256": manifest_sha,
                "inspection": inspected}
    if status != "MIGRATION_REQUIRED":
        raise MigrationError(status if isinstance(status, str) else "MIGRATION_SOURCE_UNVERIFIED")
    if manifest.get("selection_scope") != backup.SELECTION_SCOPE:
        raise MigrationError("RESTORE_SCOPE_INCOMPLETE_FOR_REQUEST")
    path_ids = inspected.get("migration_paths")
    known = {item.migration_id for item in registry}
    if not isinstance(path_ids, list) or not path_ids or any(item not in known for item in path_ids):
        raise MigrationError("MIGRATION_PATH_NOT_IMPLEMENTED")
    member_family_versions = {
        (row.get("artifact_family"), compatibility.state_family_versions.get(row.get("logical_member_id")))
        for row in manifest.get("members", [])
    }
    for migration_id in path_ids:
        definition = next(item for item in registry if item.migration_id == migration_id)
        if ((definition.state_family, definition.source_version) not in member_family_versions
                or definition.target_version not in contract.supported_state_family_versions.get(definition.state_family, ())):
            raise MigrationError("MIGRATION_PATH_NOT_IMPLEMENTED")
        present_ids = {row.get("logical_member_id") for row in manifest.get("members", [])}
        if definition.implementation_status == "IMPLEMENTED" and not definition.required_member_ids:
            raise MigrationError("MIGRATION_CHECKPOINT_INCOMPLETE")
        if not set(definition.required_member_ids) <= present_ids:
            raise MigrationError("MIGRATION_CHECKPOINT_INCOMPLETE")
    total = manifest.get("total_size_bytes")
    if not isinstance(total, int) or total > max_total_bytes:
        raise MigrationError("MIGRATION_RESOURCE_LIMIT_EXCEEDED")
    return {"status": "MIGRATION_PATH_NOT_IMPLEMENTED" if any(
                next(row for row in registry if row.migration_id == item).implementation_status != "IMPLEMENTED"
                for item in path_ids) else "MIGRATION_PATH_AVAILABLE",
            "migration_paths": sorted(path_ids), "manifest": manifest,
            "manifest_sha256": manifest_sha, "inspection": inspected,
            "total_size_bytes": total, "member_count": len(manifest["members"]),
            "registry_sha256": _digest(_registry_rows(registry)),
            "attestation_sha256": _attestation_hash(compatibility)}


def inspect_migration(*, backup_path: Path,
                      compatibility: restore.CompatibilityAttestation,
                      contract: restore.RestoreCompatibilityContract = restore.DEFAULT_COMPATIBILITY_CONTRACT,
                      max_total_bytes: int, max_member_count: int,
                      forbidden_roots: Sequence[Path]) -> dict[str, Any]:
    """Reverify A4 and rederive A5 compatibility; no receipt or filesystem writes."""
    facts = _derive(backup_path=backup_path, compatibility=compatibility, contract=contract,
                    max_total_bytes=max_total_bytes, max_member_count=max_member_count,
                    forbidden_roots=forbidden_roots)
    if facts["status"] == "MIGRATION_NOT_REQUIRED":
        return {"status": facts["status"], "migration_ids": []}
    return {"status": facts["status"], "migration_ids": facts["migration_paths"],
            "source_backup_id": facts["manifest"]["backup_id"],
            "source_backup_manifest_sha256": facts["manifest_sha256"],
            "source_state_identity": facts["manifest"]["source_state_identity"],
            "source_selection_scope": facts["manifest"]["selection_scope"],
            "backup_tier": facts["manifest"]["backup_tier"],
            "compatibility_contract_version": facts["inspection"]["target_contract_version"],
            "compatibility_contract_sha256": facts["inspection"]["target_contract_sha256"],
            "compatibility_attestation_sha256": facts["attestation_sha256"],
            "source_versions": facts["inspection"]["source_state_family_versions"],
            "target_versions": facts["inspection"]["target_supported_state_family_versions"],
            "registry_sha256": facts["registry_sha256"],
            "member_count": facts["member_count"],
            "total_size_bytes": facts["total_size_bytes"]}


@dataclass(frozen=True)
class MigrationPlan:
    """Immutable plan envelope; canonical JSON is available through ``to_dict``."""

    plan_schema_version: str
    migration_plan_id: str
    migration_id: str
    source_backup_id: str
    source_backup_manifest_sha256: str
    source_state_identity: str
    source_selection_scope: str
    compatibility_contract_version: str
    compatibility_contract_sha256: str
    compatibility_attestation_sha256: str
    source_versions_json: str
    target_versions_json: str
    affected_members_json: str
    unchanged_members_json: str
    checkpoint_kind: str
    checkpoint_backup_id: str
    checkpoint_manifest_sha256: str
    resource_limits_json: str
    registry_sha256: str
    created_at: str
    plan_integrity_sha256: str

    def to_dict(self) -> dict[str, Any]:
        payload = {"plan_schema_version": self.plan_schema_version,
                   "migration_plan_id": self.migration_plan_id,
                   "migration_id": self.migration_id,
                   "source_backup_id": self.source_backup_id,
                   "source_backup_manifest_sha256": self.source_backup_manifest_sha256,
                   "source_state_identity": self.source_state_identity,
                   "source_selection_scope": self.source_selection_scope,
                   "compatibility_contract_version": self.compatibility_contract_version,
                   "compatibility_contract_sha256": self.compatibility_contract_sha256,
                   "compatibility_attestation_sha256": self.compatibility_attestation_sha256,
                   "source_versions": json.loads(self.source_versions_json),
                   "target_versions": json.loads(self.target_versions_json),
                   "affected_members": json.loads(self.affected_members_json),
                   "unchanged_members": json.loads(self.unchanged_members_json),
                   "checkpoint_kind": self.checkpoint_kind,
                   "checkpoint_backup_id": self.checkpoint_backup_id,
                   "checkpoint_manifest_sha256": self.checkpoint_manifest_sha256,
                   "resource_limits": json.loads(self.resource_limits_json),
                   "registry_sha256": self.registry_sha256,
                   "created_at": self.created_at}
        payload["plan_integrity"] = {"algorithm": "SHA-256",
                                     "coverage": "canonical UTF-8 JSON excluding plan_integrity",
                                     "sha256": self.plan_integrity_sha256}
        return payload


def _plan_from_payload(payload: Mapping[str, Any]) -> MigrationPlan:
    body = dict(payload)
    body.pop("plan_integrity", None)
    integrity = payload.get("plan_integrity")
    if (not isinstance(integrity, Mapping) or integrity.get("algorithm") != "SHA-256"
            or integrity.get("coverage") != "canonical UTF-8 JSON excluding plan_integrity"
            or integrity.get("sha256") != _digest(body)):
        raise MigrationError("MIGRATION_PLAN_INVALID")
    return MigrationPlan(
        PLAN_SCHEMA, body["migration_plan_id"], body["migration_id"],
        body["source_backup_id"], body["source_backup_manifest_sha256"],
        body["source_state_identity"], body["source_selection_scope"],
        body["compatibility_contract_version"], body["compatibility_contract_sha256"],
        body["compatibility_attestation_sha256"], _canonical(body["source_versions"]).decode(),
        _canonical(body["target_versions"]).decode(), _canonical(body["affected_members"]).decode(),
        _canonical(body["unchanged_members"]).decode(), body["checkpoint_kind"],
        body["checkpoint_backup_id"], body["checkpoint_manifest_sha256"],
        _canonical(body["resource_limits"]).decode(), body["registry_sha256"],
        body["created_at"], integrity["sha256"])


def preview_migration(*, backup_path: Path,
                      compatibility: restore.CompatibilityAttestation,
                      contract: restore.RestoreCompatibilityContract = restore.DEFAULT_COMPATIBILITY_CONTRACT,
                      migration_id: str, migration_plan_id: str,
                      created_at: str,
                      max_total_bytes: int, max_member_count: int,
                      max_changed_members: int,
                      forbidden_roots: Sequence[Path],
                      _test_only_registry: Sequence[MigrationDefinition] | None = None) -> MigrationPlan:
    """Build a deterministic read-only plan bound to A4, A5, registry and limits."""
    if not _ID.fullmatch(migration_id) or not _ID.fullmatch(migration_plan_id):
        raise MigrationError("MIGRATION_PLAN_INVALID")
    try:
        parsed = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    except (ValueError, AttributeError) as exc:
        raise MigrationError("MIGRATION_PLAN_INVALID") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise MigrationError("MIGRATION_PLAN_INVALID")
    registry = MIGRATION_REGISTRY if _test_only_registry is None else tuple(_test_only_registry)
    if _test_only_registry is not None and any(
        item.implementation_status != "TEST_ONLY_SYNTHETIC_TRANSFORMER" for item in registry
    ):
        raise MigrationError("MIGRATION_PATH_NOT_IMPLEMENTED")
    facts = _derive(backup_path=backup_path, compatibility=compatibility, contract=contract,
                    max_total_bytes=max_total_bytes, max_member_count=max_member_count,
                    forbidden_roots=forbidden_roots,
                    registry=registry)
    if facts["status"] == "MIGRATION_NOT_REQUIRED":
        raise MigrationError("MIGRATION_NOT_REQUIRED")
    if migration_id not in facts["migration_paths"]:
        raise MigrationError("MIGRATION_PATH_NOT_IMPLEMENTED")
    if not isinstance(max_changed_members, int) or isinstance(max_changed_members, bool) or max_changed_members <= 0:
        raise MigrationError("MIGRATION_RESOURCE_LIMIT_EXCEEDED")
    definition = next((row for row in registry if row.migration_id == migration_id), None)
    if definition is None:
        raise MigrationError("MIGRATION_PATH_NOT_IMPLEMENTED")
    members = facts["manifest"]["members"]
    affected = sorted(row["logical_member_id"] for row in members
                      if row["artifact_family"] == definition.state_family)
    if not affected or len(affected) > max_changed_members:
        raise MigrationError("MIGRATION_RESOURCE_LIMIT_EXCEEDED")
    unchanged = sorted(row["logical_member_id"] for row in members
                       if row["artifact_family"] != definition.state_family)
    payload = {
        "plan_schema_version": PLAN_SCHEMA, "migration_plan_id": migration_plan_id,
        "migration_id": migration_id,
        "source_backup_id": facts["manifest"]["backup_id"],
        "source_backup_manifest_sha256": facts["manifest_sha256"],
        "source_state_identity": facts["manifest"]["source_state_identity"],
        "source_selection_scope": facts["manifest"]["selection_scope"],
        "compatibility_contract_version": facts["inspection"]["target_contract_version"],
        "compatibility_contract_sha256": facts["inspection"]["target_contract_sha256"],
        "compatibility_attestation_sha256": facts["attestation_sha256"],
        "source_versions": facts["inspection"]["source_state_family_versions"],
        "target_versions": facts["inspection"]["target_supported_state_family_versions"],
        "affected_members": affected, "unchanged_members": unchanged,
        "checkpoint_kind": CHECKPOINT_KIND,
        "checkpoint_backup_id": facts["manifest"]["backup_id"],
        "checkpoint_manifest_sha256": facts["manifest_sha256"],
        "resource_limits": {"max_total_bytes": max_total_bytes,
                            "max_member_count": max_member_count,
                            "max_changed_members": max_changed_members},
        "registry_sha256": facts["registry_sha256"], "created_at": created_at,
    }
    payload["plan_integrity"] = {"algorithm": "SHA-256",
                                 "coverage": "canonical UTF-8 JSON excluding plan_integrity",
                                 "sha256": _digest(payload)}
    return _plan_from_payload(payload)


def _validate_plan(plan: MigrationPlan, *, backup_path: Path,
                   compatibility: restore.CompatibilityAttestation,
                   contract: restore.RestoreCompatibilityContract,
                   max_total_bytes: int, max_member_count: int,
                   forbidden_roots: Sequence[Path] = (),
                   registry: Sequence[MigrationDefinition] = MIGRATION_REGISTRY) -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(plan, MigrationPlan):
        raise MigrationError("MIGRATION_PLAN_INVALID")
    payload = plan.to_dict()
    if (plan.plan_schema_version != PLAN_SCHEMA
            or not isinstance(plan.migration_plan_id, str)
            or not _ID.fullmatch(plan.migration_plan_id)
            or not isinstance(plan.migration_id, str)
            or not _ID.fullmatch(plan.migration_id)):
        raise MigrationError("MIGRATION_PLAN_INVALID")
    _require_utc(plan.created_at)
    resource_limits = payload.get("resource_limits")
    if (not isinstance(resource_limits, Mapping)
            or set(resource_limits) != {"max_total_bytes", "max_member_count", "max_changed_members"}):
        raise MigrationError("MIGRATION_PLAN_INVALID")
    body = dict(payload)
    plan_integrity = body.pop("plan_integrity", None)
    if (not isinstance(plan_integrity, Mapping)
            or plan_integrity.get("sha256") != _digest(body)
            or plan_integrity.get("sha256") != plan.plan_integrity_sha256):
        raise MigrationError("MIGRATION_PLAN_INVALID")
    facts = _derive(backup_path=backup_path, compatibility=compatibility, contract=contract,
                    max_total_bytes=max_total_bytes, max_member_count=max_member_count,
                    forbidden_roots=forbidden_roots,
                    registry=registry)
    if plan.migration_id not in facts.get("migration_paths", []):
        raise MigrationError("MIGRATION_PATH_NOT_IMPLEMENTED")
    if (payload["source_backup_id"] != facts["manifest"]["backup_id"]
            or payload["source_backup_manifest_sha256"] != facts["manifest_sha256"]
            or payload["source_state_identity"] != facts["manifest"]["source_state_identity"]
            or payload["source_selection_scope"] != backup.SELECTION_SCOPE
            or payload["compatibility_contract_version"] != facts["inspection"]["target_contract_version"]
            or payload["compatibility_contract_sha256"] != facts["inspection"]["target_contract_sha256"]
            or payload["compatibility_attestation_sha256"] != facts["attestation_sha256"]
            or payload["source_versions"] != facts["inspection"]["source_state_family_versions"]
            or payload["target_versions"] != facts["inspection"]["target_supported_state_family_versions"]
            or payload["registry_sha256"] != facts["registry_sha256"]
            or payload["checkpoint_kind"] != CHECKPOINT_KIND
            or payload["checkpoint_backup_id"] != facts["manifest"]["backup_id"]
            or payload["checkpoint_manifest_sha256"] != facts["manifest_sha256"]
            or payload["resource_limits"].get("max_total_bytes") != max_total_bytes
            or payload["resource_limits"].get("max_member_count") != max_member_count
            or not isinstance(payload["resource_limits"].get("max_changed_members"), int)
            or isinstance(payload["resource_limits"].get("max_changed_members"), bool)
            or payload["resource_limits"]["max_changed_members"] <= 0):
        raise MigrationError("MIGRATION_PLAN_INVALID")
    definition = next((item for item in registry if item.migration_id == plan.migration_id), None)
    if definition is None:
        raise MigrationError("MIGRATION_PATH_NOT_IMPLEMENTED")
    members = facts["manifest"]["members"]
    affected = sorted(row["logical_member_id"] for row in members
                      if row["artifact_family"] == definition.state_family)
    unchanged = sorted(row["logical_member_id"] for row in members
                       if row["artifact_family"] != definition.state_family)
    if payload["affected_members"] != affected or payload["unchanged_members"] != unchanged:
        raise MigrationError("MIGRATION_PLAN_INVALID")
    return facts, payload


def _read_members(package: Path, manifest: Mapping[str, Any], *, max_total_bytes: int) -> dict[str, bytes]:
    values: dict[str, bytes] = {}
    total = 0
    for row in manifest["members"]:
        relative = backup._relative(row["backup_relative_path"])
        output_relative = relative.removeprefix("members/")
        if output_relative.casefold() in {MIGRATION_RECEIPT.casefold(), ROLLBACK_RECEIPT.casefold()}:
            raise MigrationError("MIGRATION_TARGET_UNSAFE")
        source = backup._contained_file(package, relative)
        data = backup._read_source_bytes(source, backup._source_signature(source))
        if len(data) != row["size_bytes"] or hashlib.sha256(data).hexdigest() != row["sha256"]:
            raise MigrationError("MIGRATION_SOURCE_CHANGED")
        total += len(data)
        if total > max_total_bytes:
            raise MigrationError("MIGRATION_RESOURCE_LIMIT_EXCEEDED")
        values[relative.removeprefix("members/")] = data
    return values


def _destination(path: Path, *, source: Path, forbidden_roots: Sequence[Path]) -> Path:
    original = os.fspath(path)
    if original.startswith(("\\\\", "//")) or any(part == ".." for part in Path(path).parts):
        raise MigrationError("MIGRATION_TARGET_UNSAFE")
    target = Path(os.path.abspath(path))
    if not target.name or backup._is_reparse_or_symlink(target.parent):
        raise MigrationError("MIGRATION_TARGET_UNSAFE")
    backup._reject_reparse_components(target.parent)
    resolved_parent = target.parent.resolve(strict=True)
    target = resolved_parent / target.name
    for part in target.parts[1:]:
        stem = part.split(".", 1)[0].upper()
        if (":" in part or part.endswith((".", " "))
                or stem in {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)),
                            *(f"LPT{i}" for i in range(1, 10))}):
            raise MigrationError("MIGRATION_TARGET_UNSAFE")
    repo = Path(__file__).resolve().parents[2]
    protected = [source.resolve(strict=True), repo,
                 *(Path(item).resolve(strict=True) for item in forbidden_roots)]
    if any(target == item or target in item.parents or item in target.parents for item in protected):
        raise MigrationError("MIGRATION_TARGET_UNSAFE")
    if os.path.lexists(target):
        raise MigrationError("MIGRATION_TARGET_UNSAFE")
    return target


def _check_existing_isolated(path: Path, *, backup_path: Path,
                             forbidden_roots: Sequence[Path]) -> Path:
    try:
        backup._reject_reparse_components(path)
        resolved = Path(path).resolve(strict=True)
        if not resolved.is_dir():
            raise MigrationError("MIGRATION_TARGET_UNSAFE")
        repo = Path(__file__).resolve().parents[2]
        protected = [Path(backup_path).resolve(strict=True), repo,
                     *(Path(item).resolve(strict=True) for item in forbidden_roots)]
        if any(resolved == item or resolved in item.parents or item in resolved.parents for item in protected):
            raise MigrationError("MIGRATION_TARGET_UNSAFE")
        return resolved
    except MigrationError:
        raise
    except (OSError, RuntimeError, ValueError) as exc:
        raise MigrationError("MIGRATION_TARGET_UNSAFE") from exc


def _write_members(root: Path, members: Mapping[str, bytes]) -> None:
    folded: set[str] = set()
    for relative, data in sorted(members.items()):
        safe = backup._relative(relative)
        if safe.casefold() in folded:
            raise MigrationError("MIGRATION_TARGET_UNSAFE")
        folded.add(safe.casefold())
        target = root.joinpath(*safe.split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())


def _member_records(members: Mapping[str, bytes]) -> dict[str, dict[str, Any]]:
    return {key: {"size_bytes": len(value), "sha256": hashlib.sha256(value).hexdigest()}
            for key, value in sorted(members.items())}


def _verify_watchlist_members(root: Path, manifest: Mapping[str, Any]) -> None:
    for row in manifest.get("members", []):
        if row.get("artifact_family") != "persistent_watchlists_and_revision_database":
            continue
        relative = backup._relative(row.get("backup_relative_path")).removeprefix("members/")
        path = root.joinpath(*relative.split("/"))
        try:
            connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
            try:
                if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise MigrationError("MIGRATION_VERIFICATION_FAILED")
            finally:
                connection.close()
            backup._verify_watchlist_database(path)
        except (OSError, sqlite3.Error, backup.BackupError) as exc:
            raise MigrationError("MIGRATION_VERIFICATION_FAILED") from exc


def _receipt_body(plan: MigrationPlan, facts: Mapping[str, Any],
                  source_inventory: Mapping[str, tuple[int, str]],
                  target_members: Mapping[str, bytes], run_id: str,
                  created_at: str) -> dict[str, Any]:
    payload = plan.to_dict()
    return {
        "receipt_schema_version": MIGRATION_RECEIPT_SCHEMA,
        "migration_run_id": run_id,
        "migration_plan_id": plan.migration_plan_id,
        "migration_plan_sha256": plan.plan_integrity_sha256,
        "migration_id": plan.migration_id,
        "source_backup_id": facts["manifest"]["backup_id"],
        "source_backup_manifest_sha256": facts["manifest_sha256"],
        "source_state_identity": facts["manifest"]["source_state_identity"],
        "source_selection_scope": backup.SELECTION_SCOPE,
        "checkpoint_kind": CHECKPOINT_KIND,
        "checkpoint_backup_id": facts["manifest"]["backup_id"],
        "checkpoint_manifest_sha256": facts["manifest_sha256"],
        "compatibility_contract_sha256": plan.compatibility_contract_sha256,
        "compatibility_attestation_sha256": plan.compatibility_attestation_sha256,
        "source_versions": json.loads(plan.source_versions_json),
        "target_versions": json.loads(plan.target_versions_json),
        "source_inventory_sha256": _inventory_sha(source_inventory),
        "target_inventory_sha256": _inventory_sha({
            key: (len(value), hashlib.sha256(value).hexdigest())
            for key, value in target_members.items()}),
        "affected_members": json.loads(plan.affected_members_json),
        "unchanged_members": json.loads(plan.unchanged_members_json),
        "migration_outcome": "MIGRATION_APPLIED_VERIFIED",
        "members": _member_records(target_members),
        "created_at": created_at,
    }


def apply_migration(*, plan: MigrationPlan, backup_path: Path,
                    compatibility: restore.CompatibilityAttestation,
                    contract: restore.RestoreCompatibilityContract = restore.DEFAULT_COMPATIBILITY_CONTRACT,
                    destination: Path, forbidden_roots: Sequence[Path],
                    max_total_bytes: int, max_member_count: int,
                    max_changed_members: int, migration_run_id: str,
                    created_at: str,
                    _test_only_registry: Sequence[MigrationDefinition] | None = None) -> dict[str, Any]:
    """Copy-on-write apply. Production KNOWN_NOT_IMPLEMENTED exits before target writes."""
    if not _ID.fullmatch(migration_run_id):
        raise MigrationError("MIGRATION_PLAN_INVALID")
    _require_utc(created_at)
    registry = MIGRATION_REGISTRY if _test_only_registry is None else tuple(_test_only_registry)
    if _test_only_registry is not None and any(
        item.implementation_status != "TEST_ONLY_SYNTHETIC_TRANSFORMER" for item in registry
    ):
        raise MigrationError("MIGRATION_PATH_NOT_IMPLEMENTED")
    facts, _ = _validate_plan(plan, backup_path=backup_path, compatibility=compatibility,
                              contract=contract, max_total_bytes=max_total_bytes,
                              max_member_count=max_member_count,
                              forbidden_roots=forbidden_roots, registry=registry)
    definition = next(row for row in registry if row.migration_id == plan.migration_id)
    if definition.implementation_status != "IMPLEMENTED" and _test_only_registry is None:
        raise MigrationError("MIGRATION_PATH_NOT_IMPLEMENTED")
    if definition.implementation_status not in {"IMPLEMENTED", "TEST_ONLY_SYNTHETIC_TRANSFORMER"} or definition.transformer is None:
        raise MigrationError("MIGRATION_PATH_NOT_IMPLEMENTED")
    plan_changed_limit = json.loads(plan.resource_limits_json).get("max_changed_members")
    if (not isinstance(plan_changed_limit, int) or isinstance(plan_changed_limit, bool)
            or plan_changed_limit <= 0
            or len(json.loads(plan.affected_members_json)) > min(max_changed_members, plan_changed_limit)):
        raise MigrationError("MIGRATION_RESOURCE_LIMIT_EXCEEDED")
    package = Path(backup_path).resolve(strict=True)
    before_package = _inventory(package, include_receipts=True)
    manifest = facts["manifest"]
    if manifest["member_count"] > max_member_count or manifest["total_size_bytes"] > max_total_bytes:
        raise MigrationError("MIGRATION_RESOURCE_LIMIT_EXCEEDED")
    target = _destination(destination, source=package, forbidden_roots=forbidden_roots)
    staging = target.parent / f".{target.name}.migration-staging-{migration_run_id}"
    if os.path.lexists(staging):
        raise MigrationError("MIGRATION_TARGET_UNSAFE")
    original = _read_members(package, manifest, max_total_bytes=max_total_bytes)
    original_inventory = {key: (len(data), hashlib.sha256(data).hexdigest())
                          for key, data in original.items()}
    transformed = dict(definition.transformer(dict(original)))
    if set(transformed) != set(original) or any(not isinstance(value, bytes) for value in transformed.values()):
        raise MigrationError("MIGRATION_VERIFICATION_FAILED")
    allowed = {row["backup_relative_path"].removeprefix("members/")
               for row in manifest["members"]
               if row["logical_member_id"] in json.loads(plan.affected_members_json)}
    changed = {key for key in original if original[key] != transformed[key]}
    if not changed <= allowed or not changed:
        raise MigrationError("MIGRATION_VERIFICATION_FAILED")
    for key in original:
        if key not in allowed and transformed[key] != original[key]:
            raise MigrationError("MIGRATION_VERIFICATION_FAILED")
    # Re-run the deterministic transformer before finalization and compare exact
    # outputs. This is an in-memory verifier; source bytes are never rewritten.
    expected = dict(definition.transformer(dict(original)))
    if expected != transformed:
        raise MigrationError("MIGRATION_VERIFICATION_FAILED")
    try:
        staging.mkdir(parents=False, exist_ok=False)
        _write_members(staging, transformed)
        _verify_watchlist_members(staging, manifest)
        written_inventory = _inventory(staging)
        expected_inventory = {key: (len(value), hashlib.sha256(value).hexdigest())
                              for key, value in transformed.items()}
        if written_inventory != expected_inventory:
            raise MigrationError("MIGRATION_VERIFICATION_FAILED")
        receipt = _receipt_body(plan, facts, original_inventory, transformed,
                                migration_run_id, created_at)
        receipt["receipt_integrity"] = _integrity(receipt, "receipt_integrity")
        (staging / MIGRATION_RECEIPT).write_bytes(_canonical(receipt) + b"\n")
        verify_migrated_state(
            migration_root=staging, plan=plan, backup_path=backup_path,
            compatibility=compatibility, contract=contract,
            max_total_bytes=max_total_bytes, max_member_count=max_member_count,
            max_changed_members=max_changed_members,
            forbidden_roots=forbidden_roots,
            _test_only_registry=_test_only_registry)
        if _inventory(package, include_receipts=True) != before_package:
            raise MigrationError("MIGRATION_SOURCE_CHANGED")
        os.rename(staging, target)
    except Exception:
        # A failed staging tree remains explicitly non-final for inspection.
        raise
    return {"status": "MIGRATION_APPLIED_VERIFIED", "migration_path": str(target),
            "migration_run_id": migration_run_id,
            "source_backup_id": manifest["backup_id"],
            "source_backup_manifest_sha256": facts["manifest_sha256"],
            "member_count": len(transformed), "changed_member_count": len(changed)}


def verify_migrated_state(*, migration_root: Path, plan: MigrationPlan,
                          backup_path: Path,
                          compatibility: restore.CompatibilityAttestation,
                          contract: restore.RestoreCompatibilityContract = restore.DEFAULT_COMPATIBILITY_CONTRACT,
                          max_total_bytes: int, max_member_count: int,
                          max_changed_members: int,
                          forbidden_roots: Sequence[Path],
                          _test_only_registry: Sequence[MigrationDefinition] | None = None) -> dict[str, Any]:
    """Read-only receipt, lineage, changed/unchanged member and inventory verification."""
    registry = MIGRATION_REGISTRY if _test_only_registry is None else tuple(_test_only_registry)
    facts, payload = _validate_plan(plan, backup_path=backup_path, compatibility=compatibility,
                                    contract=contract, max_total_bytes=max_total_bytes,
                                    max_member_count=max_member_count,
                                    forbidden_roots=forbidden_roots, registry=registry)
    definition = next(row for row in registry if row.migration_id == plan.migration_id)
    if definition.transformer is None:
        raise MigrationError("MIGRATION_PATH_NOT_IMPLEMENTED")
    root = Path(migration_root)
    try:
        resolved = _check_existing_isolated(root, backup_path=backup_path,
                                            forbidden_roots=forbidden_roots)
        receipt_path = resolved / MIGRATION_RECEIPT
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"),
                             object_pairs_hook=backup._strict_object)
    except (OSError, ValueError, json.JSONDecodeError, backup.BackupError) as exc:
        raise MigrationError("MIGRATION_VERIFICATION_FAILED") from exc
    if (not isinstance(receipt, dict) or receipt.get("receipt_schema_version") != MIGRATION_RECEIPT_SCHEMA
            or set(receipt) != {"receipt_schema_version", "migration_run_id", "migration_plan_id",
                                "migration_plan_sha256", "migration_id", "source_backup_id",
                                "source_backup_manifest_sha256", "source_state_identity",
                                "source_selection_scope", "checkpoint_kind", "checkpoint_backup_id",
                                "checkpoint_manifest_sha256", "compatibility_contract_sha256",
                                "compatibility_attestation_sha256", "source_versions", "target_versions",
                                "source_inventory_sha256", "target_inventory_sha256", "affected_members",
                                "unchanged_members", "migration_outcome", "members", "created_at",
                                "receipt_integrity"}):
        raise MigrationError("MIGRATION_VERIFICATION_FAILED")
    body = dict(receipt)
    integrity = body.pop("receipt_integrity", None)
    if not isinstance(integrity, Mapping) or integrity != _integrity(body, "receipt_integrity"):
        raise MigrationError("MIGRATION_VERIFICATION_FAILED")
    if (receipt.get("migration_plan_id") != plan.migration_plan_id
            or receipt.get("migration_plan_sha256") != plan.plan_integrity_sha256
            or receipt.get("migration_id") != plan.migration_id
            or receipt.get("source_backup_id") != facts["manifest"]["backup_id"]
            or receipt.get("source_backup_manifest_sha256") != facts["manifest_sha256"]
            or receipt.get("source_state_identity") != facts["manifest"]["source_state_identity"]
            or receipt.get("source_selection_scope") != backup.SELECTION_SCOPE
            or receipt.get("checkpoint_kind") != CHECKPOINT_KIND
            or receipt.get("checkpoint_backup_id") != facts["manifest"]["backup_id"]
            or receipt.get("checkpoint_manifest_sha256") != facts["manifest_sha256"]
            or receipt.get("compatibility_contract_sha256") != facts["inspection"]["target_contract_sha256"]
            or receipt.get("compatibility_attestation_sha256") != facts["attestation_sha256"]
            or receipt.get("source_versions") != facts["inspection"]["source_state_family_versions"]
            or receipt.get("target_versions") != facts["inspection"]["target_supported_state_family_versions"]
            or receipt.get("migration_outcome") != "MIGRATION_APPLIED_VERIFIED"):
        raise MigrationError("MIGRATION_VERIFICATION_FAILED")
    _require_utc(receipt.get("created_at"))
    if not isinstance(receipt.get("migration_run_id"), str) or not _ID.fullmatch(receipt["migration_run_id"]):
        raise MigrationError("MIGRATION_VERIFICATION_FAILED")
    source = _read_members(Path(backup_path).resolve(strict=True), facts["manifest"],
                           max_total_bytes=max_total_bytes)
    transformed = dict(definition.transformer(dict(source)))
    _verify_watchlist_members(resolved, facts["manifest"])
    actual = _inventory(resolved, include_receipts=True)
    expected = {key: (len(value), hashlib.sha256(value).hexdigest())
                for key, value in transformed.items()}
    expected[ MIGRATION_RECEIPT ] = (len((resolved / MIGRATION_RECEIPT).read_bytes()),
                                     hashlib.sha256((resolved / MIGRATION_RECEIPT).read_bytes()).hexdigest())
    if actual != expected or receipt.get("target_inventory_sha256") != _inventory_sha({
            key: (len(value), hashlib.sha256(value).hexdigest()) for key, value in transformed.items()}):
        raise MigrationError("MIGRATION_VERIFICATION_FAILED")
    if not _has_exact_directories(resolved, list(transformed), receipt_name=MIGRATION_RECEIPT):
        raise MigrationError("MIGRATION_VERIFICATION_FAILED")
    source_hash = _inventory_sha({key: (len(value), hashlib.sha256(value).hexdigest())
                                  for key, value in source.items()})
    if (receipt.get("source_inventory_sha256") != source_hash
            or receipt.get("members") != _member_records(transformed)
            or receipt.get("affected_members") != json.loads(plan.affected_members_json)
            or receipt.get("unchanged_members") != json.loads(plan.unchanged_members_json)):
        raise MigrationError("MIGRATION_VERIFICATION_FAILED")
    changed = sorted(key for key in source if source[key] != transformed.get(key))
    plan_changed_limit = json.loads(plan.resource_limits_json).get("max_changed_members", 0)
    if len(changed) > min(max_changed_members, plan_changed_limit) or not set(changed) <= {
            row["backup_relative_path"].removeprefix("members/") for row in facts["manifest"]["members"]
            if row["logical_member_id"] in json.loads(plan.affected_members_json)}:
        raise MigrationError("MIGRATION_VERIFICATION_FAILED")
    unchanged = sorted(key for key in source if source[key] == transformed.get(key))
    if receipt.get("affected_members") != json.loads(plan.affected_members_json):
        raise MigrationError("MIGRATION_VERIFICATION_FAILED")
    return {"status": "MIGRATION_APPLIED_VERIFIED", "member_count": len(transformed),
            "changed_members": changed, "unchanged_files": unchanged,
            "source_inventory_sha256": source_hash,
            "target_inventory_sha256": receipt["target_inventory_sha256"]}


def rollback_migration(*, migration_root: Path, destination: Path, plan: MigrationPlan,
                       backup_path: Path, compatibility: restore.CompatibilityAttestation,
                       contract: restore.RestoreCompatibilityContract = restore.DEFAULT_COMPATIBILITY_CONTRACT,
                       forbidden_roots: Sequence[Path], max_total_bytes: int,
                       max_member_count: int, max_changed_members: int,
                       rollback_id: str, created_at: str,
                       _test_only_registry: Sequence[MigrationDefinition] | None = None) -> dict[str, Any]:
    """Materialize a new isolated rollback candidate from retained A4 bytes."""
    _require_utc(created_at)
    verify_migrated_state(
        migration_root=migration_root, plan=plan, backup_path=backup_path,
        compatibility=compatibility, contract=contract,
        max_total_bytes=max_total_bytes, max_member_count=max_member_count,
        max_changed_members=max_changed_members,
        forbidden_roots=forbidden_roots,
        _test_only_registry=_test_only_registry)
    package = Path(backup_path).resolve(strict=True)
    package_before = _inventory(package, include_receipts=True)
    migration_before = _inventory(Path(migration_root), include_receipts=True)
    facts, _ = _validate_plan(plan, backup_path=backup_path, compatibility=compatibility,
                              contract=contract, max_total_bytes=max_total_bytes,
                              max_member_count=max_member_count,
                              forbidden_roots=forbidden_roots,
                              registry=MIGRATION_REGISTRY if _test_only_registry is None else tuple(_test_only_registry))
    target = _destination(destination, source=package,
                          forbidden_roots=[*forbidden_roots, Path(migration_root)])
    staging = target.parent / f".{target.name}.rollback-staging-{rollback_id}"
    if not _ID.fullmatch(rollback_id) or os.path.lexists(staging):
        raise MigrationError("ROLLBACK_TARGET_UNSAFE")
    original = _read_members(package, facts["manifest"], max_total_bytes=max_total_bytes)
    try:
        staging.mkdir(parents=False, exist_ok=False)
        _write_members(staging, original)
        body = {"rollback_receipt_schema_version": ROLLBACK_RECEIPT_SCHEMA,
                "rollback_id": rollback_id,
                "migration_run_id": json.loads((Path(migration_root) / MIGRATION_RECEIPT).read_text(encoding="utf-8"))["migration_run_id"],
                "migration_plan_id": plan.migration_plan_id,
                "migration_receipt_sha256": hashlib.sha256((Path(migration_root) / MIGRATION_RECEIPT).read_bytes()).hexdigest(),
                "checkpoint_kind": CHECKPOINT_KIND,
                "checkpoint_backup_id": facts["manifest"]["backup_id"],
                "checkpoint_manifest_sha256": facts["manifest_sha256"],
                "rollback_scope": backup.SELECTION_SCOPE,
                "restored_member_count": len(original),
                "restored_total_bytes": sum(map(len, original.values())),
                "members": _member_records(original), "created_at": created_at}
        body["receipt_integrity"] = _integrity(body, "receipt_integrity")
        (staging / ROLLBACK_RECEIPT).write_bytes(_canonical(body) + b"\n")
        verification = verify_rollback(
            rollback_root=staging, migration_root=migration_root, plan=plan,
            backup_path=backup_path, compatibility=compatibility, contract=contract,
            max_total_bytes=max_total_bytes, max_member_count=max_member_count,
            max_changed_members=max_changed_members,
            forbidden_roots=forbidden_roots,
            _test_only_registry=_test_only_registry)
        if (_inventory(package, include_receipts=True) != package_before
                or _inventory(Path(migration_root), include_receipts=True) != migration_before):
            raise MigrationError("MIGRATION_SOURCE_CHANGED")
        os.rename(staging, target)
    except Exception:
        raise
    return {**verification, "status": "ROLLBACK_COMPLETED", "rollback_path": str(target)}


def verify_rollback(*, rollback_root: Path, migration_root: Path, plan: MigrationPlan,
                    backup_path: Path, compatibility: restore.CompatibilityAttestation,
                    contract: restore.RestoreCompatibilityContract = restore.DEFAULT_COMPATIBILITY_CONTRACT,
                    max_total_bytes: int, max_member_count: int,
                    max_changed_members: int,
                    forbidden_roots: Sequence[Path],
                    _test_only_registry: Sequence[MigrationDefinition] | None = None) -> dict[str, Any]:
    """Read-only verification binds receipt to A4 and the independently verified migration."""
    migrated = verify_migrated_state(
        migration_root=migration_root, plan=plan, backup_path=backup_path,
        compatibility=compatibility, contract=contract,
        max_total_bytes=max_total_bytes, max_member_count=max_member_count,
        max_changed_members=max_changed_members, forbidden_roots=forbidden_roots,
        _test_only_registry=_test_only_registry)
    root = _check_existing_isolated(rollback_root, backup_path=backup_path,
                                    forbidden_roots=[*forbidden_roots, Path(migration_root)])
    receipt_path = root / ROLLBACK_RECEIPT
    try:
        backup._reject_reparse_components(root)
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"),
                             object_pairs_hook=backup._strict_object)
    except (OSError, ValueError, json.JSONDecodeError, backup.BackupError) as exc:
        raise MigrationError("ROLLBACK_VERIFICATION_FAILED") from exc
    if (not isinstance(receipt, dict)
            or receipt.get("rollback_receipt_schema_version") != ROLLBACK_RECEIPT_SCHEMA):
        raise MigrationError("ROLLBACK_VERIFICATION_FAILED")
    body = dict(receipt)
    integrity = body.pop("receipt_integrity", None)
    if not isinstance(integrity, Mapping) or integrity != _integrity(body, "receipt_integrity"):
        raise MigrationError("ROLLBACK_VERIFICATION_FAILED")
    facts, _ = _validate_plan(plan, backup_path=backup_path, compatibility=compatibility,
                              contract=contract, max_total_bytes=max_total_bytes,
                              max_member_count=max_member_count,
                              forbidden_roots=forbidden_roots,
                              registry=MIGRATION_REGISTRY if _test_only_registry is None else tuple(_test_only_registry))
    source = _read_members(Path(backup_path).resolve(strict=True), facts["manifest"],
                           max_total_bytes=max_total_bytes)
    expected = {key: (len(value), hashlib.sha256(value).hexdigest()) for key, value in source.items()}
    actual = _inventory(root)
    if (actual != expected
            or receipt.get("checkpoint_kind") != CHECKPOINT_KIND
            or receipt.get("checkpoint_backup_id") != facts["manifest"]["backup_id"]
            or receipt.get("members") != _member_records(source)):
        raise MigrationError("ROLLBACK_VERIFICATION_FAILED")
    for field in ("restored_member_count", "restored_total_bytes"):
        value = receipt.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise MigrationError("ROLLBACK_VERIFICATION_FAILED")
    if not _has_exact_directories(root, list(source), receipt_name=ROLLBACK_RECEIPT):
        raise MigrationError("ROLLBACK_VERIFICATION_FAILED")
    if (receipt.get("checkpoint_manifest_sha256") != facts["manifest_sha256"]
            or receipt.get("migration_plan_id") != plan.migration_plan_id
            or receipt.get("migration_run_id") != json.loads((Path(migration_root) / MIGRATION_RECEIPT).read_text(encoding="utf-8")).get("migration_run_id")
            or receipt.get("migration_receipt_sha256") != hashlib.sha256(
                (Path(migration_root) / MIGRATION_RECEIPT).read_bytes()).hexdigest()
            or receipt.get("rollback_scope") != backup.SELECTION_SCOPE
            or receipt.get("restored_member_count") != len(source)
            or receipt.get("restored_total_bytes") != sum(map(len, source.values()))):
        raise MigrationError("ROLLBACK_VERIFICATION_FAILED")
    _require_utc(receipt.get("created_at"))
    if (not isinstance(receipt.get("rollback_id"), str)
            or not _ID.fullmatch(receipt["rollback_id"])
            or set(receipt) != {"rollback_receipt_schema_version", "rollback_id", "migration_run_id",
                                "migration_plan_id", "migration_receipt_sha256", "checkpoint_kind",
                                "checkpoint_backup_id", "checkpoint_manifest_sha256", "rollback_scope",
                                "restored_member_count", "restored_total_bytes", "members", "created_at",
                                "receipt_integrity"}):
        raise MigrationError("ROLLBACK_VERIFICATION_FAILED")
    return {"status": "ROLLBACK_VERIFIED", "source_backup_id": facts["manifest"]["backup_id"],
            "member_count": len(source), "total_size_bytes": sum(map(len, source.values())),
            "migration_status": migrated["status"]}
