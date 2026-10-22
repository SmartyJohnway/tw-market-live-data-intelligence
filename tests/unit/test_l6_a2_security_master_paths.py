from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.m8r_06_security_master_candidate_paths import (
    cache_security_master_root,
    retained_source_bundle_dir,
    runtime_index_dir,
    temp_security_master_root,
)


class _Installation:
    cache_root = Path("C:/Users/example/TW-Market/cache")
    temp_root = Path("C:/Users/example/TW-Market/tmp")
    security_master_root = Path("C:/Users/example/TW-Market/state/security-master")


def test_modern_derived_roots_are_installation_local(tmp_path: Path) -> None:
    installation = _Installation()
    candidate = "m8r06-01b-20990101T000000Z"

    assert cache_security_master_root(tmp_path, installation=installation) == (
        installation.cache_root / "security-master"
    )
    assert temp_security_master_root(tmp_path, installation=installation) == (
        installation.temp_root / "security-master"
    )
    assert runtime_index_dir(tmp_path, candidate, installation=installation) == (
        installation.cache_root / "security-master" / candidate
    )
    assert retained_source_bundle_dir(installation.security_master_root, candidate) == (
        installation.security_master_root / "source-bundles" / candidate
    )


def test_explicit_historical_roots_remain_unchanged(tmp_path: Path) -> None:
    candidate = "m8r06-01b-20990101T000000Z"
    explicit_cache = tmp_path / "legacy-cache"
    explicit_temp = tmp_path / "legacy-temp"
    assert cache_security_master_root(tmp_path, explicit=explicit_cache) == explicit_cache
    assert temp_security_master_root(tmp_path, explicit=explicit_temp) == explicit_temp
    assert runtime_index_dir(tmp_path, candidate) == (
        tmp_path / "data" / "security_master" / "runtime_identity_indexes" / candidate
    )


def test_failure_report_can_stay_in_staging_without_app_root_write(tmp_path: Path) -> None:
    from scripts import m8r_06_01b_materialize_production_inputs as materializer

    bundle_id = "m8r06-01b-20990101T000000Z"
    bundle_dir = tmp_path / "staging" / bundle_id
    materializer._write_failure_report(
        bundle_dir,
        "2099-01-01T00:00:00+00:00",
        "2099-01-01",
        bundle_id,
        [],
        "BLOCKED_BY_TEST",
        "BOOTSTRAP_TEST",
        repo_root=tmp_path / "staging",
    )
    reports = list((tmp_path / "staging").rglob("materialization_report.json"))
    assert reports
    payload = json.loads(reports[0].read_text(encoding="utf-8"))
    assert payload["production_input_bundle_created"] is False
    assert not (materializer.ROOT / "docs" / "reviews" / "security_master_candidates" / bundle_id).exists()


def test_direct_materializer_default_fails_closed_when_installation_resolution_fails(monkeypatch) -> None:
    from scripts import m8r_06_01b_materialize_production_inputs as materializer
    from scripts import tw_market_installation

    def fail(**_kwargs):
        raise tw_market_installation.InstallationError("HOME_UNAVAILABLE")

    monkeypatch.setattr(tw_market_installation, "resolve_installation", fail)
    monkeypatch.setattr(materializer, "BUNDLE_BASE", materializer.ROOT / "data" / "security_master" / "input_bundles")
    with pytest.raises(tw_market_installation.InstallationError, match="HOME_UNAVAILABLE"):
        materializer._resolve_bundle_base(None)


