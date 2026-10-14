"""Internal A5 restore compatibility inspection and isolated byte-preserving restore.

This module never activates restored state or applies migrations. Compatibility is
re-derived from the verified A4 manifest, an explicitly supplied trusted-caller
state-family version attestation, and the supplied versioned target contract.
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
from server.services.unified_backup import BackupError


RESTORE_CONTRACT_VERSION = "tw_market_restore_contract.v1"
RECEIPT_NAME = "restore-receipt.json"
RECEIPT_SCHEMA_VERSION = "tw_market_restore_receipt.v1"
RESTORE_SCOPE = "EXPLICIT_DECLARED_MEMBERS_ONLY"
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_CANONICAL_FAMILIES = {
    "security_master_active_release_pointer",
    "security_master_release_history_and_rollback_artifacts",
    "persistent_watchlists_and_revision_database",
    "user_product_settings",
}
_WATCHLIST_FAMILY = "persistent_watchlists_and_revision_database"
_RECEIPT_FIELDS = {
    "restore_receipt_schema_version", "restore_id", "backup_id",
    "backup_manifest_sha256", "backup_format_version", "source_state_identity",
    "restore_scope", "compatibility_outcome", "target_contract_version",
    "target_contract_sha256",
    "state_family_versions", "restored_member_count", "restored_total_bytes",
    "members", "created_at", "receipt_integrity",
}
_MEMBER_RECEIPT_FIELDS = {
    "logical_member_id", "artifact_family", "backup_relative_path",
    "restore_relative_path", "size_bytes", "sha256",
}


class RestoreError(RuntimeError):
    """Bounded A5 operation failure with a machine-readable outcome."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class RestoreCompatibilityContract:
    product_identity: str
    restore_contract_version: str
    supported_backup_formats: tuple[str, ...]
    supported_manifest_versions: tuple[str, ...]
    supported_state_family_versions: Mapping[str, tuple[str, ...]]
    migration_rules: Mapping[tuple[str, str], str]


@dataclass(frozen=True)
class CompatibilityAttestation:
    """Trusted internal caller's family-version facts, bound to one A4 manifest."""

    backup_manifest_sha256: str
    state_family_versions: Mapping[str, str]


DEFAULT_COMPATIBILITY_CONTRACT = RestoreCompatibilityContract(
    product_identity=backup.PRODUCT_IDENTITY,
    restore_contract_version=RESTORE_CONTRACT_VERSION,
    supported_backup_formats=(backup.BACKUP_FORMAT_VERSION,),
    supported_manifest_versions=(backup.MANIFEST_SCHEMA_VERSION,),
    supported_state_family_versions={
        "security_master_active_release_pointer": ("1",),
        "security_master_release_history_and_rollback_artifacts": ("1",),
        _WATCHLIST_FAMILY: ("1",),
    },
    # A5 classifies this explicitly declared historical Watchlist state only;
    # transformation remains outside this module and requires a later A6 rule.
    migration_rules={(_WATCHLIST_FAMILY, "0"): "watchlist-schema-v0-to-v1"},
)


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _receipt_hash(receipt: Mapping[str, Any]) -> str:
    body = dict(receipt)
    body.pop("receipt_integrity", None)
    return hashlib.sha256(_canonical_bytes(body)).hexdigest()


def _contract_hash(contract: RestoreCompatibilityContract) -> str:
    payload = {
        "product_identity": contract.product_identity,
        "restore_contract_version": contract.restore_contract_version,
        "supported_backup_formats": sorted(contract.supported_backup_formats),
        "supported_manifest_versions": sorted(contract.supported_manifest_versions),
        "supported_state_family_versions": {
            key: sorted(value) for key, value in sorted(contract.supported_state_family_versions.items())
        },
        "migration_rules": [
            {"state_family": family, "source_version": version, "migration_id": migration}
            for (family, version), migration in sorted(contract.migration_rules.items())
        ],
    }
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _reject_json_constant(value: str) -> None:
    raise RestoreError("RESTORE_VERIFICATION_FAILED")


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise RestoreError("RESTORE_VERIFICATION_FAILED")
        result[key] = value
    return result


