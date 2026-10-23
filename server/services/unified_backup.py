"""Internal, explicit-input backup package creation and read-only verification.

This is a copy/verification substrate, not restore authority. The caller supplies
bounded roots and members and attests that each is bound to the authority described
by its family. Nothing is discovered by scanning a machine or inferring file meaning
from a name. Unknown A3 families fail closed.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import stat
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Iterable, Mapping

from server.services.unified_retention_inventory import classify_artifact, classify_artifact_family


MANIFEST_NAME = "backup-manifest.json"
MANIFEST_SCHEMA_VERSION = "tw_market_backup_manifest.v1"
BACKUP_FORMAT_VERSION = "tw_market_backup.v1"
PRODUCT_IDENTITY = "tw-market-live-data-intelligence"
SELECTION_SCOPE = "EXPLICIT_DECLARED_MEMBERS_ONLY"
AUTHORITY_BINDING_MODEL = "TRUSTED_INTERNAL_CALLER_ATTESTED"
A1_SETTINGS_BINDING = "a1-installation-settings-v1"
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_SUPPORTED_TIERS = {"CORE", "FULL_GOVERNED"}
_DATA_FAMILIES = {"persistent_watchlists_and_revision_database"}
_MANIFEST_FIELDS = {
    "manifest_schema_version", "backup_format_version", "backup_id", "backup_tier",
    "created_at", "product_identity", "source_state_identity", "selection_scope",
    "authority_binding_model", "member_count", "declared_member_count",
    "total_size_bytes", "max_total_bytes", "members", "omitted_members",
    "manifest_integrity",
}
_MEMBER_FIELDS = {
    "logical_member_id", "artifact_family", "state_class", "backup_tier",
    "source_authority_id", "source_relative_path", "backup_relative_path", "source_kind",
    "size_bytes", "sha256", "integrity_binding", "replay_required", "audit_required",
}


class BackupError(RuntimeError):
    """Typed, bounded backup/verification failure."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def validate_a1_portable_settings(path: Path) -> None:
    """A1-D15 adapter: v1 endpoint preferences only; no paths or identity."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_strict_object,
                          parse_constant=_reject_json_constant)
        service = data["service"]
        if (set(data) != {"schema_version", "service"} or type(data["schema_version"]) is not int
                or data["schema_version"] != 1 or not isinstance(service, dict)
                or set(service) != {"host", "port"}
                or service["host"] not in {"127.0.0.1", "localhost", "::1"}
                or type(service["port"]) is not int or not 1 <= service["port"] <= 65535):
            raise ValueError
    except (ValueError, TypeError, KeyError, OSError) as exc:
        raise BackupError("A1_PORTABLE_SETTINGS_INVALID") from exc


@dataclass(frozen=True)
class BackupRoot:
    root_id: str
    path: Path


@dataclass(frozen=True)
class BackupMember:
    logical_member_id: str
    artifact_family: str
    source_root_id: str
    source_relative_path: str
    backup_relative_path: str
    authority_binding_id: str
    authority_binding_verified: bool
    governed_reference_absent_verified: bool = False
    expected_sha256: str | None = None
    source_kind: str = "file"  # "sqlite" only for the A3 Watchlist database family.


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _reject_json_constant(value: str) -> None:
    raise BackupError("BACKUP_MANIFEST_INVALID")


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise BackupError("BACKUP_MANIFEST_INVALID")
        result[key] = value
    return result


def _manifest_hash(manifest: Mapping[str, Any]) -> str:
    payload = dict(manifest)
    payload.pop("manifest_integrity", None)
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _is_reparse_or_symlink(path: Path) -> bool:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return path.is_symlink() or bool(getattr(info, "st_file_attributes", 0) & 0x400)


def _reject_reparse_components(path: Path, *, allow_missing_leaf: bool = False) -> None:
    absolute = Path(os.path.abspath(path))
    parts = [Path(absolute.anchor)]
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current = current / part
        parts.append(current)
    for index, item in enumerate(parts):
        if allow_missing_leaf and index == len(parts) - 1 and not item.exists():
            continue
        if _is_reparse_or_symlink(item):
            raise BackupError("BACKUP_PATH_UNSAFE")


def _relative(value: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value or "\\" in value:
        raise BackupError("BACKUP_PATH_UNSAFE")
    if value.startswith("/") or re.match(r"^[A-Za-z]:", value) or value.startswith("//"):
        raise BackupError("BACKUP_PATH_UNSAFE")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise BackupError("BACKUP_PATH_UNSAFE")
    reserved = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
    if any(
        ":" in part or part.endswith((".", " ")) or part.split(".", 1)[0].upper() in reserved
        for part in parts
    ):
        raise BackupError("BACKUP_PATH_UNSAFE")
    normalized = PurePosixPath(*parts).as_posix()
    if normalized != value:
        raise BackupError("BACKUP_PATH_UNSAFE")
    return normalized


def _contained_file(root: Path, relative_path: str) -> Path:
    relative = _relative(relative_path)
    candidate = root.joinpath(*relative.split("/"))
    _reject_reparse_components(root)
    current = root
    for part in relative.split("/"):
        current = current / part
        if _is_reparse_or_symlink(current):
            raise BackupError("BACKUP_PATH_UNSAFE")
    try:
        resolved = candidate.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise BackupError("BACKUP_MEMBER_MISSING") from exc
    if root.resolve(strict=True) not in resolved.parents or not resolved.is_file():
        raise BackupError("BACKUP_PATH_UNSAFE")
    return candidate


def _source_signature(path: Path) -> tuple[int, int, int, int]:
    info = path.stat(follow_symlinks=False)
    if not stat.S_ISREG(info.st_mode) or _is_reparse_or_symlink(path):
        raise BackupError("BACKUP_PATH_UNSAFE")
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)


def _verify_binding(member: BackupMember) -> dict[str, Any]:
    if not isinstance(member.logical_member_id, str) or not _ID_RE.fullmatch(member.logical_member_id) or not isinstance(member.authority_binding_id, str) or not _ID_RE.fullmatch(member.authority_binding_id):
        raise BackupError("BACKUP_MANIFEST_INVALID")
    family = classify_artifact(
        artifact_family=member.artifact_family,
        authority_binding_verified=member.authority_binding_verified is True,
        governed_reference_found=False if member.governed_reference_absent_verified is True else None,
    )
    if family["state_class"] == "UNCLASSIFIED_REQUIRES_POLICY":
        raise BackupError("UNCLASSIFIED_SOURCE_STATE")
    if member.source_kind not in {"file", "sqlite"}:
        raise BackupError("BACKUP_MANIFEST_INVALID")
    if member.source_kind == "sqlite" and member.artifact_family not in _DATA_FAMILIES:
        raise BackupError("BACKUP_CLASSIFICATION_MISMATCH")
    return family


def _validate_roots(roots: Iterable[BackupRoot]) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for root in roots:
        if not isinstance(root.root_id, str) or not _ID_RE.fullmatch(root.root_id) or root.root_id in result:
            raise BackupError("BACKUP_MANIFEST_INVALID")
        path = Path(root.path)
        _reject_reparse_components(path)
        try:
            resolved = path.resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            raise BackupError("BACKUP_PATH_UNSAFE") from exc
        if not resolved.is_dir():
            raise BackupError("BACKUP_PATH_UNSAFE")
        result[root.root_id] = resolved
    if not result:
        raise BackupError("BACKUP_MANIFEST_INVALID")
    values = list(result.values())
    for i, left in enumerate(values):
        for right in values[i + 1:]:
            if left == right or left in right.parents or right in left.parents:
                raise BackupError("BACKUP_PATH_UNSAFE")
    return result


def _selected_for_tier(family_tier: str, requested_tier: str, include_derived: bool) -> tuple[bool, str | None]:
    if family_tier in {"NONE", "UNDETERMINED"}:
        return False, "OUTSIDE_BACKUP_BOUNDARY" if family_tier == "NONE" else "UNCLASSIFIED_REQUIRES_POLICY"
    if family_tier == "DERIVED":
        return (include_derived, None if include_derived else "DERIVED_OMITTED_BY_POLICY")
    if requested_tier == "CORE":
        return family_tier == "CORE", None if family_tier == "CORE" else "NOT_IN_CORE_TIER"
    if requested_tier == "FULL_GOVERNED":
        return family_tier in {"CORE", "FULL_GOVERNED"}, None if family_tier in {"CORE", "FULL_GOVERNED"} else "NOT_IN_FULL_GOVERNED_TIER"
    raise BackupError("BACKUP_MANIFEST_INVALID")


def _verify_watchlist_database(path: Path) -> None:
    """Reuse Watchlist integrity checks with a strictly read-only SQLite connection."""
    from scripts.m8r_09_persistent_watchlists import PersistentWatchlistStore, WatchlistError

    store = object.__new__(PersistentWatchlistStore)
    store.path = path

    def connect_read_only() -> sqlite3.Connection:
        connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, timeout=0.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=5000")
        return connection

    store._connect = connect_read_only
    try:
        result = store.verify_integrity()
    except WatchlistError as exc:
        raise BackupError("BACKUP_CLASSIFICATION_MISMATCH") from exc
    if result.get("status") != "PASS" or result.get("schema_version") != 1:
        raise BackupError("BACKUP_CLASSIFICATION_MISMATCH")


def _sqlite_logical_fingerprint(connection: sqlite3.Connection) -> str:
    """Hash schema and table contents independent of SQLite file page layout."""
    schema = list(connection.execute(
        "SELECT type, name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"
    ))
    payload: list[dict[str, Any]] = []
    for kind, name, definition in schema:
        if kind != "table":
            payload.append({"type": kind, "name": name, "sql": definition})
            continue
        safe_name = str(name).replace('"', '""')
        rows = []
        for row in connection.execute(f'SELECT * FROM "{safe_name}"'):
            normalized = [
                {"bytes_hex": value.hex()} if isinstance(value, bytes) else value
                for value in row
            ]
            rows.append(_canonical_bytes(normalized).decode("utf-8"))
        payload.append({"type": kind, "name": name, "sql": definition, "rows": sorted(rows)})
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _sqlite_snapshot_fingerprint(source: Path, max_bytes: int) -> tuple[int, str]:
    """Fingerprint a consistent in-memory SQLite snapshot without writing source state."""
    uri = source.resolve().as_uri() + "?mode=ro"
    try:
        source_db = sqlite3.connect(uri, uri=True, timeout=0.0)
        snapshot_db = sqlite3.connect(":memory:")
        try:
            page_count = source_db.execute("PRAGMA page_count").fetchone()[0]
            page_size = source_db.execute("PRAGMA page_size").fetchone()[0]
            if page_count * page_size > max_bytes:
                raise BackupError("BACKUP_RESOURCE_LIMIT_EXCEEDED")
            version_before = source_db.execute("PRAGMA data_version").fetchone()[0]
            if source_db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise BackupError("BACKUP_CLASSIFICATION_MISMATCH")
            _verify_watchlist_database(source)
            source_db.backup(snapshot_db, pages=256, sleep=0.01)
            if snapshot_db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise BackupError("BACKUP_CLASSIFICATION_MISMATCH")
            version_after = source_db.execute("PRAGMA data_version").fetchone()[0]
            if version_after != version_before:
                raise BackupError("SOURCE_CHANGED_DURING_BACKUP")
            snapshot_size = len(snapshot_db.serialize())
            if snapshot_size > max_bytes:
                raise BackupError("BACKUP_RESOURCE_LIMIT_EXCEEDED")
            return snapshot_size, _sqlite_logical_fingerprint(snapshot_db)
        finally:
            snapshot_db.close()
            source_db.close()
    except BackupError:
        raise
    except sqlite3.Error as exc:
        raise BackupError("SOURCE_CHANGED_DURING_BACKUP") from exc


def plan_backup(
    *,
    backup_tier: str,
    roots: Iterable[BackupRoot],
    members: Iterable[BackupMember],
    source_state_identity: str,
    max_total_bytes: int,
    include_derived: bool = False,
) -> dict[str, Any]:
    """Plan a backup from explicit roots and members; never scans a source root."""
    if not isinstance(backup_tier, str) or backup_tier not in _SUPPORTED_TIERS or not isinstance(source_state_identity, str) or not _ID_RE.fullmatch(source_state_identity):
        raise BackupError("BACKUP_MANIFEST_INVALID")
    if not isinstance(max_total_bytes, int) or isinstance(max_total_bytes, bool) or max_total_bytes <= 0:
        raise BackupError("BACKUP_MANIFEST_INVALID")
    root_map = _validate_roots(roots)
    rows = list(members)
    if not rows:
        raise BackupError("BACKUP_MANIFEST_INVALID")
    logical_ids: set[str] = set()
    backup_paths: dict[str, str] = {}
    folded_paths: dict[str, str] = {}
    selected: list[dict[str, Any]] = []
    omitted: list[dict[str, str]] = []
    total = 0
    for member in rows:
        if not isinstance(member, BackupMember):
            raise BackupError("BACKUP_MANIFEST_INVALID")
        if not isinstance(member.logical_member_id, str) or not _ID_RE.fullmatch(member.logical_member_id):
            raise BackupError("BACKUP_MANIFEST_INVALID")
        if member.logical_member_id in logical_ids:
            raise BackupError("BACKUP_MANIFEST_INVALID")
        logical_ids.add(member.logical_member_id)
        source_relative = _relative(member.source_relative_path)
        backup_relative = _relative(member.backup_relative_path)
        if backup_relative == MANIFEST_NAME or backup_relative.startswith("members/") is False:
            raise BackupError("BACKUP_PATH_UNSAFE")
        if member.source_root_id not in root_map:
            raise BackupError("BACKUP_PATH_UNSAFE")
        if backup_relative in backup_paths or backup_relative.casefold() in folded_paths:
            raise BackupError("BACKUP_MANIFEST_INVALID")
        for existing in backup_paths:
            if backup_relative.startswith(existing + "/") or existing.startswith(backup_relative + "/"):
                raise BackupError("BACKUP_MANIFEST_INVALID")
        backup_paths[backup_relative] = member.logical_member_id
        folded_paths[backup_relative.casefold()] = backup_relative
        if member.artifact_family == "user_product_settings" and not (
                member.authority_binding_verified and member.authority_binding_id == A1_SETTINGS_BINDING):
            # A3 records no established current settings store. Preserve that
            # explicit absence in the plan without accepting a claimed source.
            family = classify_artifact_family(member.artifact_family)
            include, reason = False, "NO_CURRENT_CANONICAL_AUTHORITY"
        else:
            family = _verify_binding(member)
            include, reason = _selected_for_tier(family["backup_tier"], backup_tier, include_derived)
        if not include:
            omitted.append({"logical_member_id": member.logical_member_id, "artifact_family": member.artifact_family, "disposition": reason or "OMITTED"})
            continue
        source = _contained_file(root_map[member.source_root_id], source_relative)
        if member.artifact_family == "user_product_settings":
            validate_a1_portable_settings(source)
        signature = _source_signature(source)
        remaining_bytes = max_total_bytes - total
        if remaining_bytes <= 0:
            raise BackupError("BACKUP_RESOURCE_LIMIT_EXCEEDED")
        if member.source_kind == "file":
            if signature[2] > remaining_bytes:
                raise BackupError("BACKUP_RESOURCE_LIMIT_EXCEEDED")
            if not isinstance(member.expected_sha256, str) or not _HASH_RE.fullmatch(member.expected_sha256):
                raise BackupError("BACKUP_MANIFEST_INVALID")
            size, source_digest = _hash_file(source)
            if _source_signature(source) != signature:
                raise BackupError("SOURCE_CHANGED_DURING_BACKUP")
            if size != signature[2] or source_digest != member.expected_sha256:
                raise BackupError("BACKUP_CLASSIFICATION_MISMATCH")
        else:
            snapshot_size, snapshot_hash = _sqlite_snapshot_fingerprint(source, remaining_bytes)
            if snapshot_size > remaining_bytes:
                raise BackupError("BACKUP_RESOURCE_LIMIT_EXCEEDED")
            member_expected_hash = snapshot_hash
            size = snapshot_size
        total += size
        if total > max_total_bytes:
            raise BackupError("BACKUP_RESOURCE_LIMIT_EXCEEDED")
        if member.source_kind == "sqlite" and source.name != "watchlists.sqlite3":
            raise BackupError("BACKUP_CLASSIFICATION_MISMATCH")
        selected.append({
            "logical_member_id": member.logical_member_id,
            "artifact_family": member.artifact_family,
            "state_class": family["state_class"],
            "backup_tier": family["backup_tier"],
            "source_root_id": member.source_root_id,
            "source_relative_path": source_relative,
            "backup_relative_path": backup_relative,
            "source_kind": member.source_kind,
            "authority_binding_id": member.authority_binding_id,
            "expected_sha256": member.expected_sha256 if member.source_kind == "file" else member_expected_hash,
            "authority_binding_verified": True,
            "governed_reference_absent_verified": member.governed_reference_absent_verified,
            "integrity_binding": family["integrity_binding"],
            "replay_required": family["replay_required"],
            "audit_required": family["audit_required"],
            "planned_size_bytes": size,
            "planned_source_signature": signature,
        })
    selected.sort(key=lambda row: (row["backup_relative_path"], row["logical_member_id"]))
    return {
        "backup_tier": backup_tier,
        "product_identity": PRODUCT_IDENTITY,
        "source_state_identity": source_state_identity,
        "members": selected,
        "omitted_members": sorted(omitted, key=lambda row: row["logical_member_id"]),
        "planned_total_bytes": total,
        "max_total_bytes": max_total_bytes,
        "include_derived": include_derived,
        "_root_bindings": {key: str(value) for key, value in root_map.items()},
    }


def _read_source_bytes(source: Path, expected_signature: tuple[int, int, int, int]) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(source, flags)
        with os.fdopen(fd, "rb") as handle:
            before = os.fstat(handle.fileno())
            before_signature = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
            if before_signature != expected_signature:
                raise BackupError("SOURCE_CHANGED_DURING_BACKUP")
            chunks: list[bytes] = []
            digest_size = 1024 * 1024
            while True:
                chunk = handle.read(digest_size)
                if not chunk:
                    break
                chunks.append(chunk)
            after = os.fstat(handle.fileno())
            after_signature = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
            if after_signature != before_signature or _source_signature(source) != before_signature:
                raise BackupError("SOURCE_CHANGED_DURING_BACKUP")
            return b"".join(chunks)
    except BackupError:
        raise
    except OSError as exc:
        raise BackupError("BACKUP_MEMBER_MISSING") from exc


def _sqlite_snapshot(source: Path, destination: Path, max_bytes: int) -> tuple[int, str]:
    uri = source.resolve().as_uri() + "?mode=ro"
    try:
        source_db = sqlite3.connect(uri, uri=True, timeout=0.0)
        try:
            page_count = source_db.execute("PRAGMA page_count").fetchone()[0]
            page_size = source_db.execute("PRAGMA page_size").fetchone()[0]
            if page_count * page_size > max_bytes:
                raise BackupError("BACKUP_RESOURCE_LIMIT_EXCEEDED")
            version_before = source_db.execute("PRAGMA data_version").fetchone()[0]
            integrity = source_db.execute("PRAGMA integrity_check").fetchone()[0]
            if integrity != "ok":
                raise BackupError("BACKUP_CLASSIFICATION_MISMATCH")
            _verify_watchlist_database(source)
            target_db = sqlite3.connect(destination)
            try:
                source_db.backup(target_db, pages=256, sleep=0.01)
                target_integrity = target_db.execute("PRAGMA integrity_check").fetchone()[0]
                if target_integrity != "ok":
                    raise BackupError("BACKUP_CLASSIFICATION_MISMATCH")
                _verify_watchlist_database(destination)
                snapshot_size = len(target_db.serialize())
                if snapshot_size > max_bytes:
                    raise BackupError("BACKUP_RESOURCE_LIMIT_EXCEEDED")
                snapshot_fingerprint = (snapshot_size, _sqlite_logical_fingerprint(target_db))
            finally:
                target_db.close()
            version_after = source_db.execute("PRAGMA data_version").fetchone()[0]
            if version_after != version_before:
                raise BackupError("SOURCE_CHANGED_DURING_BACKUP")
            return snapshot_fingerprint
        finally:
            source_db.close()
    except BackupError:
        raise
    except sqlite3.Error as exc:
        raise BackupError("SOURCE_CHANGED_DURING_BACKUP") from exc


def _hash_file(path: Path) -> tuple[int, str]:
    before = _source_signature(path)
    digest = hashlib.sha256()
    size = 0
    try:
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(path, flags)
        with os.fdopen(fd, "rb") as handle:
            opened = os.fstat(handle.fileno())
            if (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns) != before:
                raise BackupError("BACKUP_MEMBER_HASH_MISMATCH")
            while True:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                digest.update(chunk)
            finished = os.fstat(handle.fileno())
            after = (finished.st_dev, finished.st_ino, finished.st_size, finished.st_mtime_ns)
            if after != before or _source_signature(path) != before:
                raise BackupError("BACKUP_MEMBER_HASH_MISMATCH")
    except BackupError:
        raise
    except OSError as exc:
        raise BackupError("BACKUP_MEMBER_MISSING") from exc
    return size, digest.hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(_canonical_bytes(value) + b"\n")
        handle.flush()
        os.fsync(handle.fileno())


def _manifest_for(plan: Mapping[str, Any], *, backup_id: str, created_at: str, member_rows: list[dict[str, Any]], total_size_bytes: int) -> dict[str, Any]:
    manifest: dict[str, Any] = {
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "backup_format_version": BACKUP_FORMAT_VERSION,
        "backup_id": backup_id,
        "backup_tier": plan["backup_tier"],
        "created_at": created_at,
        "product_identity": PRODUCT_IDENTITY,
        "source_state_identity": plan["source_state_identity"],
        "selection_scope": SELECTION_SCOPE,
        "authority_binding_model": AUTHORITY_BINDING_MODEL,
        "member_count": len(member_rows),
        "declared_member_count": len(member_rows) + len(plan["omitted_members"]),
        "total_size_bytes": total_size_bytes,
        "max_total_bytes": plan["max_total_bytes"],
        "members": member_rows,
        "omitted_members": plan["omitted_members"],
        "manifest_integrity": {"algorithm": "SHA-256", "coverage": "canonical UTF-8 JSON excluding manifest_integrity", "sha256": ""},
    }
    manifest["manifest_integrity"]["sha256"] = _manifest_hash(manifest)
    return manifest


def create_backup(
    plan: Mapping[str, Any],
    *,
    destination: Path,
    backup_id: str,
    created_at: str,
    now: Callable[[], str] | None = None,
) -> dict[str, Any]:
    """Copy the exact planned bytes into a new staged package, verify, then finalize."""
    if not _ID_RE.fullmatch(backup_id):
        raise BackupError("BACKUP_MANIFEST_INVALID")
    timestamp = created_at if now is None else now()
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except (ValueError, AttributeError) as exc:
        raise BackupError("BACKUP_MANIFEST_INVALID") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise BackupError("BACKUP_MANIFEST_INVALID")
    final_path = Path(os.path.abspath(destination))
    _relative(final_path.name)
    _reject_reparse_components(final_path.parent)
    # Plans carry roots only as internal execution bindings. These values are never
    # serialized into the portable manifest.
    root_bindings = plan.get("_root_bindings")
    if not isinstance(root_bindings, Mapping):
        raise BackupError("BACKUP_MANIFEST_INVALID")
    if not final_path.parent.is_dir():
        raise BackupError("BACKUP_PATH_UNSAFE")
    for root_value in root_bindings.values():
        root_input = Path(root_value)
        _reject_reparse_components(root_input)
        root = root_input.resolve(strict=True)
        if final_path == root or root in final_path.parents or final_path in root.parents:
            raise BackupError("BACKUP_PATH_UNSAFE")
    if os.path.lexists(final_path):
        raise BackupError("BACKUP_DESTINATION_EXISTS")
    _validate_manifest_plan(plan)
    staging = final_path.parent / f".{final_path.name}.staging-{backup_id}"
    if os.path.lexists(staging):
        raise BackupError("BACKUP_DESTINATION_EXISTS")
    try:
        staging.mkdir(parents=False, exist_ok=False)
    except FileExistsError as exc:
        raise BackupError("BACKUP_DESTINATION_EXISTS") from exc
    except OSError as exc:
        raise BackupError("BACKUP_DESTINATION_FAILED") from exc
    try:
        manifest_members: list[dict[str, Any]] = []
        actual_total_bytes = 0
        for row in plan["members"]:
            source_root = Path(root_bindings[row["source_root_id"]]).resolve(strict=True)
            source = _contained_file(source_root, row["source_relative_path"])
            expected_signature = tuple(row["planned_source_signature"])
            if _source_signature(source) != expected_signature:
                raise BackupError("SOURCE_CHANGED_DURING_BACKUP")
            relative = _relative(row["backup_relative_path"])
            target = staging.joinpath(*relative.split("/"))
            target.parent.mkdir(parents=True, exist_ok=True)
            if row["source_kind"] == "sqlite":
                remaining_bytes = plan["max_total_bytes"] - actual_total_bytes
                if remaining_bytes <= 0:
                    raise BackupError("BACKUP_RESOURCE_LIMIT_EXCEEDED")
                snapshot_size, snapshot_digest = _sqlite_snapshot(source, target, remaining_bytes)
                if snapshot_size != row["planned_size_bytes"] or snapshot_digest != row["expected_sha256"]:
                    raise BackupError("SOURCE_CHANGED_DURING_BACKUP")
                if _source_signature(source) != expected_signature:
                    raise BackupError("SOURCE_CHANGED_DURING_BACKUP")
            else:
                data = _read_source_bytes(source, expected_signature)
                if len(data) > plan["max_total_bytes"]:
                    raise BackupError("BACKUP_RESOURCE_LIMIT_EXCEEDED")
                if hashlib.sha256(data).hexdigest() != row["expected_sha256"]:
                    raise BackupError("SOURCE_CHANGED_DURING_BACKUP")
                with target.open("xb") as handle:
                    handle.write(data)
                    handle.flush()
                    os.fsync(handle.fileno())
                if hashlib.sha256(data).hexdigest() != _hash_file(target)[1]:
                    raise BackupError("BACKUP_MEMBER_HASH_MISMATCH")
                if _source_signature(source) != expected_signature:
                    raise BackupError("SOURCE_CHANGED_DURING_BACKUP")
            size, digest = _hash_file(target)
            actual_total_bytes += size
            if actual_total_bytes > plan["max_total_bytes"]:
                raise BackupError("BACKUP_RESOURCE_LIMIT_EXCEEDED")
            manifest_members.append({
                key: row[key] for key in (
                    "logical_member_id", "artifact_family", "state_class", "backup_tier",
                    "source_relative_path", "backup_relative_path", "integrity_binding",
                    "replay_required", "audit_required",
                )
            } | {"source_authority_id": row["authority_binding_id"], "source_kind": row["source_kind"], "size_bytes": size, "sha256": digest})
        manifest = _manifest_for(plan, backup_id=backup_id, created_at=timestamp, member_rows=manifest_members, total_size_bytes=actual_total_bytes)
        _write_json(staging / MANIFEST_NAME, manifest)
        verified = _verify_backup(staging, allow_staging=True, max_total_bytes=plan["max_total_bytes"])
        if verified["status"] != "BACKUP_VERIFIED":
            raise BackupError(verified["status"])
        try:
            os.rename(staging, final_path)
        except FileExistsError as exc:
            raise BackupError("BACKUP_DESTINATION_EXISTS") from exc
        return {"status": "BACKUP_CREATED", "backup_path": str(final_path), "backup_id": backup_id, "manifest_sha256": manifest["manifest_integrity"]["sha256"], "member_count": len(manifest_members), "omitted_members": manifest["omitted_members"]}
    except BackupError:
        # Staging remains visibly non-final and is never confused with the requested
        # destination package. It contains no source-state mutation.
        raise
    except OSError as exc:
        raise BackupError("BACKUP_DESTINATION_FAILED") from exc


def _validate_manifest_plan(plan: Mapping[str, Any]) -> None:
    if plan.get("backup_tier") not in _SUPPORTED_TIERS or plan.get("product_identity") != PRODUCT_IDENTITY:
        raise BackupError("BACKUP_MANIFEST_INVALID")
    if not isinstance(plan.get("source_state_identity"), str) or not _ID_RE.fullmatch(plan["source_state_identity"]):
        raise BackupError("BACKUP_MANIFEST_INVALID")
    if not isinstance(plan.get("max_total_bytes"), int) or isinstance(plan.get("max_total_bytes"), bool) or plan["max_total_bytes"] <= 0:
        raise BackupError("BACKUP_MANIFEST_INVALID")
    if not isinstance(plan.get("_root_bindings"), Mapping) or not plan["_root_bindings"]:
        raise BackupError("BACKUP_MANIFEST_INVALID")
    members = plan.get("members")
    if not isinstance(members, list) or not members:
        raise BackupError("BACKUP_MANIFEST_INVALID")
    ids: set[str] = set()
    paths: set[str] = set()
    folded: set[str] = set()
    planned_total = 0
    for row in members:
        if not isinstance(row, Mapping):
            raise BackupError("BACKUP_MANIFEST_INVALID")
        if row.get("logical_member_id") in ids:
            raise BackupError("BACKUP_MANIFEST_INVALID")
        ids.add(row.get("logical_member_id"))
        if row.get("source_root_id") not in plan["_root_bindings"]:
            raise BackupError("BACKUP_PATH_UNSAFE")
        _relative(row.get("source_relative_path"))
        path = _relative(row.get("backup_relative_path"))
        if not path.startswith("members/"):
            raise BackupError("BACKUP_PATH_UNSAFE")
        if path in paths or path.casefold() in folded:
            raise BackupError("BACKUP_MANIFEST_INVALID")
        if any(path.startswith(existing + "/") or existing.startswith(path + "/") for existing in paths):
            raise BackupError("BACKUP_MANIFEST_INVALID")
        paths.add(path)
        folded.add(path.casefold())
        if row.get("state_class") == "UNCLASSIFIED_REQUIRES_POLICY" or row.get("backup_tier") == "UNDETERMINED":
            raise BackupError("UNCLASSIFIED_SOURCE_STATE")
        policy = classify_artifact(
            artifact_family=row.get("artifact_family"),
            authority_binding_verified=row.get("authority_binding_verified") is True,
            governed_reference_found=False if row.get("governed_reference_absent_verified") is True else None,
        )
        if policy["state_class"] == "UNCLASSIFIED_REQUIRES_POLICY":
            raise BackupError("UNCLASSIFIED_SOURCE_STATE")
        include, _ = _selected_for_tier(policy["backup_tier"], plan["backup_tier"], plan.get("include_derived") is True)
        if not include:
            raise BackupError("BACKUP_CLASSIFICATION_MISMATCH")
        if row.get("artifact_family") == "user_product_settings":
            if row.get("authority_binding_id") != A1_SETTINGS_BINDING:
                raise BackupError("BACKUP_CLASSIFICATION_MISMATCH")
            validate_a1_portable_settings(_contained_file(Path(plan["_root_bindings"][row["source_root_id"]]), row["source_relative_path"]))
        for key in ("state_class", "backup_tier", "integrity_binding", "replay_required", "audit_required"):
            if row.get(key) != policy[key]:
                raise BackupError("BACKUP_CLASSIFICATION_MISMATCH")
        if row.get("source_kind") not in {"file", "sqlite"}:
            raise BackupError("BACKUP_MANIFEST_INVALID")
        if row["source_kind"] == "sqlite" and row.get("artifact_family") not in _DATA_FAMILIES:
            raise BackupError("BACKUP_CLASSIFICATION_MISMATCH")
        if row["source_kind"] == "file" and not _HASH_RE.fullmatch(str(row.get("expected_sha256", ""))):
            raise BackupError("BACKUP_MANIFEST_INVALID")
        if not isinstance(row.get("planned_size_bytes"), int) or row["planned_size_bytes"] < 0:
            raise BackupError("BACKUP_MANIFEST_INVALID")
        planned_total += row["planned_size_bytes"]
    if planned_total > plan["max_total_bytes"]:
        raise BackupError("BACKUP_RESOURCE_LIMIT_EXCEEDED")


def verify_backup(backup_path: Path, *, max_total_bytes: int) -> dict[str, Any]:
    """Verify a finalized package without writes, repair, restore, or source access."""
    return _verify_backup(backup_path, allow_staging=False, max_total_bytes=max_total_bytes)


def _verify_backup(backup_path: Path, *, allow_staging: bool, max_total_bytes: int) -> dict[str, Any]:
    if not isinstance(max_total_bytes, int) or isinstance(max_total_bytes, bool) or max_total_bytes <= 0:
        raise BackupError("BACKUP_MANIFEST_INVALID")
    root = Path(backup_path)
    if not allow_staging and ".staging-" in root.name:
        raise BackupError("BACKUP_MANIFEST_INVALID")
    try:
        _reject_reparse_components(root)
        package = root.resolve(strict=True)
        if not package.is_dir():
            raise BackupError("BACKUP_PATH_UNSAFE")
        manifest_path = package / MANIFEST_NAME
        if _is_reparse_or_symlink(manifest_path) or not manifest_path.is_file():
            raise BackupError("BACKUP_MANIFEST_INVALID")
        manifest = json.loads(
            manifest_path.read_text(encoding="utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_json_constant,
        )
    except BackupError:
        raise
    except FileNotFoundError as exc:
        raise BackupError("BACKUP_MANIFEST_INVALID") from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BackupError("BACKUP_MANIFEST_INVALID") from exc
    if not isinstance(manifest, dict) or manifest.get("manifest_schema_version") != MANIFEST_SCHEMA_VERSION or manifest.get("backup_format_version") != BACKUP_FORMAT_VERSION:
        raise BackupError("BACKUP_UNSUPPORTED_VERSION")
    if set(manifest) != _MANIFEST_FIELDS:
        raise BackupError("BACKUP_MANIFEST_INVALID")
    if manifest.get("product_identity") != PRODUCT_IDENTITY or not isinstance(manifest.get("backup_tier"), str) or manifest.get("backup_tier") not in _SUPPORTED_TIERS:
        raise BackupError("BACKUP_MANIFEST_INVALID")
    if manifest.get("selection_scope") != SELECTION_SCOPE or manifest.get("authority_binding_model") != AUTHORITY_BINDING_MODEL:
        raise BackupError("BACKUP_MANIFEST_INVALID")
    if not isinstance(manifest.get("backup_id"), str) or not _ID_RE.fullmatch(manifest["backup_id"]):
        raise BackupError("BACKUP_MANIFEST_INVALID")
    if not isinstance(manifest.get("source_state_identity"), str) or not _ID_RE.fullmatch(manifest["source_state_identity"]):
        raise BackupError("BACKUP_MANIFEST_INVALID")
    if not isinstance(manifest.get("total_size_bytes"), int) or isinstance(manifest["total_size_bytes"], bool) or manifest["total_size_bytes"] < 0:
        raise BackupError("BACKUP_MANIFEST_INVALID")
    if not isinstance(manifest.get("max_total_bytes"), int) or isinstance(manifest["max_total_bytes"], bool) or manifest["max_total_bytes"] <= 0:
        raise BackupError("BACKUP_MANIFEST_INVALID")
    if manifest["max_total_bytes"] > max_total_bytes or manifest["total_size_bytes"] > max_total_bytes:
        raise BackupError("BACKUP_RESOURCE_LIMIT_EXCEEDED")
    try:
        created_at = datetime.fromisoformat(str(manifest.get("created_at", "")).replace("Z", "+00:00"))
    except ValueError as exc:
        raise BackupError("BACKUP_MANIFEST_INVALID") from exc
    if created_at.tzinfo is None or created_at.utcoffset() != timezone.utc.utcoffset(created_at):
        raise BackupError("BACKUP_MANIFEST_INVALID")
    integrity = manifest.get("manifest_integrity")
    if not isinstance(integrity, dict) or integrity.get("algorithm") != "SHA-256" or integrity.get("coverage") != "canonical UTF-8 JSON excluding manifest_integrity" or not _HASH_RE.fullmatch(str(integrity.get("sha256", ""))):
        raise BackupError("BACKUP_MANIFEST_INVALID")
    if integrity["sha256"] != _manifest_hash(manifest):
        raise BackupError("BACKUP_MANIFEST_INVALID")
    members = manifest.get("members")
    if not isinstance(members, list) or isinstance(manifest.get("member_count"), bool) or manifest.get("member_count") != len(members) or not members:
        raise BackupError("BACKUP_MANIFEST_INVALID")
    if any(not isinstance(row, dict) for row in members):
        raise BackupError("BACKUP_MANIFEST_INVALID")
    if members != sorted(members, key=lambda row: (row.get("backup_relative_path", ""), row.get("logical_member_id", ""))):
        raise BackupError("BACKUP_MANIFEST_INVALID")
    logical_ids: set[str] = set()
    member_paths: set[str] = set()
    folded: set[str] = set()
    expected_files = {MANIFEST_NAME}
    verified_total_bytes = 0
    for item in members:
        if not isinstance(item, dict):
            raise BackupError("BACKUP_MANIFEST_INVALID")
        if set(item) != _MEMBER_FIELDS:
            raise BackupError("BACKUP_MANIFEST_INVALID")
        logical_id, family_name = item.get("logical_member_id"), item.get("artifact_family")
        if not isinstance(family_name, str):
            raise BackupError("BACKUP_MANIFEST_INVALID")
        if not isinstance(logical_id, str) or not _ID_RE.fullmatch(logical_id) or logical_id in logical_ids:
            raise BackupError("BACKUP_MANIFEST_INVALID")
        logical_ids.add(logical_id)
        if not isinstance(item.get("source_authority_id"), str) or not _ID_RE.fullmatch(item["source_authority_id"]):
            raise BackupError("BACKUP_MANIFEST_INVALID")
        _relative(item.get("source_relative_path"))
        if item.get("source_kind") not in {"file", "sqlite"}:
            raise BackupError("BACKUP_MANIFEST_INVALID")
        relative = _relative(item.get("backup_relative_path"))
        if not relative.startswith("members/") or relative in member_paths or relative.casefold() in folded:
            raise BackupError("BACKUP_PATH_UNSAFE")
        if any(relative.startswith(existing + "/") or existing.startswith(relative + "/") for existing in member_paths):
            raise BackupError("BACKUP_PATH_UNSAFE")
        member_paths.add(relative)
        folded.add(relative.casefold())
        family = classify_artifact(artifact_family=family_name, authority_binding_verified=True, governed_reference_found=False)
        if family["state_class"] == "UNCLASSIFIED_REQUIRES_POLICY":
            raise BackupError("UNCLASSIFIED_SOURCE_STATE")
        selected, _ = _selected_for_tier(family["backup_tier"], manifest["backup_tier"], include_derived=True)
        if not selected or item.get("state_class") != family["state_class"] or item.get("backup_tier") != family["backup_tier"]:
            raise BackupError("BACKUP_CLASSIFICATION_MISMATCH")
        for field in ("integrity_binding", "replay_required", "audit_required"):
            if item.get(field) != family[field]:
                raise BackupError("BACKUP_CLASSIFICATION_MISMATCH")
        if not isinstance(item.get("size_bytes"), int) or isinstance(item.get("size_bytes"), bool) or item["size_bytes"] < 0 or not _HASH_RE.fullmatch(str(item.get("sha256", ""))):
            raise BackupError("BACKUP_MANIFEST_INVALID")
        target = _contained_file(package, relative)
        if family_name == "user_product_settings":
            if item["source_authority_id"] != A1_SETTINGS_BINDING:
                raise BackupError("BACKUP_CLASSIFICATION_MISMATCH")
            validate_a1_portable_settings(target)
        actual_size = _source_signature(target)[2]
        if actual_size != item["size_bytes"]:
            raise BackupError("BACKUP_MEMBER_SIZE_MISMATCH")
        if actual_size > max_total_bytes - verified_total_bytes:
            raise BackupError("BACKUP_RESOURCE_LIMIT_EXCEEDED")
        size, digest = _hash_file(target)
        verified_total_bytes += size
        if digest != item["sha256"]:
            raise BackupError("BACKUP_MEMBER_HASH_MISMATCH")
        expected_files.add(relative)
    actual_files: set[str] = set()
    actual_directories: set[str] = set()
    for path in package.rglob("*"):
        if _is_reparse_or_symlink(path):
            raise BackupError("BACKUP_PATH_UNSAFE")
        if path.is_file():
            actual_files.add(path.relative_to(package).as_posix())
        elif path.is_dir():
            actual_directories.add(path.relative_to(package).as_posix())
    if actual_files - expected_files:
        raise BackupError("BACKUP_MEMBER_UNEXPECTED")
    if expected_files - actual_files:
        raise BackupError("BACKUP_MEMBER_MISSING")
    if verified_total_bytes != manifest["total_size_bytes"]:
        raise BackupError("BACKUP_MEMBER_SIZE_MISMATCH")
    expected_directories: set[str] = set()
    for file_name in expected_files:
        parent = PurePosixPath(file_name).parent
        while parent.as_posix() not in {".", ""}:
            expected_directories.add(parent.as_posix())
            parent = parent.parent
    if actual_directories - expected_directories:
        raise BackupError("BACKUP_MEMBER_UNEXPECTED")
    omissions = manifest.get("omitted_members", [])
    if not isinstance(omissions, list) or isinstance(manifest.get("declared_member_count"), bool) or manifest.get("declared_member_count") != len(members) + len(omissions):
        raise BackupError("BACKUP_MANIFEST_INVALID")
    for omitted in omissions:
        if not isinstance(omitted, dict) or set(omitted) != {"logical_member_id", "artifact_family", "disposition"} or not isinstance(omitted.get("logical_member_id"), str) or not _ID_RE.fullmatch(omitted["logical_member_id"]) or omitted["logical_member_id"] in logical_ids:
            raise BackupError("BACKUP_MANIFEST_INVALID")
        logical_ids.add(omitted["logical_member_id"])
        if not isinstance(omitted.get("artifact_family"), str):
            raise BackupError("BACKUP_MANIFEST_INVALID")
        family_name = omitted["artifact_family"]
        family = classify_artifact_family(family_name)
        if family["state_class"] == "UNCLASSIFIED_REQUIRES_POLICY":
            raise BackupError("BACKUP_CLASSIFICATION_MISMATCH")
        if family_name == "user_product_settings":
            allowed = {"NO_CURRENT_CANONICAL_AUTHORITY"}
        elif family["backup_tier"] == "DERIVED":
            allowed = {"DERIVED_OMITTED_BY_POLICY"}
        elif family["backup_tier"] == "NONE":
            allowed = {"OUTSIDE_BACKUP_BOUNDARY"}
        elif manifest["backup_tier"] == "CORE" and family["backup_tier"] == "FULL_GOVERNED":
            allowed = {"NOT_IN_CORE_TIER"}
        else:
            # A family selected by the declared package tier cannot be laundered
            # into an omission by recomputing the self-hash of the manifest.
            raise BackupError("BACKUP_CLASSIFICATION_MISMATCH")
        if omitted.get("disposition") not in allowed:
            raise BackupError("BACKUP_CLASSIFICATION_MISMATCH")
    if omissions != sorted(omissions, key=lambda row: row["logical_member_id"]):
        raise BackupError("BACKUP_MANIFEST_INVALID")
    return {"status": "BACKUP_VERIFIED", "backup_id": manifest.get("backup_id"), "backup_tier": manifest["backup_tier"], "member_count": len(members), "manifest_sha256": integrity["sha256"]}
