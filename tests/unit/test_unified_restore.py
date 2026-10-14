from __future__ import annotations

import hashlib
import json
import socket
import sqlite3
from pathlib import Path

import pytest

from scripts.m8r_09_persistent_watchlists import PersistentWatchlistStore
from server.services import unified_backup as backup_module
from server.services import unified_restore as restore_module
from server.services.unified_backup import BackupMember, BackupRoot, create_backup, plan_backup
from server.services.unified_restore import (
    CompatibilityAttestation,
    DEFAULT_COMPATIBILITY_CONTRACT,
    RECEIPT_NAME,
    RestoreCompatibilityContract,
    RestoreError,
    inspect_restore,
    restore_backup,
    verify_restored_state,
    _safe_relative,
)


UTC = "2026-10-14T00:00:00Z"
LIMIT = 2_000_000


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _inventory(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): _sha(p.read_bytes()) for p in sorted(root.rglob("*")) if p.is_file()}


def _rehash_receipt(receipt: dict) -> None:
    body = dict(receipt)
    body.pop("receipt_integrity", None)
    canonical = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    receipt["receipt_integrity"]["sha256"] = _sha(canonical)


def _create_backup(tmp_path: Path, *, family: str = "security_master_active_release_pointer",
                   content: bytes = b'{"release_id":"r1"}\n', logical_id: str = "active-pointer"):
    source = tmp_path / "source"
    source.mkdir()
    (source / "state.bin").write_bytes(content)
    backup_parent = tmp_path / "backups"
    backup_parent.mkdir()
    item = BackupMember(logical_id, family, "install", "state.bin", "members/state.bin",
                        "binding-1", True, expected_sha256=_sha(content))
    plan = plan_backup(backup_tier="CORE", roots=[BackupRoot("install", source)], members=[item],
                       source_state_identity="state-1", max_total_bytes=LIMIT)
    package = backup_parent / "backup-1"
    create_backup(plan, destination=package, backup_id="backup-1", created_at=UTC)
    manifest = json.loads((package / "backup-manifest.json").read_text(encoding="utf-8"))
    attestation = CompatibilityAttestation(
        manifest["manifest_integrity"]["sha256"], {logical_id: "1"}
    )
    return source, package, attestation


def _inspect(package: Path, attestation: CompatibilityAttestation, **kwargs):
    return inspect_restore(backup_path=package, compatibility=attestation,
                           max_total_bytes=LIMIT, max_member_count=100, **kwargs)


def test_direct_compatibility_and_restore_preserve_exact_bytes_and_scope(tmp_path: Path) -> None:
    source, package, attestation = _create_backup(tmp_path, content=b'{ "keep": [1,2] }\r\n')
    source_before = _inventory(source)
    package_before = _inventory(package)
    destination = tmp_path / "restored"
    inspection = _inspect(package, attestation)
    assert inspection["status"] == "DIRECT_RESTORE_COMPATIBLE"
    result = restore_backup(backup_path=package, destination=destination, compatibility=attestation,
                            forbidden_roots=[source], max_total_bytes=LIMIT, max_member_count=100,
                            restore_id="restore-1", created_at=UTC)
    assert result["restore_status"] == "RESTORE_COMPLETED"
    restored = destination / "state.bin"
    assert restored.read_bytes() == b'{ "keep": [1,2] }\r\n'
    assert _inventory(package) == package_before
    assert _inventory(source) == source_before
    receipt = json.loads((destination / RECEIPT_NAME).read_text(encoding="utf-8"))
    assert receipt["restore_scope"] == "EXPLICIT_DECLARED_MEMBERS_ONLY"
    restored_before_verify = _inventory(destination)
    assert verify_restored_state(backup_path=package, restored_path=destination,
                                 compatibility=attestation, max_total_bytes=LIMIT,
                                 max_member_count=100)["status"] == "RESTORED_STATE_VERIFIED"
    assert _inventory(destination) == restored_before_verify


