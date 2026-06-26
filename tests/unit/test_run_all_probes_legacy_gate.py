import os
import subprocess
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../scripts")))

from run_all_probes import (
    LEGACY_ACK_ENV_VAR,
    LEGACY_ACK_VALUE,
    legacy_gate_message,
    legacy_run_all_probes_acknowledged,
)


def test_legacy_gate_requires_explicit_environment_ack(monkeypatch):
    monkeypatch.delenv(LEGACY_ACK_ENV_VAR, raising=False)
    assert legacy_run_all_probes_acknowledged() is False

    monkeypatch.setenv(LEGACY_ACK_ENV_VAR, "true")
    assert legacy_run_all_probes_acknowledged() is False

    monkeypatch.setenv(LEGACY_ACK_ENV_VAR, LEGACY_ACK_VALUE)
    assert legacy_run_all_probes_acknowledged() is True


def test_legacy_gate_message_names_required_ack():
    message = legacy_gate_message()
    assert "legacy/manual network runner" in message
    assert f"{LEGACY_ACK_ENV_VAR}={LEGACY_ACK_VALUE}" in message
    assert "M3G controlled refresh path" in message


def test_run_all_probes_script_exits_before_probe_without_ack():
    env = os.environ.copy()
    env.pop(LEGACY_ACK_ENV_VAR, None)

    result = subprocess.run(
        [sys.executable, "scripts/run_all_probes.py"],
        cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
        check=False,
    )

    assert result.returncode == 2
    assert f"{LEGACY_ACK_ENV_VAR}={LEGACY_ACK_VALUE}" in result.stdout
    assert "Running probes..." not in result.stdout