def _load_manifest(package: Path) -> dict[str, Any]:
    try:
        backup._reject_reparse_components(package)
        root = package.resolve(strict=True)
        manifest_path = root / backup.MANIFEST_NAME
        if not root.is_dir() or backup._is_reparse_or_symlink(manifest_path) or not manifest_path.is_file():
            raise RestoreError("RESTORE_SOURCE_INVALID")
        raw = manifest_path.read_text(encoding="utf-8")
        value = json.loads(raw, object_pairs_hook=_strict_object, parse_constant=_reject_json_constant)
    except RestoreError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RestoreError("RESTORE_SOURCE_INVALID") from exc
    if not isinstance(value, dict):
        raise RestoreError("RESTORE_SOURCE_INVALID")
    return value


def _verify_source(backup_path: Path, max_total_bytes: int, max_member_count: int) -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(max_total_bytes, int) or isinstance(max_total_bytes, bool) or max_total_bytes <= 0:
        raise RestoreError("RESTORE_RESOURCE_LIMIT_EXCEEDED")
    if not isinstance(max_member_count, int) or isinstance(max_member_count, bool) or max_member_count <= 0:
        raise RestoreError("RESTORE_RESOURCE_LIMIT_EXCEEDED")
    # Read only the small manifest first so declared bounds are rejected before
    # A4 hashes any member bytes.
    preliminary = _load_manifest(Path(backup_path))
    if preliminary.get("product_identity") != backup.PRODUCT_IDENTITY:
        raise RestoreError("PRODUCT_IDENTITY_MISMATCH")
    if isinstance(preliminary.get("members"), list) and len(preliminary["members"]) > max_member_count:
        raise RestoreError("RESTORE_RESOURCE_LIMIT_EXCEEDED")
    if isinstance(preliminary.get("total_size_bytes"), int) and preliminary["total_size_bytes"] > max_total_bytes:
        raise RestoreError("RESTORE_RESOURCE_LIMIT_EXCEEDED")
    try:
        verified = backup.verify_backup(backup_path, max_total_bytes=max_total_bytes)
    except BackupError as exc:
        if exc.code == "BACKUP_UNSUPPORTED_VERSION":
            raise RestoreError("UNSUPPORTED_BACKUP_FORMAT") from exc
        if exc.code == "BACKUP_RESOURCE_LIMIT_EXCEEDED":
            raise RestoreError("RESTORE_RESOURCE_LIMIT_EXCEEDED") from exc
        code = "RESTORE_MEMBER_INTEGRITY_FAILED" if exc.code in {
            "BACKUP_MEMBER_HASH_MISMATCH", "BACKUP_MEMBER_SIZE_MISMATCH",
            "BACKUP_MEMBER_MISSING", "BACKUP_MEMBER_UNEXPECTED",
        } else "RESTORE_SOURCE_INVALID"
        raise RestoreError(code) from exc
    package = Path(backup_path).resolve(strict=True)
    manifest = _load_manifest(package)
    if manifest.get("product_identity") != backup.PRODUCT_IDENTITY:
        raise RestoreError("PRODUCT_IDENTITY_MISMATCH")
    if len(manifest.get("members", [])) > max_member_count:
        raise RestoreError("RESTORE_RESOURCE_LIMIT_EXCEEDED")
    return verified, manifest


def _validate_contract(contract: RestoreCompatibilityContract) -> None:
    if not isinstance(contract, RestoreCompatibilityContract):
        raise RestoreError("RESTORE_COMPATIBILITY_UNKNOWN")
    if (contract.product_identity != backup.PRODUCT_IDENTITY
            or not isinstance(contract.restore_contract_version, str)
            or not _ID_RE.fullmatch(contract.restore_contract_version)
            or not contract.supported_backup_formats
            or not contract.supported_manifest_versions):
        raise RestoreError("RESTORE_COMPATIBILITY_UNKNOWN")