def test_migration_required_is_inspect_only_and_creates_no_target(tmp_path: Path) -> None:
    _, package, attestation = _create_backup(tmp_path)
    historical = CompatibilityAttestation(attestation.backup_manifest_sha256, {"active-pointer": "0"})
    contract = RestoreCompatibilityContract(
        DEFAULT_COMPATIBILITY_CONTRACT.product_identity,
        DEFAULT_COMPATIBILITY_CONTRACT.restore_contract_version,
        DEFAULT_COMPATIBILITY_CONTRACT.supported_backup_formats,
        DEFAULT_COMPATIBILITY_CONTRACT.supported_manifest_versions,
        DEFAULT_COMPATIBILITY_CONTRACT.supported_state_family_versions,
        {("security_master_active_release_pointer", "0"): "sm-state-v0-to-v1"},
    )
    inspected = _inspect(package, historical, contract=contract)
    assert inspected["status"] == "MIGRATION_REQUIRED"
    assert inspected["source_state_family_versions"] == {"active-pointer": "0"}
    assert inspected["migration_paths"] == ["sm-state-v0-to-v1"]
    destination = tmp_path / "must-not-exist"
    result = restore_backup(backup_path=package, destination=destination, compatibility=historical,
                            contract=contract, forbidden_roots=[], max_total_bytes=LIMIT, max_member_count=100,
                            restore_id="restore-migrate", created_at=UTC)
    assert result["restore_status"] == "MIGRATION_REQUIRED"
    assert not destination.exists()


def test_newer_and_unknown_versions_fail_closed_before_target_write(tmp_path: Path) -> None:
    _, package, attestation = _create_backup(tmp_path)
    newer = CompatibilityAttestation(attestation.backup_manifest_sha256, {"active-pointer": "2"})
    assert _inspect(package, newer)["status"] == "UNSUPPORTED_NEWER_STATE"
    unknown = CompatibilityAttestation(attestation.backup_manifest_sha256, {"active-pointer": "beta"})
    assert _inspect(package, unknown)["status"] == "RESTORE_COMPATIBILITY_UNKNOWN"
    missing = CompatibilityAttestation(attestation.backup_manifest_sha256, {})
    assert _inspect(package, missing)["status"] == "RESTORE_COMPATIBILITY_UNKNOWN"


def test_attestation_must_bind_exact_manifest_and_product_contract(tmp_path: Path) -> None:
    _, package, attestation = _create_backup(tmp_path)
    wrong = CompatibilityAttestation("0" * 64, attestation.state_family_versions)
    assert _inspect(package, wrong)["status"] == "RESTORE_COMPATIBILITY_UNKNOWN"
    mismatched = RestoreCompatibilityContract(
        "other-product", "tw_market_restore_contract.v1",
        DEFAULT_COMPATIBILITY_CONTRACT.supported_backup_formats,
        DEFAULT_COMPATIBILITY_CONTRACT.supported_manifest_versions,
        DEFAULT_COMPATIBILITY_CONTRACT.supported_state_family_versions, {},
    )
    with pytest.raises(RestoreError, match="RESTORE_COMPATIBILITY_UNKNOWN"):
        _inspect(package, attestation, contract=mismatched)


@pytest.mark.parametrize("relative", ["../escape", "C:/outside", "/absolute", "//server/share", "dir/file:stream", "CON/file"])
def test_restore_member_paths_reject_windows_and_posix_escape_forms(relative: str) -> None:
    with pytest.raises(RestoreError, match="RESTORE_TARGET_UNSAFE"):
        _safe_relative(relative)


def test_restore_rejects_existing_or_protected_target_without_overwrite(tmp_path: Path) -> None:
    source, package, attestation = _create_backup(tmp_path)
    existing = tmp_path / "existing"
    existing.mkdir()
    with pytest.raises(RestoreError, match="RESTORE_TARGET_NOT_EMPTY"):
        restore_backup(backup_path=package, destination=existing, compatibility=attestation,
                       forbidden_roots=[], max_total_bytes=LIMIT, max_member_count=100, restore_id="restore-existing",
                       created_at=UTC)
    with pytest.raises(RestoreError, match="RESTORE_TARGET_UNSAFE"):
        restore_backup(backup_path=package, destination=source / "child",
                       compatibility=attestation, forbidden_roots=[source], max_total_bytes=LIMIT,
                       max_member_count=100, restore_id="restore-protected", created_at=UTC)


