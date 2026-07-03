from __future__ import annotations

import sys

import pytest

from scripts import run_operator_preflight as preflight


def test_default_timeout_is_300(monkeypatch):
    monkeypatch.delenv(preflight.TIMEOUT_ENV_VAR, raising=False)
    assert preflight.resolve_timeout_seconds(None) == 300


def test_env_timeout_override_works():
    assert preflight.resolve_timeout_seconds(None, {preflight.TIMEOUT_ENV_VAR: "123"}) == 123


def test_cli_timeout_override_takes_precedence():
    assert preflight.resolve_timeout_seconds(456, {preflight.TIMEOUT_ENV_VAR: "123"}) == 456


@pytest.mark.parametrize("value", ["0", "-1", "abc", "1.5"])
def test_invalid_env_timeout_fails_clearly(value):
    with pytest.raises(ValueError, match=preflight.TIMEOUT_ENV_VAR):
        preflight.resolve_timeout_seconds(None, {preflight.TIMEOUT_ENV_VAR: value})


def test_timed_out_child_command_returns_fail_shape():
    result = preflight.run_command(
        "slow command",
        [sys.executable, "-c", "import time; time.sleep(2)"],
        timeout_seconds=1,
    )
    assert result["status"] == "FAIL"
    assert result["returncode"] is None
    assert result["timeout_seconds"] == 1
    assert result["timed_out"] is True
    assert "timed out after 1 seconds" in result["stderr_tail"]
    assert "--timeout-seconds" in result["diagnostic"]