def _watchlist_schema_version(package: Path, member: Mapping[str, Any]) -> str | None:
    try:
        relative = backup._relative(member.get("backup_relative_path"))
        path = _verify_member_path(package, relative)
        connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
        try:
            versions = [str(row[0]) for row in connection.execute(
                "SELECT version FROM schema_migrations ORDER BY version"
            )]
        finally:
            connection.close()
        return versions[0] if len(versions) == 1 else None
    except (BackupError, RestoreError, OSError, sqlite3.Error, ValueError):
        return None


def _classify(manifest: Mapping[str, Any], manifest_sha256: str,
              attestation: CompatibilityAttestation,
              contract: RestoreCompatibilityContract,
              package: Path | None = None) -> dict[str, Any]:
    _validate_contract(contract)
    if manifest.get("product_identity") != contract.product_identity:
        return {"status": "PRODUCT_IDENTITY_MISMATCH", "migration_paths": []}
    if manifest.get("backup_format_version") not in contract.supported_backup_formats:
        return {"status": "UNSUPPORTED_BACKUP_FORMAT", "migration_paths": []}
    if manifest.get("manifest_schema_version") not in contract.supported_manifest_versions:
        return {"status": "UNSUPPORTED_BACKUP_FORMAT", "migration_paths": []}
    if (not isinstance(attestation, CompatibilityAttestation)
            or attestation.backup_manifest_sha256 != manifest_sha256
            or not isinstance(attestation.state_family_versions, Mapping)):
        return {"status": "RESTORE_COMPATIBILITY_UNKNOWN", "migration_paths": []}
    members = manifest.get("members")
    if not isinstance(members, list):
        return {"status": "RESTORE_SOURCE_INVALID", "migration_paths": []}
    expected_facts: dict[str, str] = {}
    migrations: set[str] = set()
    for member in members:
        if not isinstance(member, dict):
            return {"status": "RESTORE_SOURCE_INVALID", "migration_paths": []}
        family = member.get("artifact_family")
        if family not in _CANONICAL_FAMILIES:
            # Governed evidence is copied as opaque retained bytes; its Result or
            # Audit schema never stands in for installation-state compatibility.
            continue
        logical_id = member.get("logical_member_id")
        version = attestation.state_family_versions.get(logical_id)
        if not isinstance(logical_id, str) or not isinstance(version, str) or not version:
            return {"status": "RESTORE_COMPATIBILITY_UNKNOWN", "migration_paths": []}
        if family == _WATCHLIST_FAMILY:
            observed = _watchlist_schema_version(package, member) if package is not None else None
            if observed is None or observed != version:
                return {"status": "RESTORE_COMPATIBILITY_UNKNOWN", "migration_paths": []}
        expected_facts[logical_id] = version
        supported = contract.supported_state_family_versions.get(family, ())
        if version in supported:
            continue
        migration = contract.migration_rules.get((family, version))
        if migration:
            migrations.add(migration)
            continue
        # Numeric state versions above the highest explicit support are newer.
        if version.isdecimal() and supported and all(item.isdecimal() for item in supported):
            if int(version) > max(int(item) for item in supported):
                return {"status": "UNSUPPORTED_NEWER_STATE", "migration_paths": []}
        return {"status": "RESTORE_COMPATIBILITY_UNKNOWN", "migration_paths": []}
    if set(attestation.state_family_versions) != set(expected_facts):
        return {"status": "RESTORE_COMPATIBILITY_UNKNOWN", "migration_paths": []}
    if migrations:
        return {"status": "MIGRATION_REQUIRED", "migration_paths": sorted(migrations)}
    return {"status": "DIRECT_RESTORE_COMPATIBLE", "migration_paths": []}


