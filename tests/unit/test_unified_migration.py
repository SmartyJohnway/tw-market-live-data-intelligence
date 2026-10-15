from __future__ import annotations

import hashlib
import json
import socket
from dataclasses import replace
from pathlib import Path

import pytest

from server.services import unified_backup as backup
from server.services import unified_migration as migration
from server.services.unified_restore import (
    CompatibilityAttestation,
    DEFAULT_COMPATIBILITY_CONTRACT,
    RestoreCompatibilityContract,
    restore_backup,
)


LIMIT = 2_000_000
UTC = "2026-10-15T00:00:00Z"
FAMILY = "security_master_active_release_pointer"
MIGRATION_ID = "test-only-synthetic-v0-to-v1"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _source(tmp_path: Path):
    origin = tmp_path / "original"
    origin.mkdir()
    content = b"legacy-state\n"
    (origin / "state.bin").write_bytes(content)
    package = tmp_path / "a4-source"
    item = backup.BackupMember(
        "active-pointer", FAMILY, "origin", "state.bin", "members/state.bin",
        "binding-source", True, expected_sha256=_sha(content))
    plan = backup.plan_backup(backup_tier="CORE", roots=[backup.BackupRoot("origin", origin)],
                              members=[item], source_state_identity="state-one",
                              max_total_bytes=LIMIT)
    backup.create_backup(plan, destination=package, backup_id="backup-one", created_at=UTC)
    manifest = json.loads((package / backup.MANIFEST_NAME).read_text(encoding="utf-8"))
    compatibility = CompatibilityAttestation(
        manifest["manifest_integrity"]["sha256"], {"active-pointer": "0"})
    contract = RestoreCompatibilityContract(
        DEFAULT_COMPATIBILITY_CONTRACT.product_identity,
        DEFAULT_COMPATIBILITY_CONTRACT.restore_contract_version,
        DEFAULT_COMPATIBILITY_CONTRACT.supported_backup_formats,
        DEFAULT_COMPATIBILITY_CONTRACT.supported_manifest_versions,
        DEFAULT_COMPATIBILITY_CONTRACT.supported_state_family_versions,
        {(FAMILY, "0"): MIGRATION_ID})
    registry = (migration.MigrationDefinition(
        MIGRATION_ID, FAMILY, "0", "1", "TEST_ONLY_SYNTHETIC_TRANSFORMER",
        "unit-test-only synthetic bytes transformer", ("active-pointer",),
        lambda members: {**members, "state.bin": members["state.bin"].upper()}),)
    return origin, package, compatibility, contract, registry


def _preview(tmp_path: Path, package, compatibility, contract, registry):
    return migration.preview_migration(
        backup_path=package, compatibility=compatibility, contract=contract,
        migration_id=MIGRATION_ID, migration_plan_id="plan-one",
        created_at=UTC,
        max_total_bytes=LIMIT, max_member_count=10, max_changed_members=2,
        forbidden_roots=[],
        _test_only_registry=registry)


def test_inspection_reverifies_a4_and_a5_and_known_watchlist_path_is_not_implemented(tmp_path: Path):
    _, package, compatibility, _, _ = _source(tmp_path)
    with pytest.raises(migration.MigrationError, match="MIGRATION_PATH_NOT_IMPLEMENTED"):
        migration.inspect_migration(
            backup_path=package, compatibility=compatibility,
            contract=RestoreCompatibilityContract(
                DEFAULT_COMPATIBILITY_CONTRACT.product_identity,
                DEFAULT_COMPATIBILITY_CONTRACT.restore_contract_version,
                DEFAULT_COMPATIBILITY_CONTRACT.supported_backup_formats,
                DEFAULT_COMPATIBILITY_CONTRACT.supported_manifest_versions,
                DEFAULT_COMPATIBILITY_CONTRACT.supported_state_family_versions,
                {(FAMILY, "0"): MIGRATION_ID}),
            max_total_bytes=LIMIT, max_member_count=10, forbidden_roots=[])
    # A migration identifier absent from the production A6 registry is closed.
    assert [row.migration_id for row in migration.MIGRATION_REGISTRY] == [migration.WATCHLIST_V0_TO_V1]
    assert migration.MIGRATION_REGISTRY[0].implementation_status == "KNOWN_NOT_IMPLEMENTED"


