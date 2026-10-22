"""Native installation integration; all state is in temporary installation roots."""
from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from unittest.mock import patch

import pytest

from scripts import tw_market_lifecycle as lifecycle
from scripts.tw_market_installation import initialize_installation, resolve_installation, enumerate_installation_state


@pytest.fixture
def home(tmp_path, monkeypatch):
    real_default = Path(os.environ["LOCALAPPDATA"]) / "TW-Market"
    original_default_exists = real_default.exists()
    selected = tmp_path / "home"
    monkeypatch.setenv("TW_MARKET_HOME", str(selected))
    for name in ("TW_MARKET_STATE_ROOT", "TW_MARKET_SECURITY_MASTER_ROOT", "TW_MARKET_WATCHLIST_ROOT", "M8R_06_03_CONTROL_ROOT", "TW_MARKET_OPERATIONAL_EVENT_PATH", "TW_MARKET_HOST", "TW_MARKET_PORT"):
        monkeypatch.delenv(name, raising=False)
    yield selected
    assert real_default.exists() == original_default_exists


@pytest.mark.parametrize("command", ["status", "doctor", "start", "stop"])
def test_preinit_commands_are_read_only(home, capsys, command):
    with patch.object(lifecycle.subprocess, "run", side_effect=AssertionError("no child checks before init")), patch.object(lifecycle, "_port_open", side_effect=AssertionError("no socket before init")):
        result = lifecycle.main([command, "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert result == (1 if command == "start" else 0)
    assert payload["status"] == "INSTALLATION_NOT_INITIALIZED"
    assert payload["installation"]["home"] == str(home)
    assert not home.exists()


def test_cli_home_context_reaches_every_child(home, tmp_path, capsys):
    alternate = tmp_path / "alternate"
    inst = initialize_installation(home=alternate)
    seen = []
    def child(args, **kwargs):
        seen.append(kwargs["env"])
        return subprocess.CompletedProcess(args, 0, json.dumps({"status": "NOT_INITIALIZED"}))
    with patch.object(lifecycle.subprocess, "run", side_effect=child), patch.object(lifecycle, "_port_open", return_value=False):
        assert lifecycle.main(["status", "--home", str(alternate), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["installation"]["installation_id"] == inst.installation_id
    assert all(env["TW_MARKET_HOME"] == str(alternate) and env["TW_MARKET_STATE_ROOT"] == str(inst.state_root) for env in seen)
    assert not home.exists()


def test_init_offline_business_state_absent_and_stable(home, capsys):
    with patch.object(lifecycle.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, '{"status":"NOT_INITIALIZED"}')):
        assert lifecycle.main(["init", "--json"]) == 0
        first = json.loads(capsys.readouterr().out)
        assert lifecycle.main(["init", "--json"]) == 0
        second = json.loads(capsys.readouterr().out)
    assert first["installation"]["installation_id"] == second["installation"]["installation_id"]
    assert first["identity"]["status"] == "NOT_INITIALIZED"
    assert not list((home / "state").rglob("*.*"))


def test_runtime_is_installation_keyed_across_app_roots(home, tmp_path):
    inst = initialize_installation()
    first = resolve_installation(app_root=tmp_path / "app1")
    second = resolve_installation(app_root=tmp_path / "app2")
    assert first.runtime_root == second.runtime_root
    assert inst.installation_id in str(first.runtime_root)
    assert lifecycle._owner_path(18000).parent == first.runtime_root
    assert lifecycle._event_path(18000).parent == home / "logs"


def test_wrong_installation_pid_marker_is_never_active(home):
    initialize_installation()
    record = {"installation_id": "old-installation", "pid": os.getpid(), "process_start_token": "token", "executable": sys.executable}
    with patch.object(lifecycle, "_identity_matches", return_value=True):
        assert lifecycle._process_matches(record) is False
        assert lifecycle._starting_creator_matches({**record, "state": "starting"}) is False


def test_fresh_init_does_not_adopt_existing_canonical_business_state(home):
    from scripts.tw_market_installation import InstallationError
    prior = home / "state" / "watchlists"
    prior.mkdir(parents=True)
    (prior / "legacy.sqlite3").write_bytes(b"do-not-adopt")
    with pytest.raises(InstallationError, match="EXISTING_STATE_REQUIRES_EXPLICIT_TRANSFER"):
        initialize_installation()
    assert not (home / "meta" / "installation.json").exists()
    assert (prior / "legacy.sqlite3").read_bytes() == b"do-not-adopt"


def test_home_ancestor_does_not_allow_metadata_under_application(home):
    from scripts.tw_market_installation import InstallationError
    with pytest.raises(InstallationError, match="PATH_INSIDE_APP_ROOT"):
        resolve_installation(home=home, app_root=home / "meta")


def test_log_override_is_visible_and_does_not_rewrite_metadata(home, tmp_path, monkeypatch):
    inst = initialize_installation()
    original = inst.installation_metadata_path.read_bytes()
    selected = tmp_path / "diagnostics" / "events.jsonl"
    monkeypatch.setenv("TW_MARKET_OPERATIONAL_EVENT_PATH", str(selected))
    resolved = resolve_installation()
    assert resolved.operational_event_path == selected
    assert resolved.diagnostics["NONCANONICAL_ROOT_OVERRIDE"]["operational_events"] == "TW_MARKET_OPERATIONAL_EVENT_PATH"
    assert inst.installation_metadata_path.read_bytes() == original
    assert not selected.exists()


def test_concurrent_init_lock_prevents_losing_state_layout(home, tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from scripts import tw_market_installation as installation
    first, second = tmp_path / "state1", tmp_path / "state2"
    with installation._home_init_lock(home, installation.APP_ROOT):
        with ThreadPoolExecutor(max_workers=2) as pool:
            jobs = [pool.submit(initialize_installation, home=home, state_root=state) for state in (first, second)]
            for job in jobs:
                with pytest.raises(installation.InstallationError, match="INIT_IN_PROGRESS"):
                    job.result()
        assert not first.exists() and not second.exists()
    chosen = initialize_installation(home=home, state_root=first)
    assert initialize_installation(home=home, state_root=first).installation_id == chosen.installation_id
    with pytest.raises(installation.InstallationError, match="STATE_ROOT_CONFLICT"):
        initialize_installation(home=home, state_root=second)
    assert not second.exists()


def test_init_refuses_unwritable_required_root_before_metadata_publication(home, monkeypatch):
    from scripts import tw_market_installation as installation
    original = installation.atomic_write_text
    def write(root, name, content, **kwargs):
        if Path(root).name == "watchlists" and name.startswith(".tw-market-init-probe-"):
            raise PermissionError("simulated Windows permission denial")
        return original(root, name, content, **kwargs)
    monkeypatch.setattr(installation, "atomic_write_text", write)
    with pytest.raises(installation.InstallationError, match="INSTALLATION_ROOT_NOT_WRITABLE"):
        initialize_installation()
    assert not (home / "meta" / "installation.json").exists()
    assert not (home / "config" / "settings.json").exists()
    assert not list(home.rglob(".tw-market-init-probe-*"))


@pytest.mark.parametrize("parent", ["meta", "config"])
def test_absent_metadata_below_reparse_parent_fails_before_read(home, tmp_path, parent):
    from scripts.tw_market_installation import InstallationError
    target = tmp_path / "other"
    target.mkdir()
    home.mkdir()
    try:
        (home / parent).symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("directory symlink creation unavailable")
    with pytest.raises(InstallationError):
        resolve_installation()
    assert not list(target.iterdir())


def test_dynamic_watchlist_and_control_root_share_installation(home):
    inst = initialize_installation()
    from scripts.m8r_09_persistent_watchlists import default_root, default_security_master_root
    assert default_root() == inst.watchlist_root
    assert default_security_master_root() == inst.security_master_root
    code = "from server.services.unified_mode_b2 import CONTROL_ROOT as a; from server.services.unified_mode_c import CONTROL_ROOT as b; from scripts.m8r_06_03_execute_once import CONTROL_ROOT as c; assert a == b == c; print(a)"
    result = subprocess.run([sys.executable, "-X", "utf8", "-B", "-c", code], capture_output=True, text=True, check=True)
    assert result.stdout.strip() == str(inst.governed_root)
    assert not list(inst.governed_root.iterdir())


def test_enumeration_does_not_adopt_source_identity_or_scan_state(home):
    inst = initialize_installation()
    roles = {row["role"]: row for row in enumerate_installation_state(inst)}
    assert roles["installation_metadata"]["portable"] is False
    assert roles["runtime"]["portable"] is False
    assert all(row["l2_binding_required"] and not row["classifier_bypass"] for row in roles.values())


def test_direct_production_factories_cannot_initialize_canonical_stores(home):
    from scripts.m8r_09_persistent_watchlists import production_store, WatchlistError
    from server.services import unified_mode_b2, unified_mode_c
    from scripts import m8r_06_03_execute_once
    with pytest.raises(WatchlistError, match="INSTALLATION_NOT_INITIALIZED"):
        production_store()
    with pytest.raises(unified_mode_b2.ModeB2Error, match="INSTALLATION_NOT_INITIALIZED"):
        unified_mode_b2._control_root()
    with pytest.raises(Exception, match="INSTALLATION_NOT_INITIALIZED"):
        m8r_06_03_execute_once.load_control_package("umea-v1-" + "a" * 20)
    with pytest.raises(unified_mode_c.ModeCError, match="INSTALLATION_NOT_INITIALIZED"):
        unified_mode_c._load_verified("umea-v1-" + "a" * 20)
    assert not home.exists()


def test_initialized_sm_absent_real_start_status_stop(home):
    inst = initialize_installation()
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    def cli(command):
        p = subprocess.run([sys.executable, "-X", "utf8", "-B", "-m", "scripts.tw_market", command, "--home", str(home), "--port", str(port), "--json"], capture_output=True, text=True, timeout=60)
        return p, json.loads(p.stdout)
    try:
        process, started = cli("start")
        assert process.returncode == 0, started
        assert started["status"] == "STARTED"
        process, duplicate = cli("start")
        assert duplicate["status"] == "ALREADY_RUNNING"
        process, status = cli("status")
        assert process.returncode == 0
        assert status["installation"]["installation_status"] == "READY"
        assert status["identity"]["status"] == "NOT_INITIALIZED"
        assert status["service"]["alive"] is True
        assert Path(status["paths"]["ownership_file"]).parent == inst.runtime_root
    finally:
        process, stopped = cli("stop")
        assert process.returncode == 0, stopped
    assert not (inst.runtime_root / f"service-{port}.json").exists()
    assert not list(inst.security_master_root.iterdir())
