from __future__ import annotations

import hashlib
import json
import socket
import sqlite3
from pathlib import Path

import pytest

import server.services.unified_backup as backup_module
from scripts.m8r_09_persistent_watchlists import PersistentWatchlistStore
from server.services.unified_backup import (
    MANIFEST_NAME,
    BackupError,
    BackupMember,
    BackupRoot,
    create_backup,
    plan_backup,
    verify_backup,
)


UTC = "2026-10-14T00:00:00Z"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _inventory(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): _sha(p.read_bytes()) for p in sorted(root.rglob("*")) if p.is_file()}


def _verify(package: Path, limit: int = 8_000_000):
    return verify_backup(package, max_total_bytes=limit)


def _rehash_manifest(manifest: dict) -> None:
    payload = dict(manifest)
    payload.pop("manifest_integrity", None)
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    manifest["manifest_integrity"]["sha256"] = hashlib.sha256(canonical).hexdigest()


def _member(root: Path, *, family="security_master_active_release_pointer", logical="active-pointer", source="identity/active.json", target="members/identity/active.json", binding="sm-release-1", kind="file") -> BackupMember:
    file_hash = _sha((root / source).read_bytes()) if kind == "file" else None
    return BackupMember(logical, family, "install", source, target, binding, True, expected_sha256=file_hash, source_kind=kind)


def _fixture(tmp_path: Path):
    source = tmp_path / "state"
    source.mkdir()
    (source / "identity").mkdir()
    (source / "identity" / "active.json").write_bytes(b'{"release_id":"r1"}\n')
    destination_parent = tmp_path / "backups"
    destination_parent.mkdir()
    roots = [BackupRoot("install", source)]
    member = _member(source)
    plan = plan_backup(backup_tier="CORE", roots=roots, members=[member], source_state_identity="installation-state-1", max_total_bytes=1024)
    return source, destination_parent, roots, member, plan


def test_core_plan_uses_a3_and_omits_unestablished_settings_authority(tmp_path: Path) -> None:
    source, _, roots, member, _ = _fixture(tmp_path)
    (source / "releases" / "r1").mkdir(parents=True)
    release_manifest = source / "releases" / "r1" / "manifest.json"
    release_manifest.write_bytes(b'{"release_id":"r1","index_sha256":"abc"}\n')
    history = BackupMember(
        "release-r1-manifest", "security_master_release_history_and_rollback_artifacts",
        "install", "releases/r1/manifest.json", "members/identity/releases/r1/manifest.json",
        "sm-release-r1", True, expected_sha256=_sha(release_manifest.read_bytes()),
    )
    settings = BackupMember("settings", "user_product_settings", "install", "not-present/settings.json", "members/settings.json", "none", False)
    plan = plan_backup(backup_tier="CORE", roots=roots, members=[member, history, settings], source_state_identity="installation-state-1", max_total_bytes=2048)
    assert [row["logical_member_id"] for row in plan["members"]] == ["active-pointer", "release-r1-manifest"]
    assert plan["omitted_members"] == [{"logical_member_id": "settings", "artifact_family": "user_product_settings", "disposition": "NO_CURRENT_CANONICAL_AUTHORITY"}]
    assert plan["members"][0]["expected_sha256"] == _sha((source / "identity/active.json").read_bytes())