def inspect_restore(*, backup_path: Path, compatibility: CompatibilityAttestation,
                    contract: RestoreCompatibilityContract = DEFAULT_COMPATIBILITY_CONTRACT,
                    max_total_bytes: int, max_member_count: int) -> dict[str, Any]:
    """Read-only A4 verification plus deterministic compatibility classification."""
    verified, manifest = _verify_source(backup_path, max_total_bytes, max_member_count)
    outcome = _classify(manifest, verified["manifest_sha256"], compatibility, contract,
                        Path(backup_path).resolve(strict=True))
    if manifest.get("selection_scope") != RESTORE_SCOPE:
        raise RestoreError("RESTORE_SCOPE_INCOMPLETE_FOR_REQUEST")
    return {
        **outcome,
        "backup_id": manifest["backup_id"],
        "backup_manifest_sha256": verified["manifest_sha256"],
        "backup_tier": manifest["backup_tier"],
        "restore_scope": RESTORE_SCOPE,
        "member_count": len(manifest["members"]),
        "total_size_bytes": manifest["total_size_bytes"],
        "target_contract_version": contract.restore_contract_version,
        "target_contract_sha256": _contract_hash(contract),
        "source_state_family_versions": dict(sorted(compatibility.state_family_versions.items())) if isinstance(compatibility, CompatibilityAttestation) else {},
        "target_supported_state_family_versions": {
            row["artifact_family"]: list(contract.supported_state_family_versions.get(row["artifact_family"], ()))
            for row in manifest["members"] if row["artifact_family"] in _CANONICAL_FAMILIES
        },
    }


def _unsafe_path(path: Path) -> bool:
    try:
        current = Path(path.anchor)
        for part in path.parts[1:]:
            current = current / part
            if current.is_symlink() or (current.exists() and bool(getattr(current.lstat(), "st_file_attributes", 0) & 0x400)):
                return True
        return False
    except OSError:
        return True


def _safe_relative(value: Any) -> str:
    try:
        return backup._relative(value)
    except BackupError as exc:
        raise RestoreError("RESTORE_TARGET_UNSAFE") from exc


def _resolve_destination(destination: Path, *, backup_path: Path,
                         forbidden_roots: Sequence[Path]) -> Path:
    if not isinstance(forbidden_roots, Sequence) or isinstance(forbidden_roots, (str, bytes)):
        raise RestoreError("RESTORE_TARGET_UNSAFE")
    original = Path(destination)
    original_text = os.fspath(original)
    # Tier-1 restore targets are local filesystem paths. Reject UNC/device paths
    # before exists()/resolve() can trigger SMB or other network filesystem I/O.
    if original_text.startswith("\\\\") or original_text.startswith("//"):
        raise RestoreError("RESTORE_TARGET_UNSAFE")
    if any(part == ".." for part in original.parts):
        raise RestoreError("RESTORE_TARGET_UNSAFE")
    raw = Path(os.path.abspath(original))
    if not raw.name or raw.name in {".", ".."} or _unsafe_path(raw.parent):
        raise RestoreError("RESTORE_TARGET_UNSAFE")
    if os.path.lexists(raw):
        if raw.is_symlink() or not raw.is_dir() or any(raw.iterdir()):
            raise RestoreError("RESTORE_TARGET_NOT_EMPTY")
        raise RestoreError("RESTORE_TARGET_NOT_EMPTY")
    try:
        parent = raw.parent.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise RestoreError("RESTORE_TARGET_UNSAFE") from exc
    if any(":" in part or part.endswith((".", " ")) or part.split(".", 1)[0].upper() in {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))} for part in raw.parts[1:]):
        raise RestoreError("RESTORE_TARGET_UNSAFE")
    final = parent / raw.name
    backup_root = Path(backup_path).resolve(strict=True)
    protected = [backup_root, *(Path(item).resolve(strict=True) for item in forbidden_roots)]
    for root in protected:
        if final == root or final in root.parents or root in final.parents:
            raise RestoreError("RESTORE_TARGET_UNSAFE")
    # Repository itself is always a forbidden target even when caller omitted it.
    repo_root = Path(__file__).resolve().parents[2]
    if final == repo_root or final in repo_root.parents or repo_root in final.parents:
        raise RestoreError("RESTORE_TARGET_UNSAFE")
    return final