def test_restore_rejects_reparse_or_symlinked_destination_parent_when_supported(tmp_path: Path) -> None:
    source, package, attestation = _create_backup(tmp_path)
    link = tmp_path / "linked-parent"
    try:
        link.symlink_to(source, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("directory symlink creation unavailable")
    with pytest.raises(RestoreError, match="RESTORE_TARGET_UNSAFE"):
        restore_backup(backup_path=package, destination=link / "restored", compatibility=attestation,
                       forbidden_roots=[source], max_total_bytes=LIMIT, max_member_count=100,
                       restore_id="restore-link", created_at=UTC)


def test_receipt_outcome_cannot_be_laundered_by_rehash(tmp_path: Path) -> None:
    _, package, attestation = _create_backup(tmp_path)
    destination = tmp_path / "restored"
    restore_backup(backup_path=package, destination=destination, compatibility=attestation,
                   forbidden_roots=[], max_total_bytes=LIMIT, max_member_count=100, restore_id="restore-tamper",
                   created_at=UTC)
    receipt_path = destination / RECEIPT_NAME
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["compatibility_outcome"] = "MIGRATION_REQUIRED"
    _rehash_receipt(receipt)
    receipt_path.write_text(json.dumps(receipt, sort_keys=True), encoding="utf-8")
    with pytest.raises(RestoreError, match="RESTORE_VERIFICATION_FAILED"):
        verify_restored_state(backup_path=package, restored_path=destination,
                              compatibility=attestation, max_total_bytes=LIMIT,
                              max_member_count=100)


def test_compatibility_metadata_and_outcome_cannot_be_laundered_by_rehash(tmp_path: Path) -> None:
    _, package, attestation = _create_backup(tmp_path)
    destination = tmp_path / "restored"
    restore_backup(backup_path=package, destination=destination, compatibility=attestation,
                   forbidden_roots=[], max_total_bytes=LIMIT, max_member_count=100, restore_id="restore-meta",
                   created_at=UTC)
    receipt_path = destination / RECEIPT_NAME
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["state_family_versions"]["active-pointer"] = "0"
    receipt["compatibility_outcome"] = "MIGRATION_REQUIRED"
    _rehash_receipt(receipt)
    receipt_path.write_text(json.dumps(receipt, sort_keys=True), encoding="utf-8")
    with pytest.raises(RestoreError, match="RESTORE_VERIFICATION_FAILED"):
        verify_restored_state(backup_path=package, restored_path=destination,
                              compatibility=attestation, max_total_bytes=LIMIT,
                              max_member_count=100)


def test_scope_cannot_be_laundered_by_rehash(tmp_path: Path) -> None:
    _, package, attestation = _create_backup(tmp_path)
    destination = tmp_path / "restored"
    restore_backup(backup_path=package, destination=destination, compatibility=attestation,
                   forbidden_roots=[], max_total_bytes=LIMIT, max_member_count=100, restore_id="restore-scope",
                   created_at=UTC)
    receipt_path = destination / RECEIPT_NAME
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["restore_scope"] = "WHOLE_INSTALLATION_COMPLETE"
    _rehash_receipt(receipt)
    receipt_path.write_text(json.dumps(receipt, sort_keys=True), encoding="utf-8")
    with pytest.raises(RestoreError, match="RESTORE_VERIFICATION_FAILED"):
        verify_restored_state(backup_path=package, restored_path=destination,
                              compatibility=attestation, max_total_bytes=LIMIT,
                              max_member_count=100)


def test_receipt_envelope_metadata_cannot_be_laundered_by_rehash(tmp_path: Path) -> None:
    _, package, attestation = _create_backup(tmp_path)
    destination = tmp_path / "restored"
    restore_backup(backup_path=package, destination=destination, compatibility=attestation,
                   forbidden_roots=[], max_total_bytes=LIMIT, max_member_count=100,
                   restore_id="restore-envelope", created_at=UTC)
    receipt_path = destination / RECEIPT_NAME
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["restore_id"] = "invalid restore id"
    receipt["created_at"] = "not-a-timestamp"
    receipt["receipt_integrity"]["extra"] = "not-allowed"
    _rehash_receipt(receipt)
    receipt_path.write_text(json.dumps(receipt, sort_keys=True), encoding="utf-8")
    with pytest.raises(RestoreError, match="RESTORE_VERIFICATION_FAILED"):
        verify_restored_state(backup_path=package, restored_path=destination,
                              compatibility=attestation, max_total_bytes=LIMIT,
                              max_member_count=100)


def test_unc_destination_rejected_before_filesystem_probe(tmp_path: Path, monkeypatch) -> None:
    _, package, _ = _create_backup(tmp_path)

    def forbidden_probe(path):
        raise AssertionError("UNC destination must be rejected before filesystem probing")

    monkeypatch.setattr(restore_module, "_unsafe_path", forbidden_probe)
    with pytest.raises(RestoreError, match="RESTORE_TARGET_UNSAFE"):
        restore_module._resolve_destination(
            Path(r"\\\\server\\share\\restored"), backup_path=package, forbidden_roots=[]
        )


def test_extra_or_tampered_restored_member_fails_read_only_verification(tmp_path: Path) -> None:
    _, package, attestation = _create_backup(tmp_path)
    destination = tmp_path / "restored"
    restore_backup(backup_path=package, destination=destination, compatibility=attestation,
                   forbidden_roots=[], max_total_bytes=LIMIT, max_member_count=100, restore_id="restore-extra",
                   created_at=UTC)
    (destination / "extra.bin").write_bytes(b"extra")
    with pytest.raises(RestoreError, match="RESTORE_VERIFICATION_FAILED"):
        verify_restored_state(backup_path=package, restored_path=destination,
                              compatibility=attestation, max_total_bytes=LIMIT,
                              max_member_count=100)


def test_watchlist_snapshot_restore_passes_sqlite_integrity_without_migration(tmp_path: Path) -> None:
    source = tmp_path / "source"
    store = PersistentWatchlistStore(root=source / "watchlists")
    db_path = store.path
    backup_parent = tmp_path / "backups"
    backup_parent.mkdir()
    member = BackupMember("watchlists", "persistent_watchlists_and_revision_database", "install",
                          "watchlists/watchlists.sqlite3", "members/watchlists/watchlists.sqlite3",
                          "watchlist-binding", True, source_kind="sqlite")
    plan = plan_backup(backup_tier="CORE", roots=[BackupRoot("install", source)], members=[member],
                       source_state_identity="state-watchlist", max_total_bytes=LIMIT)
    package = backup_parent / "watchlists-backup"
    create_backup(plan, destination=package, backup_id="watchlists-backup", created_at=UTC)
    manifest = json.loads((package / "backup-manifest.json").read_text(encoding="utf-8"))
    attestation = CompatibilityAttestation(manifest["manifest_integrity"]["sha256"], {"watchlists": "1"})
    destination = tmp_path / "restored-watchlists"
    restore_backup(backup_path=package, destination=destination, compatibility=attestation,
                   forbidden_roots=[], max_total_bytes=LIMIT, max_member_count=100, restore_id="restore-wl",
                   created_at=UTC)
    restored_db = destination / "watchlists/watchlists.sqlite3"
    con = sqlite3.connect(f"file:{restored_db.as_posix()}?mode=ro", uri=True)
    try:
        assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    finally:
        con.close()


def test_f3_result_audit_and_authorization_are_retained_as_exact_bytes(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    payloads = {
        "active.json": ("security_master_active_release_pointer", b'{"schema_version":"identity-pointer.v1"}\n'),
        "f3.json": ("f3_historical_validation_artifact", b'{  "historical_f3" : true }\r\n'),
        "result.json": ("persisted_result_json", b'{"schema_version":"result.v3","evidence":[]}\n'),
        "audit.json": ("persisted_audit_package", b'{"schema_version":"audit.v3","lineage":[]}\n'),
        "authorization.json": ("authorization_and_consumption_binding", b'{"consumed":true,"retained":true}\n'),
    }
    members = []
    for name, (family, payload) in payloads.items():
        (source / name).write_bytes(payload)
        members.append(BackupMember(name, family, "install", name, f"members/{name}",
                                    "authority-1", True, expected_sha256=_sha(payload)))
    plan = plan_backup(backup_tier="FULL_GOVERNED", roots=[BackupRoot("install", source)],
                       members=members, source_state_identity="state-evidence", max_total_bytes=LIMIT)
    backup_parent = tmp_path / "backups"
    backup_parent.mkdir()
    package = backup_parent / "full"
    create_backup(plan, destination=package, backup_id="full-backup", created_at=UTC)
    manifest = json.loads((package / "backup-manifest.json").read_text(encoding="utf-8"))
    attestation = CompatibilityAttestation(manifest["manifest_integrity"]["sha256"], {"active.json": "1"})
    destination = tmp_path / "restored-full"
    result = restore_backup(backup_path=package, destination=destination, compatibility=attestation,
                           forbidden_roots=[], max_total_bytes=LIMIT, max_member_count=100, restore_id="restore-full",
                           created_at=UTC)
    assert result["status"] == "RESTORED_STATE_VERIFIED"
    for name, (_, expected) in payloads.items():
        assert (destination / name).read_bytes() == expected


def test_member_and_byte_limits_fail_before_restore_write(tmp_path: Path) -> None:
    _, package, attestation = _create_backup(tmp_path)
    with pytest.raises(RestoreError, match="RESTORE_RESOURCE_LIMIT_EXCEEDED"):
        inspect_restore(backup_path=package, compatibility=attestation, max_total_bytes=1, max_member_count=10)
    with pytest.raises(RestoreError, match="RESTORE_RESOURCE_LIMIT_EXCEEDED"):
        inspect_restore(backup_path=package, compatibility=attestation, max_total_bytes=LIMIT, max_member_count=0)


def test_member_count_limit_is_checked_before_a4_member_hashing(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "one").write_bytes(b"one")
    (source / "two").write_bytes(b"two")
    items = [BackupMember(name, "security_master_active_release_pointer", "install", name,
                          f"members/{name}", f"binding-{name}", True,
                          expected_sha256=_sha(name.encode())) for name in ("one", "two")]
    plan = plan_backup(backup_tier="CORE", roots=[BackupRoot("install", source)], members=items,
                       source_state_identity="state-many", max_total_bytes=LIMIT)
    parent = tmp_path / "backups"
    parent.mkdir()
    package = parent / "multi"
    create_backup(plan, destination=package, backup_id="multi", created_at=UTC)
    manifest = json.loads((package / "backup-manifest.json").read_text(encoding="utf-8"))
    attestation = CompatibilityAttestation(manifest["manifest_integrity"]["sha256"], {"one": "1", "two": "1"})

    def forbidden(*args, **kwargs):
        raise AssertionError("member limit should fail before A4 member verification")

    monkeypatch.setattr(backup_module, "verify_backup", forbidden)
    with pytest.raises(RestoreError, match="RESTORE_RESOURCE_LIMIT_EXCEEDED"):
        inspect_restore(backup_path=package, compatibility=attestation,
                        max_total_bytes=LIMIT, max_member_count=1)


def test_invalid_or_tampered_a4_package_is_rejected_before_target_creation(tmp_path: Path) -> None:
    _, package, attestation = _create_backup(tmp_path)
    (package / "members/state.bin").write_bytes(b"tampered")
    destination = tmp_path / "must-not-be-created"
    with pytest.raises(RestoreError, match="RESTORE_MEMBER_INTEGRITY_FAILED"):
        restore_backup(backup_path=package, destination=destination, compatibility=attestation,
                       forbidden_roots=[], max_total_bytes=LIMIT, max_member_count=100, restore_id="restore-badtamper",
                       created_at=UTC)
    assert not destination.exists()
    assert not (tmp_path / ".must-not-be-created.staging-restore-badtamper").exists()


def test_tampered_a4_manifest_is_rejected_without_mutation(tmp_path: Path) -> None:
    _, package, attestation = _create_backup(tmp_path)
    manifest_path = package / "backup-manifest.json"
    manifest_path.write_text(manifest_path.read_text(encoding="utf-8").replace('"backup_id":"backup-1"', '"backup_id":"changed"'), encoding="utf-8")
    before = _inventory(package)
    with pytest.raises(RestoreError, match="RESTORE_SOURCE_INVALID"):
        inspect_restore(backup_path=package, compatibility=attestation,
                        max_total_bytes=LIMIT, max_member_count=100)
    assert _inventory(package) == before


def test_inspection_restore_and_verification_make_no_network_calls(tmp_path: Path, monkeypatch) -> None:
    _, package, attestation = _create_backup(tmp_path)
    calls: list[str] = []

    def forbidden(*args, **kwargs):
        calls.append("network")
        raise AssertionError("A5 must remain offline")

    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)
    destination = tmp_path / "offline-restored"
    assert _inspect(package, attestation)["status"] == "DIRECT_RESTORE_COMPATIBLE"
    restore_backup(backup_path=package, destination=destination, compatibility=attestation,
                   forbidden_roots=[], max_total_bytes=LIMIT, max_member_count=100, restore_id="restore-offline",
                   created_at=UTC)
    verify_restored_state(backup_path=package, restored_path=destination,
                          compatibility=attestation, max_total_bytes=LIMIT,
                          max_member_count=100)
    assert calls == []