def test_preview_plan_is_deterministic_and_bound_to_a4_a5_and_registry(tmp_path: Path):
    _, package, compatibility, contract, registry = _source(tmp_path)
    first = _preview(tmp_path, package, compatibility, contract, registry)
    second = _preview(tmp_path, package, compatibility, contract, registry)
    assert first == second
    assert first.to_dict()["checkpoint_kind"] == "SOURCE_A4_BACKUP"
    assert first.to_dict()["source_selection_scope"] == "EXPLICIT_DECLARED_MEMBERS_ONLY"
    assert "source_restore_receipt_sha256" not in first.to_dict()
    assert first.to_dict()["source_backup_manifest_sha256"] == compatibility.backup_manifest_sha256


def test_missing_registry_required_checkpoint_member_fails_closed(tmp_path: Path):
    _, package, compatibility, contract, registry = _source(tmp_path)
    incomplete = (replace(registry[0], required_member_ids=("missing-required-member",)),)
    with pytest.raises(migration.MigrationError, match="MIGRATION_CHECKPOINT_INCOMPLETE"):
        _preview(tmp_path, package, compatibility, contract, incomplete)


def test_test_only_transformer_copy_on_write_verify_and_rollback(tmp_path: Path):
    _, package, compatibility, contract, registry = _source(tmp_path)
    plan = _preview(tmp_path, package, compatibility, contract, registry)
    package_before = {item.relative_to(package).as_posix(): _sha(item.read_bytes())
                      for item in package.rglob("*") if item.is_file()}
    migrated = tmp_path / "migrated"
    result = migration.apply_migration(
        plan=plan, backup_path=package, compatibility=compatibility, contract=contract,
        destination=migrated, forbidden_roots=[], max_total_bytes=LIMIT,
        max_member_count=10, max_changed_members=2, migration_run_id="run-one",
        created_at=UTC, _test_only_registry=registry)
    assert result["status"] == "MIGRATION_APPLIED_VERIFIED"
    assert (migrated / "state.bin").read_bytes() == b"LEGACY-STATE\n"
    assert migration.verify_migrated_state(
        migration_root=migrated, plan=plan, backup_path=package,
        compatibility=compatibility, contract=contract, max_total_bytes=LIMIT,
        max_member_count=10, max_changed_members=2,
        forbidden_roots=[],
        _test_only_registry=registry)["status"] == "MIGRATION_APPLIED_VERIFIED"
    rolled_back = tmp_path / "rollback-candidate"
    rollback = migration.rollback_migration(
        migration_root=migrated, destination=rolled_back, plan=plan,
        backup_path=package, compatibility=compatibility, contract=contract,
        forbidden_roots=[], max_total_bytes=LIMIT, max_member_count=10,
        max_changed_members=2, rollback_id="rollback-one", created_at=UTC,
        _test_only_registry=registry)
    assert rollback["status"] == "ROLLBACK_COMPLETED"
    assert (rolled_back / "state.bin").read_bytes() == b"legacy-state\n"
    assert migration.verify_rollback(
        rollback_root=rolled_back, migration_root=migrated, plan=plan,
        backup_path=package, compatibility=compatibility, contract=contract,
        max_total_bytes=LIMIT, max_member_count=10, max_changed_members=2,
        forbidden_roots=[],
        _test_only_registry=registry)["status"] == "ROLLBACK_VERIFIED"
    rollback_receipt_path = rolled_back / migration.ROLLBACK_RECEIPT
    rollback_receipt = json.loads(rollback_receipt_path.read_text(encoding="utf-8"))
    rollback_receipt["rollback_scope"] = "WHOLE_INSTALLATION_COMPLETE"
    rollback_receipt["receipt_integrity"] = migration._integrity(rollback_receipt, "receipt_integrity")
    rollback_receipt_path.write_bytes(migration._canonical(rollback_receipt) + b"\n")
    with pytest.raises(migration.MigrationError, match="ROLLBACK_VERIFICATION_FAILED"):
        migration.verify_rollback(
            rollback_root=rolled_back, migration_root=migrated, plan=plan,
            backup_path=package, compatibility=compatibility, contract=contract,
            max_total_bytes=LIMIT, max_member_count=10, max_changed_members=2,
            forbidden_roots=[], _test_only_registry=registry)
    package_after = {item.relative_to(package).as_posix(): _sha(item.read_bytes())
                     for item in package.rglob("*") if item.is_file()}
    assert package_after == package_before