def test_full_governed_includes_core_and_governed_and_omits_derived_by_default(tmp_path: Path) -> None:
    source, _, roots, core, _ = _fixture(tmp_path)
    (source / "control").mkdir()
    (source / "control" / "f3.json").write_bytes(b'{"schema_version":"f3.v1"}\n')
    (source / "control" / "result.json").write_bytes(b'{"result":"retained bytes"}\n')
    (source / "control" / "audit.json").write_bytes(b'{"audit":"retained bytes"}\n')
    (source / "derived").mkdir()
    (source / "derived" / "handoff.json").write_bytes(b'{"handoff":true}\n')
    f3 = _member(source, family="f3_historical_validation_artifact", logical="historical-f3", source="control/f3.json", target="members/control/f3.json", binding="package-audit-1")
    result = _member(source, family="persisted_result_json", logical="result", source="control/result.json", target="members/control/result.json", binding="package-audit-1")
    audit = _member(source, family="persisted_audit_package", logical="audit", source="control/audit.json", target="members/control/audit.json", binding="package-audit-1")
    derived = _member(source, family="persisted_ai_handoff", logical="handoff", source="derived/handoff.json", target="members/derived/handoff.json", binding="projection-1")
    plan = plan_backup(backup_tier="FULL_GOVERNED", roots=roots, members=[derived, f3, core, result, audit], source_state_identity="installation-state-1", max_total_bytes=4096)
    assert [row["logical_member_id"] for row in plan["members"]] == ["audit", "historical-f3", "result", "active-pointer"]
    assert plan["omitted_members"][0]["disposition"] == "DERIVED_OMITTED_BY_POLICY"


def test_full_governed_verifier_rejects_laundered_required_family_omission(tmp_path: Path) -> None:
    source, parent, roots, core, _ = _fixture(tmp_path)
    (source / "control").mkdir()
    f3_path = source / "control" / "f3.json"
    f3_path.write_bytes(b'{"schema_version":"f3.v1"}\n')
    f3 = _member(
        source,
        family="f3_historical_validation_artifact",
        logical="historical-f3",
        source="control/f3.json",
        target="members/control/f3.json",
        binding="package-audit-1",
    )
    plan = plan_backup(
        backup_tier="FULL_GOVERNED",
        roots=roots,
        members=[core, f3],
        source_state_identity="installation-state-1",
        max_total_bytes=4096,
    )
    package = parent / "backup"
    create_backup(plan, destination=package, backup_id="backup", created_at=UTC)
    manifest_path = package / MANIFEST_NAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    removed = next(row for row in manifest["members"] if row["logical_member_id"] == "historical-f3")
    manifest["members"] = [row for row in manifest["members"] if row["logical_member_id"] != "historical-f3"]
    manifest["member_count"] = len(manifest["members"])
    manifest["total_size_bytes"] = sum(row["size_bytes"] for row in manifest["members"])
    manifest["omitted_members"].append({
        "logical_member_id": "historical-f3",
        "artifact_family": "f3_historical_validation_artifact",
        "disposition": "NOT_IN_FULL_GOVERNED_TIER",
    })
    manifest["omitted_members"].sort(key=lambda row: row["logical_member_id"])
    manifest["declared_member_count"] = len(manifest["members"]) + len(manifest["omitted_members"])
    _rehash_manifest(manifest)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    (package / removed["backup_relative_path"]).unlink()
    (package / "members" / "control").rmdir()
    with pytest.raises(BackupError, match="BACKUP_CLASSIFICATION_MISMATCH"):
        _verify(package)


def test_sqlite_plan_uses_snapshot_size_not_raw_source_file_size(tmp_path: Path, monkeypatch) -> None:
    source_root = tmp_path / "installation"
    watchlists = source_root / "watchlists"
    watchlists.mkdir(parents=True)
    source_db = watchlists / "watchlists.sqlite3"
    source_db.write_bytes(b"raw-source-file")
    snapshot_size = len(source_db.read_bytes()) + 4096
    monkeypatch.setattr(
        backup_module,
        "_sqlite_snapshot_fingerprint",
        lambda source, max_bytes: (snapshot_size, "a" * 64),
    )
    member = BackupMember(
        "watchlists-db", "persistent_watchlists_and_revision_database", "install",
        "watchlists/watchlists.sqlite3", "members/watchlists/watchlists.sqlite3",
        "watchlist-store-1", True, source_kind="sqlite",
    )
    plan = plan_backup(
        backup_tier="CORE",
        roots=[BackupRoot("install", source_root)],
        members=[member],
        source_state_identity="installation-state-1",
        max_total_bytes=snapshot_size + 1024,
    )
    assert plan["members"][0]["planned_size_bytes"] == snapshot_size
    assert plan["planned_total_bytes"] == snapshot_size