def _source_inventory(package: Path) -> dict[str, tuple[int, str]]:
    inventory: dict[str, tuple[int, str]] = {}
    for path in package.rglob("*"):
        if backup._is_reparse_or_symlink(path):
            raise RestoreError("RESTORE_SOURCE_INVALID")
        if path.is_file():
            size, digest = backup._hash_file(path)
            inventory[path.relative_to(package).as_posix()] = (size, digest)
    return inventory


def _verify_watchlist(path: Path) -> None:
    try:
        connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
        try:
            if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise RestoreError("RESTORE_VERIFICATION_FAILED")
        finally:
            connection.close()
    except sqlite3.Error as exc:
        raise RestoreError("RESTORE_VERIFICATION_FAILED") from exc
    try:
        backup._verify_watchlist_database(path)
    except BackupError as exc:
        raise RestoreError("RESTORE_VERIFICATION_FAILED") from exc


def _verify_member_path(root: Path, relative: str) -> Path:
    safe = _safe_relative(relative)
    candidate = root.joinpath(*safe.split("/"))
    current = root
    for part in safe.split("/"):
        current = current / part
        if backup._is_reparse_or_symlink(current):
            raise RestoreError("RESTORE_TARGET_UNSAFE")
    try:
        resolved = candidate.resolve(strict=True)
        resolved_root = root.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise RestoreError("RESTORE_VERIFICATION_FAILED") from exc
    if resolved_root not in resolved.parents or not resolved.is_file():
        raise RestoreError("RESTORE_TARGET_UNSAFE")
    return candidate


def _make_receipt(manifest: Mapping[str, Any], *, manifest_sha256: str,
                  outcome: Mapping[str, Any], compatibility: CompatibilityAttestation,
                  restore_id: str, created_at: str, members: list[dict[str, Any]],
                  contract: RestoreCompatibilityContract) -> dict[str, Any]:
    receipt = {
        "restore_receipt_schema_version": RECEIPT_SCHEMA_VERSION,
        "restore_id": restore_id,
        "backup_id": manifest["backup_id"],
        "backup_manifest_sha256": manifest_sha256,
        "backup_format_version": manifest["backup_format_version"],
        "source_state_identity": manifest["source_state_identity"],
        "restore_scope": RESTORE_SCOPE,
        "compatibility_outcome": outcome["status"],
        "target_contract_version": contract.restore_contract_version,
        "target_contract_sha256": _contract_hash(contract),
        "state_family_versions": dict(sorted(compatibility.state_family_versions.items())),
        "restored_member_count": len(members),
        "restored_total_bytes": sum(row["size_bytes"] for row in members),
        "members": members,
        "created_at": created_at,
        "receipt_integrity": {"algorithm": "SHA-256", "coverage": "canonical UTF-8 JSON excluding receipt_integrity", "sha256": ""},
    }
    receipt["receipt_integrity"]["sha256"] = _receipt_hash(receipt)
    return receipt