def test_rollback_receipt_checkpoint_kind_cannot_be_laundered(tmp_path: Path):
    _, package, compatibility, contract, registry = _source(tmp_path)
    plan = _preview(tmp_path, package, compatibility, contract, registry)
    migrated = tmp_path / "migrated-checkpoint"
    migration.apply_migration(
        plan=plan, backup_path=package, compatibility=compatibility, contract=contract,
        destination=migrated, forbidden_roots=[], max_total_bytes=LIMIT,
        max_member_count=10, max_changed_members=2, migration_run_id="run-checkpoint",
        created_at=UTC, _test_only_registry=registry)
    rolled_back = tmp_path / "rollback-checkpoint"
    migration.rollback_migration(
        migration_root=migrated, destination=rolled_back, plan=plan,
        backup_path=package, compatibility=compatibility, contract=contract,
        forbidden_roots=[], max_total_bytes=LIMIT, max_member_count=10,
        max_changed_members=2, rollback_id="rollback-checkpoint", created_at=UTC,
        _test_only_registry=registry)
    receipt_path = rolled_back / migration.ROLLBACK_RECEIPT
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["checkpoint_kind"] = "FAKE_CHECKPOINT"
    receipt["receipt_integrity"] = migration._integrity(receipt, "receipt_integrity")
    receipt_path.write_bytes(migration._canonical(receipt) + b"\n")
    with pytest.raises(migration.MigrationError, match="ROLLBACK_VERIFICATION_FAILED"):
        migration.verify_rollback(
            rollback_root=rolled_back, migration_root=migrated, plan=plan,
            backup_path=package, compatibility=compatibility, contract=contract,
            max_total_bytes=LIMIT, max_member_count=10, max_changed_members=2,
            forbidden_roots=[], _test_only_registry=registry)


def test_rehashed_tampered_plan_cannot_change_migration_or_checkpoint_binding(tmp_path: Path):
    _, package, compatibility, contract, registry = _source(tmp_path)
    plan = _preview(tmp_path, package, compatibility, contract, registry)
    payload = plan.to_dict()
    payload["migration_id"] = "another-path"
    payload["plan_integrity"] = migration._integrity(payload, "plan_integrity")
    tampered = migration._plan_from_payload(payload)
    with pytest.raises(migration.MigrationError, match="MIGRATION_PATH_NOT_IMPLEMENTED|MIGRATION_PLAN_INVALID"):
        migration._validate_plan(tampered, backup_path=package, compatibility=compatibility,
                                 contract=contract, max_total_bytes=LIMIT,
                                 max_member_count=10, registry=registry)


def test_rehashed_plan_operation_metadata_cannot_be_laundered(tmp_path: Path):
    _, package, compatibility, contract, registry = _source(tmp_path)
    plan = _preview(tmp_path, package, compatibility, contract, registry)
    for field, value in (
        ("compatibility_contract_version", "fake-contract.v9"),
        ("created_at", "not-a-timestamp"),
        ("migration_plan_id", "invalid plan id"),
    ):
        payload = plan.to_dict()
        payload[field] = value
        payload["plan_integrity"] = migration._integrity(payload, "plan_integrity")
        tampered = migration._plan_from_payload(payload)
        with pytest.raises(migration.MigrationError, match="MIGRATION_PLAN_INVALID"):
            migration._validate_plan(
                tampered, backup_path=package, compatibility=compatibility,
                contract=contract, max_total_bytes=LIMIT, max_member_count=10,
                forbidden_roots=[], registry=registry)


def test_migration_receipt_outcome_cannot_be_laundered_by_self_hash(tmp_path: Path):
    _, package, compatibility, contract, registry = _source(tmp_path)
    plan = _preview(tmp_path, package, compatibility, contract, registry)
    migrated = tmp_path / "migrated"
    migration.apply_migration(
        plan=plan, backup_path=package, compatibility=compatibility, contract=contract,
        destination=migrated, forbidden_roots=[], max_total_bytes=LIMIT,
        max_member_count=10, max_changed_members=2, migration_run_id="run-tamper",
        created_at=UTC, _test_only_registry=registry)
    receipt_path = migrated / migration.MIGRATION_RECEIPT
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["migration_outcome"] = "DIRECT_RESTORE_COMPATIBLE"
    receipt["receipt_integrity"] = migration._integrity(receipt, "receipt_integrity")
    receipt_path.write_bytes(migration._canonical(receipt) + b"\n")
    with pytest.raises(migration.MigrationError, match="MIGRATION_VERIFICATION_FAILED"):
        migration.verify_migrated_state(
            migration_root=migrated, plan=plan, backup_path=package,
            compatibility=compatibility, contract=contract, max_total_bytes=LIMIT,
            max_member_count=10, max_changed_members=2,
            forbidden_roots=[],
            _test_only_registry=registry)


@pytest.mark.parametrize("raw", ["../escape", "CON", "file:stream", "name.", "name ", "//server/share"])
def test_migration_destination_rejects_unsafe_paths(tmp_path: Path, raw: str):
    source = tmp_path / "source"
    source.mkdir()
    with pytest.raises(migration.MigrationError, match="MIGRATION_TARGET_UNSAFE"):
        migration._destination(Path(raw), source=source, forbidden_roots=[])