def test_direct_materializer_rejects_reparse_bundle_root(tmp_path: Path) -> None:
    from scripts import m8r_06_01b_materialize_production_inputs as materializer
    from scripts.m8r_filesystem_safety import FilesystemSafetyError

    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "bundle-link"
    try:
        os.symlink(target, link, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("directory symlink creation is unavailable")
    with pytest.raises(FilesystemSafetyError):
        materializer._resolve_bundle_base(link)


def test_materializer_rejects_forged_authority_root_flags(tmp_path: Path) -> None:
    from scripts import m8r_06_01b_materialize_production_inputs as materializer

    with pytest.raises(SystemExit):
        materializer.main(
            [
                "--installation-temp-root",
                str(tmp_path / "temp-root"),
                "--app-root",
                str(tmp_path / "app-root"),
            ]
        )


def test_direct_materializer_rejects_divergent_report_root(monkeypatch, tmp_path: Path) -> None:
    from scripts import m8r_06_01b_materialize_production_inputs as materializer
    import scripts.tw_market_installation as installation_module

    class ReadyInstallation:
        temp_root = tmp_path / "temp-root"

        def require_initialized(self):
            return self

    monkeypatch.setattr(installation_module, "resolve_installation", lambda: ReadyInstallation())
    bundle_root = tmp_path / "temp-root" / "security-master" / "staging"
    report_root = tmp_path / "other"
    with pytest.raises(RuntimeError, match="REPORT_ROOT_MUST_EQUAL_BOUNDED_BUNDLE_ROOT"):
        materializer.main(
            ["--bundle-root", str(bundle_root), "--report-root", str(report_root)]
        )
    assert not report_root.exists()


def test_materializer_cli_bundle_root_requires_initialized_installation(monkeypatch, tmp_path: Path) -> None:
    from scripts import m8r_06_01b_materialize_production_inputs as materializer
    import scripts.tw_market_installation as installation_module

    monkeypatch.setenv("TW_MARKET_HOME", str(tmp_path / "fresh-installation"))
    monkeypatch.delenv("TW_MARKET_STATE_ROOT", raising=False)
    arbitrary = tmp_path / "arbitrary"
    with pytest.raises(installation_module.InstallationError):
        materializer.main(["--bundle-root", str(arbitrary)])
    assert not arbitrary.exists()


def test_production_bundle_root_must_be_installation_temp_and_outside_app(tmp_path: Path) -> None:
    from scripts import m8r_06_01b_materialize_production_inputs as materializer

    temp_root = tmp_path / "installation-temp" / "security-master"
    app_root = tmp_path / "application"
    app_root.mkdir()
    with pytest.raises(ValueError, match="BUNDLE_ROOT_OUTSIDE_INSTALLATION_TEMP"):
        materializer._resolve_bundle_base(
            tmp_path / "other",
            installation_temp_root=temp_root,
            app_root=app_root,
        )
    assert not (tmp_path / "other").exists()
    with pytest.raises(ValueError, match="BUNDLE_ROOT_INSIDE_APPLICATION_ROOT"):
        materializer._resolve_bundle_base(
            app_root / "staging",
            installation_temp_root=app_root,
            app_root=app_root,
        )
    assert not (app_root / "staging").exists()


def test_default_loader_does_not_adopt_preinit_canonical_bytes(monkeypatch, tmp_path: Path) -> None:
    from scripts import m8r_06_01c2_mode_a_security_master_loader as loader
    import scripts.tw_market_installation as installation_module

    rogue_root = tmp_path / "state" / "security-master"
    rogue_root.mkdir(parents=True)
    (rogue_root / "active.json").write_text('{"release_id":"rogue"}', encoding="utf-8")
    install = type(
        "PreInitInstallation",
        (),
        {
            "security_master_root": rogue_root,
            "installation_status": "INSTALLATION_NOT_INITIALIZED",
            "installation_id": None,
            "require_initialized": lambda self: (_ for _ in ()).throw(
                installation_module.InstallationError("INSTALLATION_NOT_INITIALIZED")
            ),
        },
    )()
    monkeypatch.setattr(installation_module, "resolve_installation", lambda **_kwargs: install)
    loader.reset_production_mode_a_security_master_for_tests()
    with pytest.raises(loader.ModeASecurityMasterUnavailable) as exc:
        loader.load_active_mode_a_security_master()
    assert exc.value.reason_code == "INSTALLATION_NOT_INITIALIZED"


def test_unqualified_live_candidate_is_never_retained(monkeypatch, tmp_path: Path) -> None:
    from scripts import manage_security_master as manager
    import scripts.tw_market_installation as installation_module

    temp_root = tmp_path / "temp"
    install = SimpleNamespace(
        home=tmp_path / "home",
        state_root=tmp_path / "state",
        security_master_root=tmp_path / "state" / "security-master",
        temp_root=temp_root,
        installation_status="READY",
        installation_id="test-installation",
        diagnostics={},
        require_initialized=lambda: install,
    )
    monkeypatch.setattr(installation_module, "resolve_installation", lambda **_kwargs: install)
    bundle = temp_root / "security-master" / "m8r06-01b-20990101T000000Z"
    bundle.mkdir(parents=True)
    (bundle / "dryrun_snapshot.json").write_text(json.dumps({"records": []}), encoding="utf-8")

    class Success:
        returncode = 0

    monkeypatch.setattr(manager.subprocess, "run", lambda *args, **kwargs: Success())
    monkeypatch.setattr(manager, "build_candidate_release", lambda **_kwargs: tmp_path / "candidate")
    monkeypatch.setattr(manager, "qualify_candidate_release", lambda **_kwargs: (None, tmp_path / "rejected"))
    assert manager.main(["update", "--root", str(install.security_master_root), "--live"]) == 1
    assert not (install.security_master_root / "source-bundles").exists()


def test_staged_candidate_must_be_direct_child_of_temp_root(tmp_path: Path) -> None:
    from scripts import manage_security_master as manager
    from scripts.m8r_08g_security_master_releases import LocalSecurityMasterError

    staging = tmp_path / "temp" / "security-master"
    bundle = staging / "nested" / "m8r06-01b-20990101T000000Z"
    bundle.mkdir(parents=True)
    with pytest.raises(LocalSecurityMasterError, match="staged_candidate_outside_temp_root"):
        manager._validate_staged_candidate(bundle, staging)


def test_staged_candidate_symlink_is_rejected_when_supported(tmp_path: Path) -> None:
    from scripts import manage_security_master as manager
    from scripts.m8r_08g_security_master_releases import LocalSecurityMasterError

    staging = tmp_path / "temp" / "security-master"
    staging.mkdir(parents=True)
    target = tmp_path / "outside"
    target.mkdir()
    link = staging / "m8r06-01b-20990101T000000Z"
    try:
        os.symlink(target, link, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("directory symlink creation is unavailable")
    with pytest.raises(LocalSecurityMasterError, match="staged_candidate_reparse_point"):
        manager._validate_staged_candidate(link, staging)