def _validate_receipt_envelope(receipt: Mapping[str, Any]) -> None:
    if not isinstance(receipt, Mapping) or set(receipt) != _RECEIPT_FIELDS:
        raise RestoreError("RESTORE_VERIFICATION_FAILED")
    if not isinstance(receipt.get("restore_id"), str) or not _ID_RE.fullmatch(receipt["restore_id"]):
        raise RestoreError("RESTORE_VERIFICATION_FAILED")
    try:
        created_at = datetime.fromisoformat(str(receipt.get("created_at", "")).replace("Z", "+00:00"))
    except ValueError as exc:
        raise RestoreError("RESTORE_VERIFICATION_FAILED") from exc
    if created_at.tzinfo is None or created_at.utcoffset() != timezone.utc.utcoffset(created_at):
        raise RestoreError("RESTORE_VERIFICATION_FAILED")
    integrity = receipt.get("receipt_integrity")
    if (not isinstance(integrity, Mapping)
            or set(integrity) != {"algorithm", "coverage", "sha256"}
            or integrity.get("algorithm") != "SHA-256"
            or integrity.get("coverage") != "canonical UTF-8 JSON excluding receipt_integrity"
            or not isinstance(integrity.get("sha256"), str)
            or not _HASH_RE.fullmatch(integrity["sha256"])
            or integrity["sha256"] != _receipt_hash(receipt)):
        raise RestoreError("RESTORE_VERIFICATION_FAILED")
    for field in ("restored_member_count", "restored_total_bytes"):
        value = receipt.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise RestoreError("RESTORE_VERIFICATION_FAILED")
    versions = receipt.get("state_family_versions")
    if (not isinstance(versions, Mapping)
            or any(not isinstance(key, str) or not key or not isinstance(value, str) or not value
                   for key, value in versions.items())):
        raise RestoreError("RESTORE_VERIFICATION_FAILED")
    rows = receipt.get("members")
    if not isinstance(rows, list):
        raise RestoreError("RESTORE_VERIFICATION_FAILED")
    for row in rows:
        if not isinstance(row, Mapping) or set(row) != _MEMBER_RECEIPT_FIELDS:
            raise RestoreError("RESTORE_VERIFICATION_FAILED")
        if not isinstance(row.get("logical_member_id"), str) or not _ID_RE.fullmatch(row["logical_member_id"]):
            raise RestoreError("RESTORE_VERIFICATION_FAILED")
        if not isinstance(row.get("artifact_family"), str) or not row["artifact_family"]:
            raise RestoreError("RESTORE_VERIFICATION_FAILED")
        size = row.get("size_bytes")
        if not isinstance(size, int) or isinstance(size, bool) or size < 0:
            raise RestoreError("RESTORE_VERIFICATION_FAILED")
        if not isinstance(row.get("sha256"), str) or not _HASH_RE.fullmatch(row["sha256"]):
            raise RestoreError("RESTORE_VERIFICATION_FAILED")