def test_production_known_not_implemented_dispatch_writes_nothing(tmp_path: Path, monkeypatch):
    _, package, compatibility, contract, registry = _source(tmp_path)
    test_plan = _preview(tmp_path, package, compatibility, contract, registry)
    production_plan = replace(test_plan, migration_id=migration.WATCHLIST_V0_TO_V1)
    monkeypatch.setattr(migration, "_validate_plan", lambda *_args, **_kw: ({"manifest": {}}, {}))
    destination = tmp_path / "must-not-exist"
    with pytest.raises(migration.MigrationError, match="MIGRATION_PATH_NOT_IMPLEMENTED"):
        migration.apply_migration(
            plan=production_plan, backup_path=package, compatibility=compatibility,
            contract=contract, destination=destination, forbidden_roots=[],
            max_total_bytes=LIMIT, max_member_count=10, max_changed_members=2,
            migration_run_id="run-blocked", created_at=UTC)
    assert not destination.exists()
    assert not list(tmp_path.glob(".*.migration-staging-*"))


def test_inspection_uses_no_network_and_rejects_unbound_attestation(tmp_path: Path, monkeypatch):
    _, package, _, _, _ = _source(tmp_path)
    manifest = json.loads((package / backup.MANIFEST_NAME).read_text(encoding="utf-8"))
    compatibility = CompatibilityAttestation(
        manifest["manifest_integrity"]["sha256"], {"active-pointer": "1"})
    def denied(*_args, **_kwargs):
        raise AssertionError("network access is forbidden")
    monkeypatch.setattr(socket, "socket", denied)
    monkeypatch.setattr(socket, "create_connection", denied)
    result = migration.inspect_migration(
        backup_path=package, compatibility=compatibility, contract=DEFAULT_COMPATIBILITY_CONTRACT,
        max_total_bytes=LIMIT, max_member_count=10, forbidden_roots=[])
    assert result["status"] == "MIGRATION_NOT_REQUIRED"
    bad = CompatibilityAttestation("0" * 64, compatibility.state_family_versions)
    with pytest.raises(migration.MigrationError, match="MIGRATION_SOURCE_UNVERIFIED"):
        migration.inspect_migration(
            backup_path=package, compatibility=bad, contract=DEFAULT_COMPATIBILITY_CONTRACT,
            max_total_bytes=LIMIT, max_member_count=10, forbidden_roots=[])


def test_newer_unknown_oversize_and_tampered_a4_inputs_fail_closed(tmp_path: Path):
    _, package, _, _, _ = _source(tmp_path)
    manifest = json.loads((package / backup.MANIFEST_NAME).read_text(encoding="utf-8"))
    for version, expected in [("2", "UNSUPPORTED_NEWER_STATE"),
                              ("future", "RESTORE_COMPATIBILITY_UNKNOWN")]:
        attestation = CompatibilityAttestation(
            manifest["manifest_integrity"]["sha256"], {"active-pointer": version})
        with pytest.raises(migration.MigrationError, match=expected):
            migration.inspect_migration(
                backup_path=package, compatibility=attestation,
                max_total_bytes=LIMIT, max_member_count=10, forbidden_roots=[])
    attestation = CompatibilityAttestation(
        manifest["manifest_integrity"]["sha256"], {"active-pointer": "1"})
    with pytest.raises(migration.MigrationError, match="MIGRATION_RESOURCE_LIMIT_EXCEEDED"):
        migration.inspect_migration(
            backup_path=package, compatibility=attestation, max_total_bytes=1,
            max_member_count=10, forbidden_roots=[])
    (package / "members" / "state.bin").write_bytes(b"tampered")
    with pytest.raises(migration.MigrationError, match="MIGRATION_SOURCE_UNVERIFIED"):
        migration.inspect_migration(
            backup_path=package, compatibility=attestation, max_total_bytes=LIMIT,
            max_member_count=10, forbidden_roots=[])


def test_a5_migration_classification_does_not_materialize_restore(tmp_path: Path):
    _, package, compatibility, contract, _ = _source(tmp_path)
    destination = tmp_path / "no-a5-restore"
    restore_result = restore_backup(
        backup_path=package, destination=destination, compatibility=compatibility,
        contract=contract, forbidden_roots=[], max_total_bytes=LIMIT,
        max_member_count=10, restore_id="restore-blocked", created_at=UTC)
    assert restore_result["restore_status"] == "MIGRATION_REQUIRED"
    assert not destination.exists()