def test_unknown_or_unverified_family_fails_closed(tmp_path: Path) -> None:
    source, _, roots, _, _ = _fixture(tmp_path)
    unknown = BackupMember("unknown", "cache", "install", "identity/active.json", "members/cache", "unknown", True, expected_sha256=_sha((source / "identity/active.json").read_bytes()))
    with pytest.raises(BackupError, match="UNCLASSIFIED_SOURCE_STATE"):
        plan_backup(backup_tier="CORE", roots=roots, members=[unknown], source_state_identity="state-1", max_total_bytes=1024)
    unbound = BackupMember("unbound", "security_master_active_release_pointer", "install", "identity/active.json", "members/unbound", "", False, expected_sha256=_sha((source / "identity/active.json").read_bytes()))
    with pytest.raises(BackupError, match="BACKUP_MANIFEST_INVALID"):
        plan_backup(backup_tier="CORE", roots=roots, members=[unbound], source_state_identity="state-1", max_total_bytes=1024)


def test_ephemeral_family_needs_explicit_unreferenced_proof_and_is_omitted(tmp_path: Path) -> None:
    source, _, roots, _, _ = _fixture(tmp_path)
    (source / "identity/diagnostic.jsonl").write_bytes(b'{"event":"ready"}\n')
    missing_proof = BackupMember(
        "diagnostic", "operational_jsonl_diagnostics", "install", "identity/diagnostic.jsonl",
        "members/diagnostic.jsonl", "runtime-owner-1", True,
        expected_sha256=_sha((source / "identity/diagnostic.jsonl").read_bytes()),
    )
    with pytest.raises(BackupError, match="UNCLASSIFIED_SOURCE_STATE"):
        plan_backup(backup_tier="CORE", roots=roots, members=[missing_proof], source_state_identity="state-1", max_total_bytes=1024)
    proven = BackupMember(
        "diagnostic", "operational_jsonl_diagnostics", "install", "identity/diagnostic.jsonl",
        "members/diagnostic.jsonl", "runtime-owner-1", True, True,
        expected_sha256=_sha((source / "identity/diagnostic.jsonl").read_bytes()),
    )
    plan = plan_backup(backup_tier="CORE", roots=roots, members=[proven], source_state_identity="state-1", max_total_bytes=1024)
    assert plan["members"] == []
    assert plan["omitted_members"][0]["disposition"] == "OUTSIDE_BACKUP_BOUNDARY"


def test_create_copies_exact_bytes_with_portable_verified_manifest_and_no_source_mutation(tmp_path: Path) -> None:
    source, destination_parent, _, _, plan = _fixture(tmp_path)
    before = _inventory(source)
    result = create_backup(plan, destination=destination_parent / "backup-001", backup_id="backup-001", created_at=UTC)
    assert result["status"] == "BACKUP_CREATED"
    assert _inventory(source) == before
    package = destination_parent / "backup-001"
    member = package / "members/identity/active.json"
    assert member.read_bytes() == (source / "identity/active.json").read_bytes()
    manifest = json.loads((package / MANIFEST_NAME).read_text(encoding="utf-8"))
    assert set(manifest) == {"manifest_schema_version", "backup_format_version", "backup_id", "backup_tier", "created_at", "product_identity", "source_state_identity", "selection_scope", "authority_binding_model", "member_count", "declared_member_count", "total_size_bytes", "max_total_bytes", "members", "omitted_members", "manifest_integrity"}
    assert manifest["selection_scope"] == "EXPLICIT_DECLARED_MEMBERS_ONLY"
    assert manifest["authority_binding_model"] == "TRUSTED_INTERNAL_CALLER_ATTESTED"
    row = manifest["members"][0]
    assert row["source_relative_path"] == "identity/active.json"
    assert row["backup_relative_path"] == "members/identity/active.json"
    assert row["source_authority_id"] == "sm-release-1"
    assert row["sha256"] == _sha(member.read_bytes())
    assert row["size_bytes"] == len(member.read_bytes())
    assert "D:\\" not in (package / MANIFEST_NAME).read_text(encoding="utf-8")
    assert "C:\\Users" not in (package / MANIFEST_NAME).read_text(encoding="utf-8")
    assert _verify(package)["status"] == "BACKUP_VERIFIED"