def restore_backup(*, backup_path: Path, destination: Path,
                   compatibility: CompatibilityAttestation,
                   contract: RestoreCompatibilityContract = DEFAULT_COMPATIBILITY_CONTRACT,
                   forbidden_roots: Sequence[Path], max_total_bytes: int,
                   max_member_count: int, restore_id: str,
                   created_at: str, now: Callable[[], str] | None = None) -> dict[str, Any]:
    """Restore verified bytes into a new isolated root. Never overwrite or activate."""
    if not isinstance(restore_id, str) or not _ID_RE.fullmatch(restore_id):
        raise RestoreError("RESTORE_VERIFICATION_FAILED")
    timestamp = created_at if now is None else now()
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except (ValueError, AttributeError) as exc:
        raise RestoreError("RESTORE_VERIFICATION_FAILED") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise RestoreError("RESTORE_VERIFICATION_FAILED")
    inspection = inspect_restore(backup_path=backup_path, compatibility=compatibility,
                                 contract=contract, max_total_bytes=max_total_bytes,
                                 max_member_count=max_member_count)
    if inspection["status"] != "DIRECT_RESTORE_COMPATIBLE":
        return {**inspection, "restore_status": inspection["status"], "restore_path": None}
    final = _resolve_destination(destination, backup_path=backup_path, forbidden_roots=forbidden_roots)
    staging = final.parent / f".{final.name}.staging-{restore_id}"
    if os.path.lexists(staging):
        raise RestoreError("RESTORE_TARGET_NOT_EMPTY")
    package = Path(backup_path).resolve(strict=True)
    before = _source_inventory(package)
    manifest = _load_manifest(package)
    expected_manifest_sha = inspection["backup_manifest_sha256"]
    try:
        staging.mkdir(parents=False, exist_ok=False)
    except OSError as exc:
        raise RestoreError("RESTORE_TARGET_UNSAFE") from exc
    try:
        member_receipts: list[dict[str, Any]] = []
        total = 0
        for row in manifest["members"]:
            relative = _safe_relative(row["backup_relative_path"])
            source = _verify_member_path(package, relative)
            size, digest = backup._hash_file(source)
            if size != row["size_bytes"] or digest != row["sha256"]:
                raise RestoreError("RESTORE_MEMBER_INTEGRITY_FAILED")
            if size > max_total_bytes - total:
                raise RestoreError("RESTORE_RESOURCE_LIMIT_EXCEEDED")
            data = backup._read_source_bytes(source, backup._source_signature(source))
            if len(data) != size or hashlib.sha256(data).hexdigest() != digest:
                raise RestoreError("RESTORE_MEMBER_INTEGRITY_FAILED")
            target_relative = relative.removeprefix("members/")
            target_relative = _safe_relative(target_relative)
            target = staging.joinpath(*target_relative.split("/"))
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            if target.read_bytes() != data:
                raise RestoreError("RESTORE_VERIFICATION_FAILED")
            if row["artifact_family"] == _WATCHLIST_FAMILY:
                _verify_watchlist(target)
            total += size
            member_receipts.append({
                "logical_member_id": row["logical_member_id"],
                "artifact_family": row["artifact_family"],
                "backup_relative_path": relative,
                "restore_relative_path": target_relative,
                "size_bytes": size,
                "sha256": digest,
            })
        outcome = _classify(manifest, expected_manifest_sha, compatibility, contract, package)
        receipt = _make_receipt(manifest, manifest_sha256=expected_manifest_sha,
                                outcome=outcome, compatibility=compatibility,
                                restore_id=restore_id, created_at=timestamp,
                                members=member_receipts, contract=contract)
        (staging / RECEIPT_NAME).write_bytes(_canonical_bytes(receipt) + b"\n")
        verified = verify_restored_state(
            backup_path=package, restored_path=staging, compatibility=compatibility,
            contract=contract, max_total_bytes=max_total_bytes,
            max_member_count=max_member_count,
        )
        if verified["status"] != "RESTORED_STATE_VERIFIED":
            raise RestoreError("RESTORE_VERIFICATION_FAILED")
        if _source_inventory(package) != before:
            raise RestoreError("RESTORE_SOURCE_INVALID")
        os.rename(staging, final)
        return {"restore_status": "RESTORE_COMPLETED", "status": "RESTORED_STATE_VERIFIED",
                "restore_path": str(final), "restore_scope": RESTORE_SCOPE,
                "restore_id": restore_id, "backup_id": manifest["backup_id"],
                "member_count": len(member_receipts), "total_size_bytes": total}
    except RestoreError:
        raise
    except OSError as exc:
        raise RestoreError("RESTORE_VERIFICATION_FAILED") from exc


