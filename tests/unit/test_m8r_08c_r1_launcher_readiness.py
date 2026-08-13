"""Deterministic process-readiness ordering for the official Workbench launcher."""
from __future__ import annotations

import importlib
import sys

import pytest


launcher = importlib.import_module("scripts.run_unified_workbench")


def _main(monkeypatch, *arguments):
    monkeypatch.setattr(sys, "argv", ["run_unified_workbench.py", *arguments])
    with pytest.raises(SystemExit) as exit_info:
        launcher.main()
    return exit_info.value.code


def test_normal_launch_preloads_before_uvicorn_and_uses_no_background_work(monkeypatch):
    events = []
    monkeypatch.setattr(launcher, "preload_governed_runtime", lambda: events.append("preload") or {"status": "ok"})
    monkeypatch.setattr(launcher.uvicorn, "run", lambda *_args, **_kwargs: events.append("uvicorn"))
    monkeypatch.setattr(sys, "argv", ["run_unified_workbench.py"])
    launcher.main()
    assert events == ["preload", "uvicorn"]


def test_preload_failure_prevents_uvicorn_bind(monkeypatch, capsys):
    monkeypatch.setattr(launcher, "preload_governed_runtime", lambda: (_ for _ in ()).throw(ValueError("no path leak")))
    monkeypatch.setattr(launcher.uvicorn, "run", lambda *_args, **_kwargs: pytest.fail("uvicorn must not bind"))
    assert _main(monkeypatch) == 1
    output = capsys.readouterr().out
    assert "ValueError" in output
    assert "no path leak" not in output


def test_invalid_host_is_rejected_before_expensive_preload(monkeypatch):
    monkeypatch.setattr(launcher, "preload_governed_runtime", lambda: pytest.fail("invalid host must not preload"))
    assert _main(monkeypatch, "--host", "0.0.0.0") == 1


def test_startup_check_reuses_preload_helper(monkeypatch, capsys):
    expected = {"status": "ok", "security_master_loaded": True}
    monkeypatch.setattr(launcher, "preload_governed_runtime", lambda: expected)
    assert launcher.run_startup_check() == 0
    assert '"security_master_loaded": true' in capsys.readouterr().out


def test_startup_check_preload_error_is_bounded_and_no_fixture_fallback(monkeypatch, capsys):
    monkeypatch.setattr(launcher, "preload_governed_runtime", lambda: (_ for _ in ()).throw(FileNotFoundError("C:/secret")))
    assert launcher.run_startup_check() == 1
    output = capsys.readouterr().out
    assert "governed_runtime_preload_failed:FileNotFoundError" in output
    assert "C:/secret" not in output