def test_deterministic_member_order_and_injected_time_and_id(tmp_path: Path) -> None:
    source, parent, roots, core, _ = _fixture(tmp_path)
    (source / "identity" / "second.json").write_bytes(b"second")
    second = _member(source, logical="second", source="identity/second.json", target="members/z.json", binding="sm-release-2")
    first = _member(source, logical="first", target="members/a.json", binding="sm-release-1")
    plan = plan_backup(backup_tier="CORE", roots=roots, members=[second, first], source_state_identity="s-1", max_total_bytes=2048)
    assert [row["backup_relative_path"] for row in plan["members"]] == ["members/a.json", "members/z.json"]
    create_backup(plan, destination=parent / "ordered", backup_id="ordered", created_at=UTC)
    manifest = json.loads((parent / "ordered" / MANIFEST_NAME).read_text(encoding="utf-8"))
    assert [row["backup_relative_path"] for row in manifest["members"]] == ["members/a.json", "members/z.json"]
    assert manifest["created_at"] == UTC


@pytest.mark.parametrize("source_path,target_path", [
    ("../escape", "members/escape"),
    ("identity/active.json", "../escape"),
    ("identity/active.json", "C:/outside"),
    ("identity/active.json", "/absolute/outside"),
])
def test_path_traversal_and_absolute_paths_fail_closed(tmp_path: Path, source_path: str, target_path: str) -> None:
    source, _, roots, _, _ = _fixture(tmp_path)
    member = BackupMember("bad", "security_master_active_release_pointer", "install", source_path, target_path, "bind-1", True, expected_sha256=_sha((source / "identity/active.json").read_bytes()))
    with pytest.raises(BackupError, match="BACKUP_PATH_UNSAFE"):
        plan_backup(backup_tier="CORE", roots=roots, members=[member], source_state_identity="state-1", max_total_bytes=1024)


def test_duplicate_logical_and_casefold_paths_fail_closed(tmp_path: Path) -> None:
    source, _, roots, _, _ = _fixture(tmp_path)
    hash_value = _sha((source / "identity/active.json").read_bytes())
    one = BackupMember("one", "security_master_active_release_pointer", "install", "identity/active.json", "members/a.json", "bind-1", True, expected_sha256=hash_value)
    duplicate_id = BackupMember("one", "security_master_active_release_pointer", "install", "identity/active.json", "members/b.json", "bind-2", True, expected_sha256=hash_value)
    with pytest.raises(BackupError, match="BACKUP_MANIFEST_INVALID"):
        plan_backup(backup_tier="CORE", roots=roots, members=[one, duplicate_id], source_state_identity="state-1", max_total_bytes=1024)
    collision = BackupMember("two", "security_master_active_release_pointer", "install", "identity/active.json", "members/A.JSON", "bind-2", True, expected_sha256=hash_value)
    with pytest.raises(BackupError, match="BACKUP_MANIFEST_INVALID"):
        plan_backup(backup_tier="CORE", roots=roots, members=[one, collision], source_state_identity="state-1", max_total_bytes=1024)


def test_tamper_missing_unexpected_and_existing_destination_fail_closed(tmp_path: Path) -> None:
    _, parent, _, _, plan = _fixture(tmp_path)
    package = parent / "backup"
    create_backup(plan, destination=package, backup_id="backup", created_at=UTC)
    (package / "members/identity/active.json").write_bytes(b'{"release_id":"r2"}\n')
    with pytest.raises(BackupError, match="BACKUP_MEMBER_HASH_MISMATCH"):
        _verify(package)
    with pytest.raises(BackupError, match="BACKUP_DESTINATION_EXISTS"):
        create_backup(plan, destination=package, backup_id="again", created_at=UTC)
    (package / "members/identity/active.json").unlink()
    with pytest.raises(BackupError, match="BACKUP_MEMBER_MISSING"):
        _verify(package)
    (package / "members/identity/active.json").write_bytes(b'{"release_id":"r1"}\n')
    (package / "extra.txt").write_text("unexpected", encoding="utf-8")
    # Recompute a valid manifest hash is not required: unexpected files are rejected
    # after the declared members are independently verified.
    with pytest.raises(BackupError, match="BACKUP_MEMBER_UNEXPECTED"):
        _verify(package)