def verify_restored_state(*, backup_path: Path, restored_path: Path,
                          compatibility: CompatibilityAttestation,
                          contract: RestoreCompatibilityContract = DEFAULT_COMPATIBILITY_CONTRACT,
                          max_total_bytes: int, max_member_count: int) -> dict[str, Any]:
    """Read-only verification; compatibility is independently recomputed."""
    inspection = inspect_restore(backup_path=backup_path, compatibility=compatibility,
                                 contract=contract, max_total_bytes=max_total_bytes,
                                 max_member_count=max_member_count)
    if inspection["status"] != "DIRECT_RESTORE_COMPATIBLE":
        raise RestoreError(inspection["status"])
    root = Path(restored_path)
    try:
        backup._reject_reparse_components(root)
        resolved = root.resolve(strict=True)
        if not resolved.is_dir():
            raise RestoreError("RESTORE_TARGET_UNSAFE")
        receipt_path = resolved / RECEIPT_NAME
        if backup._is_reparse_or_symlink(receipt_path):
            raise RestoreError("RESTORE_TARGET_UNSAFE")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"), object_pairs_hook=_strict_object, parse_constant=_reject_json_constant)
    except RestoreError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RestoreError("RESTORE_VERIFICATION_FAILED") from exc
    _validate_receipt_envelope(receipt)
    if receipt.get("restore_receipt_schema_version") != RECEIPT_SCHEMA_VERSION:
        raise RestoreError("RESTORE_VERIFICATION_FAILED")
    manifest = _load_manifest(Path(backup_path).resolve(strict=True))
    if (receipt.get("backup_id") != manifest.get("backup_id")
            or receipt.get("backup_manifest_sha256") != inspection["backup_manifest_sha256"]
            or receipt.get("backup_format_version") != manifest.get("backup_format_version")
            or receipt.get("source_state_identity") != manifest.get("source_state_identity")
            or receipt.get("restore_scope") != RESTORE_SCOPE
            or receipt.get("target_contract_version") != contract.restore_contract_version
            or receipt.get("target_contract_sha256") != _contract_hash(contract)):
        raise RestoreError("RESTORE_VERIFICATION_FAILED")
    derived = _classify(manifest, inspection["backup_manifest_sha256"], compatibility, contract,
                        Path(backup_path).resolve(strict=True))
    if (receipt.get("compatibility_outcome") != derived["status"]
            or receipt.get("state_family_versions") != dict(sorted(compatibility.state_family_versions.items()))):
        raise RestoreError("RESTORE_VERIFICATION_FAILED")
    expected = manifest["members"]
    rows = receipt.get("members")
    if not isinstance(rows, list) or len(rows) != len(expected) or receipt.get("restored_member_count") != len(expected):
        raise RestoreError("RESTORE_VERIFICATION_FAILED")
    expected_files = {RECEIPT_NAME}
    expected_dirs: set[str] = set()
    total = 0
    ids: set[str] = set()
    for source_row, row in zip(expected, rows):
        if not isinstance(row, dict) or set(row) != _MEMBER_RECEIPT_FIELDS:
            raise RestoreError("RESTORE_VERIFICATION_FAILED")
        relative = _safe_relative(row.get("restore_relative_path"))
        backup_relative = _safe_relative(source_row.get("backup_relative_path"))
        if (row.get("logical_member_id") in ids
                or row.get("logical_member_id") != source_row.get("logical_member_id")
                or row.get("artifact_family") != source_row.get("artifact_family")
                or row.get("backup_relative_path") != backup_relative
                or relative != backup_relative.removeprefix("members/")
                or row.get("sha256") != source_row.get("sha256")
                or row.get("size_bytes") != source_row.get("size_bytes")):
            raise RestoreError("RESTORE_VERIFICATION_FAILED")
        ids.add(row["logical_member_id"])
        target = _verify_member_path(resolved, relative)
        size, digest = backup._hash_file(target)
        if size != row["size_bytes"] or digest != row["sha256"]:
            raise RestoreError("RESTORE_VERIFICATION_FAILED")
        if source_row["artifact_family"] == _WATCHLIST_FAMILY:
            _verify_watchlist(target)
        total += size
        if total > max_total_bytes:
            raise RestoreError("RESTORE_RESOURCE_LIMIT_EXCEEDED")
        expected_files.add(relative)
    if total != receipt.get("restored_total_bytes"):
        raise RestoreError("RESTORE_VERIFICATION_FAILED")
    actual_files: set[str] = set()
    actual_dirs: set[str] = set()
    folded: set[str] = set()
    for path in resolved.rglob("*"):
        if backup._is_reparse_or_symlink(path):
            raise RestoreError("RESTORE_TARGET_UNSAFE")
        relative = path.relative_to(resolved).as_posix()
        if relative.casefold() in folded:
            raise RestoreError("RESTORE_TARGET_UNSAFE")
        folded.add(relative.casefold())
        if path.is_file():
            actual_files.add(relative)
        elif path.is_dir():
            actual_dirs.add(relative)
    if actual_files != expected_files:
        raise RestoreError("RESTORE_VERIFICATION_FAILED")
    for file_name in expected_files:
        parent = PurePosixPath(file_name).parent
        while parent.as_posix() not in {".", ""}:
            expected_dirs.add(parent.as_posix())
            parent = parent.parent
    if actual_dirs != expected_dirs:
        raise RestoreError("RESTORE_VERIFICATION_FAILED")
    return {"status": "RESTORED_STATE_VERIFIED", "restore_scope": RESTORE_SCOPE,
            "backup_id": manifest["backup_id"], "member_count": len(expected),
            "total_size_bytes": total, "compatibility_outcome": derived["status"]}
