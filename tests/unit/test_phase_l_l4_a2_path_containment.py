from __future__ import annotations

import os
import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import m8r_filesystem_safety as fs
from scripts import m8r_06_03_execute_once as execute_once
from scripts.m8r_09_persistent_watchlists import PersistentWatchlistStore, WatchlistError
from scripts import tw_market_lifecycle as lifecycle
from server import operational_diagnostics as diagnostics
from server.services import unified_mode_c
from server.services.unified_mode_c import ModeCError


def _fake_reparse_stat():
    return SimpleNamespace(
        st_mode=stat.S_IFDIR | 0o700,
        st_file_attributes=0x400,
        st_dev=1,
        st_ino=999,
    )


def _mark_reparse(monkeypatch, target: Path):
    original = Path.lstat

    def fake_lstat(path):
        if path == target:
            return _fake_reparse_stat()
        return original(path)

    monkeypatch.setattr(Path, "lstat", fake_lstat)


def test_watchlist_explicit_external_authority_root_is_supported(tmp_path):
    external = tmp_path / "installation-state" / "watchlists"
    store = PersistentWatchlistStore(root=external)
    assert store.root == external.resolve()
    assert store.path.is_file()


def test_watchlist_root_symlink_is_rejected(tmp_path):
    real = tmp_path / "real"
    real.mkdir()
    alias = tmp_path / "alias"
    try:
        alias.symlink_to(real, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("host cannot create a test symlink")
    with pytest.raises(WatchlistError) as exc:
        PersistentWatchlistStore(root=alias)
    assert exc.value.code == "WATCHLIST_STORAGE_PATH_UNSAFE"


def test_lexical_symlink_is_not_hidden_by_parent_component(tmp_path):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    target = tmp_path / "target"
    target.mkdir()
    alias = tmp_path / "alias"
    try:
        alias.symlink_to(elsewhere, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("host cannot create a test symlink")
    selected = alias / ".." / "target"
    with pytest.raises(fs.FilesystemSafetyError):
        fs.validate_authorized_root(selected)


def test_watchlist_root_windows_reparse_attribute_is_rejected(tmp_path, monkeypatch):
    root = tmp_path / "configured"
    root.mkdir()
    _mark_reparse(monkeypatch, root)
    with pytest.raises(WatchlistError) as exc:
        PersistentWatchlistStore(root=root)
    assert exc.value.code == "WATCHLIST_STORAGE_PATH_UNSAFE"


def test_watchlist_database_symlink_is_rejected_before_sqlite_open(tmp_path):
    root = tmp_path / "watchlists"
    root.mkdir()
    external_db = tmp_path / "outside.sqlite3"
    external_db.write_bytes(b"not a watchlist")
    try:
        (root / "watchlists.sqlite3").symlink_to(external_db)
    except (OSError, NotImplementedError):
        pytest.skip("host cannot create a test symlink")
    with pytest.raises(WatchlistError) as exc:
        PersistentWatchlistStore(root=root)
    assert exc.value.code == "WATCHLIST_STORAGE_PATH_UNSAFE"


def test_watchlist_database_reparse_attribute_is_rejected(tmp_path, monkeypatch):
    root = tmp_path / "watchlists"
    root.mkdir()
    leaf = root / "watchlists.sqlite3"
    leaf.write_bytes(b"placeholder")
    _mark_reparse(monkeypatch, leaf)
    with pytest.raises(WatchlistError) as exc:
        PersistentWatchlistStore(root=root)
    assert exc.value.code == "WATCHLIST_STORAGE_PATH_UNSAFE"


def test_artifact_root_and_intermediate_reparse_components_fail_closed(tmp_path, monkeypatch):
    root = tmp_path / "artifacts"
    root.mkdir()
    _mark_reparse(monkeypatch, root)
    with pytest.raises(fs.FilesystemSafetyError):
        fs.validate_authorized_root(root)

    monkeypatch.undo()
    parent = root / "nested"
    parent.mkdir()
    _mark_reparse(monkeypatch, parent)
    with pytest.raises(fs.FilesystemSafetyError):
        fs.safe_destination(root, "nested/result.json")


def test_control_package_root_preserves_lexical_path_until_validation(tmp_path, monkeypatch):
    real = tmp_path / "real-control"
    real.mkdir()
    alias = tmp_path / "control-alias"
    try:
        alias.symlink_to(real, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("host cannot create a test symlink")
    monkeypatch.setattr(execute_once, "CONTROL_ROOT", alias)
    with pytest.raises(fs.FilesystemSafetyError):
        execute_once.load_control_package("umea-v1-" + "a" * 20)
    assert list(real.iterdir()) == []


def test_artifact_existing_destination_reparse_fails_closed(tmp_path, monkeypatch):
    root = tmp_path / "artifacts"
    root.mkdir()
    leaf = root / "result.json"
    leaf.write_text("existing")
    _mark_reparse(monkeypatch, leaf)
    with pytest.raises(fs.FilesystemSafetyError):
        fs.safe_destination(root, leaf.name)


def test_mode_c_result_package_rejects_reparse_output_directory(tmp_path, monkeypatch):
    package = tmp_path / "control" / "umea-v1-test"
    output_dir = package / "ai_context"
    output_dir.mkdir(parents=True)
    _mark_reparse(monkeypatch, output_dir)
    with pytest.raises(ModeCError, match="mode_c_control_integrity_failed"):
        unified_mode_c._persisted_output_version(package)


def test_new_parent_chain_is_revalidated_after_creation(tmp_path, monkeypatch):
    root = tmp_path / "artifacts"
    root.mkdir()
    original = fs.reject_reparse_components
    observed = []

    def verify_after_create(path, *, code="path_reparse_component_forbidden"):
        candidate = Path(path)
        if candidate == root / "new" / "nested" and candidate.is_dir():
            observed.append(candidate)
        return original(path, code=code)

    monkeypatch.setattr(fs, "reject_reparse_components", verify_after_create)
    destination = fs.safe_destination(root, "new/nested/file.json", create_parent=True)
    assert destination.path.parent.is_dir()
    assert observed


def test_atomic_write_rechecks_parent_identity_before_replace(tmp_path, monkeypatch):
    root = tmp_path / "artifacts"
    root.mkdir()
    original = fs._assert_identity
    calls = []

    def fail_parent(path, expected, *, code="path_identity_changed"):
        calls.append(path)
        if len(calls) == 2:
            raise fs.FilesystemSafetyError("path_identity_changed")
        return original(path, expected, code=code)

    monkeypatch.setattr(fs, "_assert_identity", fail_parent)
    with pytest.raises(fs.FilesystemSafetyError, match="path_identity_changed"):
        fs.atomic_write_text(root, "nested/result.json", "secret")
    assert not (root / "nested" / "result.json").exists()
    assert not list((root / "nested").glob("*.tmp"))


def test_exclusive_create_preserves_no_replay(tmp_path):
    root = tmp_path / "artifacts"
    first = fs.atomic_create_text_exclusive(root, "claim/once.json", "one")
    assert first.path.read_text() == "one"
    with pytest.raises(fs.FilesystemSafetyError) as exc:
        fs.atomic_create_text_exclusive(root, "claim/once.json", "two")
    assert exc.value.code == "already_consumed_or_replayed"
    assert first.path.read_text() == "one"


def test_operational_event_unsafe_parent_is_ignored_and_safe_target_appends(tmp_path, monkeypatch):
    outside = tmp_path / "outside"
    outside.mkdir()
    link = tmp_path / "event-parent"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("host cannot create a test symlink")
    monkeypatch.setenv(diagnostics.EVENT_PATH_ENV, str(link / "events.jsonl"))
    assert diagnostics.event_path_from_env() is None
    event = diagnostics.build_event(component="test", event_code="safe", status="ok")
    assert diagnostics.emit_jsonl(event, link / "events.jsonl") is False

    safe_parent = tmp_path / "safe"
    safe_parent.mkdir()
    target = safe_parent / "events.jsonl"
    assert diagnostics.emit_jsonl(event, target) is True
    assert target.read_text(encoding="utf-8").count("\n") == 1

    external_file = tmp_path / "outside-events.jsonl"
    external_file.write_text("do not append", encoding="utf-8")
    linked_target = safe_parent / "linked-events.jsonl"
    try:
        linked_target.symlink_to(external_file)
    except (OSError, NotImplementedError):
        pytest.skip("host cannot create a test symlink")
    assert diagnostics.emit_jsonl(event, linked_target) is False
    assert external_file.read_text(encoding="utf-8") == "do not append"


def test_lifecycle_runtime_reparse_parent_rejected_before_start(tmp_path, monkeypatch):
    real = tmp_path / "runtime"
    real.mkdir()
    link = tmp_path / "runtime-link"
    try:
        link.symlink_to(real, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("host cannot create a test symlink")
    monkeypatch.setattr(lifecycle, "_owner_path", lambda _port: link / "service-8123.json")
    result = lifecycle._start("127.0.0.1", 8123)
    assert result == {"status": "START_FAILED", "reason_code": "RUNTIME_PATH_UNSAFE"}


def test_lifecycle_owner_file_symlink_is_never_read_as_authority(tmp_path):
    outside = tmp_path / "outside.json"
    outside.write_text('{"state":"running"}', encoding="utf-8")
    linked = tmp_path / "service.json"
    try:
        linked.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("host cannot create a test symlink")
    record, error = lifecycle._read_owner(linked)
    assert record is None
    assert error == "STALE_PROCESS_OWNERSHIP"


def test_lifecycle_runtime_root_is_created_as_ordinary_directory(tmp_path, monkeypatch):
    runtime_parent = tmp_path / "temp" / "tw-market-runtime" / "install"
    monkeypatch.setattr(lifecycle, "_owner_path", lambda port: runtime_parent / f"service-{port}.json")
    validated = fs.validate_authorized_root(runtime_parent)
    assert validated == runtime_parent.resolve()
    fs.reject_reparse_components(validated)
    assert validated.is_dir()


def test_reparse_detector_uses_windows_attribute_mask(tmp_path, monkeypatch):
    path = tmp_path / "ordinary-looking-dir"
    path.mkdir()
    _mark_reparse(monkeypatch, path)
    assert fs.is_reparse_or_symlink(path) is True
    with pytest.raises(fs.FilesystemSafetyError):
        fs.reject_reparse_components(path)