def test_rehashed_manifest_cannot_upgrade_declared_selection_scope(tmp_path: Path) -> None:
    _, parent, _, _, plan = _fixture(tmp_path)
    package = parent / "backup"
    create_backup(plan, destination=package, backup_id="backup", created_at=UTC)
    manifest_path = package / MANIFEST_NAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["selection_scope"] = "WHOLE_INSTALLATION_COMPLETE"
    manifest["authority_binding_model"] = "SELF_ASSERTED"
    _rehash_manifest(manifest)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    with pytest.raises(BackupError, match="BACKUP_MANIFEST_INVALID"):
        _verify(package)


def test_source_change_after_plan_fails_before_finalization(tmp_path: Path) -> None:
    source, parent, _, _, plan = _fixture(tmp_path)
    (source / "identity/active.json").write_bytes(b'{"release_id":"r2"}\n')
    with pytest.raises(BackupError, match="SOURCE_CHANGED_DURING_BACKUP"):
        create_backup(plan, destination=parent / "changed", backup_id="changed", created_at=UTC)
    assert not (parent / "changed").exists()
    staging = parent / ".changed.staging-changed"
    assert staging.is_dir()
    with pytest.raises(BackupError, match="BACKUP_MANIFEST_INVALID"):
        _verify(staging)


def test_source_and_destination_root_overlap_is_rejected(tmp_path: Path) -> None:
    source, _, roots, _, plan = _fixture(tmp_path)
    with pytest.raises(BackupError, match="BACKUP_PATH_UNSAFE"):
        create_backup(plan, destination=source / "nested-backup", backup_id="nested", created_at=UTC)
    with pytest.raises(BackupError, match="BACKUP_PATH_UNSAFE"):
        create_backup(plan, destination=source.parent, backup_id="parent", created_at=UTC)


def test_tampered_manifest_integrity_fails_closed(tmp_path: Path) -> None:
    _, parent, _, _, plan = _fixture(tmp_path)
    package = parent / "backup"
    create_backup(plan, destination=package, backup_id="backup", created_at=UTC)
    manifest_path = package / MANIFEST_NAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["source_state_identity"] = "altered"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(BackupError, match="BACKUP_MANIFEST_INVALID"):
        _verify(package)


def test_duplicate_manifest_json_keys_fail_closed(tmp_path: Path) -> None:
    _, parent, _, _, plan = _fixture(tmp_path)
    package = parent / "backup"
    create_backup(plan, destination=package, backup_id="backup", created_at=UTC)
    manifest_path = package / MANIFEST_NAME
    raw = manifest_path.read_text(encoding="utf-8")
    raw = raw.replace('"backup_id":"backup"', '"backup_id":"backup","backup_id":"shadow"', 1)
    manifest_path.write_text(raw, encoding="utf-8")
    with pytest.raises(BackupError, match="BACKUP_MANIFEST_INVALID"):
        _verify(package)


def test_unknown_manifest_version_fails_closed(tmp_path: Path) -> None:
    _, parent, _, _, plan = _fixture(tmp_path)
    package = parent / "backup"
    create_backup(plan, destination=package, backup_id="backup", created_at=UTC)
    manifest_path = package / MANIFEST_NAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["backup_format_version"] = "tw_market_backup.v999"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(BackupError, match="BACKUP_UNSUPPORTED_VERSION"):
        _verify(package)


def test_planner_rejects_oversize_file_before_hashing(tmp_path: Path, monkeypatch) -> None:
    source, _, roots, _, _ = _fixture(tmp_path)
    large = source / "identity" / "large.json"
    large.write_bytes(b"x" * 4096)
    member = _member(
        source,
        logical="large",
        source="identity/large.json",
        target="members/identity/large.json",
        binding="sm-large",
    )
    calls = []

    def forbidden_hash(path):
        calls.append(path)
        raise AssertionError("oversize source should be rejected before hashing")

    monkeypatch.setattr(backup_module, "_hash_file", forbidden_hash)
    with pytest.raises(BackupError, match="BACKUP_RESOURCE_LIMIT_EXCEEDED"):
        plan_backup(
            backup_tier="CORE",
            roots=roots,
            members=[member],
            source_state_identity="state-1",
            max_total_bytes=1024,
        )
    assert calls == []


