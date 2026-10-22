from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.tw_market_installation import (
    InstallationError,
    effective_root,
    enumerate_installation_state,
    initialize_installation,
    resolve_installation,
)


def env(tmp_path, **extra):
    values = {"LOCALAPPDATA": str(tmp_path / "local")}
    values.update({k: str(v) for k, v in extra.items()})
    return values


def test_home_precedence_and_app_separation(tmp_path):
    app = tmp_path / "app"
    cli = tmp_path / "cli"
    chosen = resolve_installation(home=cli, app_root=app, environ=env(tmp_path, TW_MARKET_HOME=tmp_path / "env"))
    assert chosen.home == cli
    assert chosen.state_root == cli / "state"
    with pytest.raises(InstallationError):
        resolve_installation(home=app / "state", app_root=app, environ=env(tmp_path))


def test_preinit_is_read_only_and_require_initialized(tmp_path):
    home = tmp_path / "home"
    inst = resolve_installation(home=home, app_root=tmp_path / "app", environ=env(tmp_path))
    assert inst.installation_status == "INSTALLATION_NOT_INITIALIZED"
    assert not home.exists()
    with pytest.raises(InstallationError) as exc:
        inst.require_initialized()
    assert exc.value.code == "INSTALLATION_NOT_INITIALIZED"


def test_initialize_is_idempotent_and_preserves_identity_and_settings(tmp_path):
    home, app = tmp_path / "home", tmp_path / "app"
    first = initialize_installation(home=home, app_root=app, host="localhost", port=8123, environ=env(tmp_path))
    settings = first.settings_path.read_text(encoding="utf-8")
    second = initialize_installation(home=home, app_root=app, environ=env(tmp_path))
    assert second.installation_id == first.installation_id
    assert second.state_root == first.state_root
    assert second.settings_path.read_text(encoding="utf-8") == settings
    assert first.effective_service_port == 8123
    assert second.effective_service_port == 8000
    assert json.loads(settings)["service"] == {"host": "127.0.0.1", "port": 8000}


def test_state_root_conflict_fails_closed(tmp_path):
    home = tmp_path / "home"
    initialize_installation(home=home, state_root=tmp_path / "state-a", app_root=tmp_path / "app", environ=env(tmp_path))
    with pytest.raises(InstallationError) as exc:
        resolve_installation(home=home, state_root=tmp_path / "state-b", app_root=tmp_path / "app", environ=env(tmp_path))
    assert exc.value.code == "STATE_ROOT_CONFLICT"


@pytest.mark.parametrize("payload", ["{", '{"schema_version": true}', '{"schema_version": 2, "service": {}}', '{"schema_version": 1, "home": "x", "service": {}}'])
def test_malformed_or_forbidden_settings_fail_even_with_cli(tmp_path, payload):
    home = tmp_path / "home"
    path = home / "config" / "settings.json"
    path.parent.mkdir(parents=True)
    path.write_text(payload, encoding="utf-8")
    with pytest.raises(InstallationError):
        resolve_installation(home=home, host="127.0.0.1", port=8000, app_root=tmp_path / "app", environ=env(tmp_path))


def test_settings_cli_env_precedence_and_bounds(tmp_path):
    home, app = tmp_path / "home", tmp_path / "app"
    initialize_installation(home=home, app_root=app, environ=env(tmp_path))
    (home / "config" / "settings.json").write_text(json.dumps({"schema_version": 1, "service": {"host": "localhost", "port": 8010}}), encoding="utf-8")
    chosen = resolve_installation(home=home, host="127.0.0.1", port=8020, app_root=app, environ=env(tmp_path, TW_MARKET_HOST="::1", TW_MARKET_PORT="8030"))
    assert (chosen.effective_service_host, chosen.effective_service_port) == ("127.0.0.1", 8020)
    with pytest.raises(InstallationError):
        resolve_installation(home=home, port=0, app_root=app, environ=env(tmp_path))


@pytest.mark.parametrize("service", [{"host": "127.0.0.1"}, {"port": 8000}])
def test_persisted_settings_require_host_and_port(service, tmp_path):
    home = tmp_path / "home"
    path = home / "config" / "settings.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"schema_version": 1, "service": service}), encoding="utf-8")
    with pytest.raises(InstallationError) as exc:
        resolve_installation(home=home, app_root=tmp_path / "app", environ=env(tmp_path))
    assert exc.value.code == "MALFORMED_SETTINGS"


def test_legacy_root_overrides_are_explicitly_diagnosed(tmp_path):
    roots = {"TW_MARKET_SECURITY_MASTER_ROOT": tmp_path / "sm", "TW_MARKET_WATCHLIST_ROOT": tmp_path / "wl", "M8R_06_03_CONTROL_ROOT": tmp_path / "gov"}
    inst = resolve_installation(home=tmp_path / "home", app_root=tmp_path / "app", environ=env(tmp_path, **roots))
    assert inst.security_master_root == roots["TW_MARKET_SECURITY_MASTER_ROOT"]
    assert set(inst.diagnostics["NONCANONICAL_ROOT_OVERRIDE"]) == {"security_master", "watchlists", "governed"}
    assert effective_root("watchlists", installation=inst) == roots["TW_MARKET_WATCHLIST_ROOT"]
    assert effective_root("governed", explicit=tmp_path / "explicit", installation=inst) == tmp_path / "explicit"


def test_state_roles_are_fixed_and_non_discovering(tmp_path):
    inst = initialize_installation(home=tmp_path / "home", app_root=tmp_path / "app", environ=env(tmp_path))
    roles = enumerate_installation_state(inst)
    assert {entry["role"] for entry in roles} == {"installation_metadata", "settings", "security_master", "watchlists", "governed", "cache", "logs", "runtime", "temp"}
    assert all("backup" in entry and "portable" in entry for entry in roles)


def test_metadata_is_strict_and_stable(tmp_path):
    home, app = tmp_path / "home", tmp_path / "app"
    inst = initialize_installation(home=home, app_root=app, environ=env(tmp_path))
    metadata = json.loads(inst.installation_metadata_path.read_text(encoding="utf-8"))
    metadata["installation_schema_version"] = True
    inst.installation_metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    with pytest.raises(InstallationError):
        resolve_installation(home=home, app_root=app, environ=env(tmp_path))


def test_failed_exclusive_publication_leaves_no_partial_metadata(tmp_path):
    home, app = tmp_path / "home", tmp_path / "app"
    lock = home / "meta" / ".installation.json.init-lock"
    lock.parent.mkdir(parents=True)
    lock.write_text("in-flight", encoding="utf-8")
    with pytest.raises(InstallationError) as exc:
        initialize_installation(home=home, app_root=app, environ=env(tmp_path))
    assert exc.value.code == "CONCURRENT_INITIALIZATION"
    assert not (home / "meta" / "installation.json").exists()