def test_verifier_rejects_size_tamper_before_hashing(tmp_path: Path, monkeypatch) -> None:
    _, parent, _, _, plan = _fixture(tmp_path)
    package = parent / "backup"
    create_backup(plan, destination=package, backup_id="backup", created_at=UTC)
    member_path = package / "members" / "identity" / "active.json"
    member_path.write_bytes(member_path.read_bytes() + b"tamper")
    calls = []

    def forbidden_hash(path):
        calls.append(path)
        raise AssertionError("size mismatch should be rejected before hashing")

    monkeypatch.setattr(backup_module, "_hash_file", forbidden_hash)
    with pytest.raises(BackupError, match="BACKUP_MEMBER_SIZE_MISMATCH"):
        _verify(package)
    assert calls == []


def test_verifier_applies_explicit_caller_size_bound(tmp_path: Path) -> None:
    _, parent, _, _, plan = _fixture(tmp_path)
    package = parent / "backup"
    create_backup(plan, destination=package, backup_id="backup", created_at=UTC)
    with pytest.raises(BackupError, match="BACKUP_RESOURCE_LIMIT_EXCEEDED"):
        _verify(package, limit=1)


def test_symlink_source_is_rejected_when_supported(tmp_path: Path) -> None:
    source, _, roots, _, _ = _fixture(tmp_path)
    outside = tmp_path / "outside.json"
    outside.write_bytes((source / "identity/active.json").read_bytes())
    link = source / "identity" / "link.json"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable")
    member = BackupMember("linked", "security_master_active_release_pointer", "install", "identity/link.json", "members/link.json", "bind-1", True, expected_sha256=_sha(outside.read_bytes()))
    with pytest.raises(BackupError, match="BACKUP_PATH_UNSAFE"):
        plan_backup(backup_tier="CORE", roots=roots, members=[member], source_state_identity="state-1", max_total_bytes=1024)


def test_live_watchlist_database_uses_sqlite_snapshot_api_and_source_is_unchanged(tmp_path: Path) -> None:
    source_root = tmp_path / "installation"
    store = PersistentWatchlistStore(root=source_root / "watchlists")
    before = _inventory(source_root)
    member = BackupMember(
        "watchlists-db", "persistent_watchlists_and_revision_database", "install",
        "watchlists/watchlists.sqlite3", "members/watchlists/watchlists.sqlite3",
        "watchlist-store-1", True, source_kind="sqlite",
    )
    plan = plan_backup(backup_tier="CORE", roots=[BackupRoot("install", source_root)], members=[member], source_state_identity="installation-state-1", max_total_bytes=8_000_000)
    parent = tmp_path / "backup-dest"
    parent.mkdir()
    result = create_backup(plan, destination=parent / "watchlist-backup", backup_id="watchlist-backup", created_at=UTC)
    assert result["status"] == "BACKUP_CREATED"
    assert _inventory(source_root) == before
    copied_db = parent / "watchlist-backup/members/watchlists/watchlists.sqlite3"
    con = sqlite3.connect(f"file:{copied_db.as_posix()}?mode=ro", uri=True)
    try:
        assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    finally:
        con.close()


def test_verifier_is_read_only_and_never_uses_network_or_acquisition(tmp_path: Path, monkeypatch) -> None:
    _, parent, _, _, plan = _fixture(tmp_path)
    package = parent / "backup"
    calls = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("unexpected network/database operation")

    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    create_backup(plan, destination=package, backup_id="backup", created_at=UTC)
    before = _inventory(package)
    assert _verify(package)["status"] == "BACKUP_VERIFIED"
    assert calls == []
    assert _inventory(package) == before
