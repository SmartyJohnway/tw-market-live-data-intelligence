from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from pathlib import Path

import pytest

from server.services import unified_mode_b2
from server.services import unified_mode_b2_execution


ROOT = Path(__file__).resolve().parents[2]
WRAPPER = ROOT / "scripts" / "m8r_06_03_execute_once.py"


def _rebuilt():
    plan = json.loads((ROOT / "tests/fixtures/m8r_05b_01/golden/single_executable_plan.json").read_text(encoding="utf-8"))
    return {"preview": {"status": "ready_for_confirmation", "internal_execution_reference": {"preview_id": "umepreview-v1-child"}}, "orchestration_plan": plan}


def _package(tmp_path, monkeypatch):
    monkeypatch.setattr(unified_mode_b2, "CONTROL_ROOT", tmp_path)
    monkeypatch.setattr(unified_mode_b2, "build_mode_b1_preview", lambda _request: _rebuilt())
    plan = _rebuilt()["orchestration_plan"]
    return unified_mode_b2.build_mode_b2_authorization({
        "request": {"schema_version": "unified_market_evidence_request.v1", "request_id": "child-test"},
        "expected_preview_id": "umepreview-v1-child", "expected_plan_id": plan["plan_id"], "expected_plan_hash": plan["plan_hash"],
        "confirm_authorization": True, "approval_scope_mode": "whole_plan_executable_scope",
    })


def test_fixed_child_executes_once_and_replay_is_rejected(tmp_path, monkeypatch):
    package = _package(tmp_path, monkeypatch)
    environment = os.environ | {"PYTHONPATH": str(ROOT), "M8R_06_03_CONTROL_ROOT": str(tmp_path), "M8R_06_03_TEST_SOURCE_TRANSPORT": "deterministic"}
    command = [sys.executable, str(WRAPPER), "--authorization-id", package["authorization_id"], "--confirm-execution", "--confirm-network-execution", "--operator-confirmation-reference", "unit-child"]
    first = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, env=environment, timeout=30)
    assert first.returncode == 0
    result = json.loads(first.stdout)
    assert result["consumption_state"] in {"consumed_success", "consumed_partial", "consumed_failed"}
    assert result["external_market_network_executed"] is False
    second = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, env=environment, timeout=30)
    assert second.returncode == 2
    assert json.loads(second.stdout) == {"error": "mode_b2_execution_unavailable"}
    assert "Traceback" not in second.stderr


def test_fixed_child_rejects_unknown_arguments_without_command_execution():
    result = subprocess.run([sys.executable, str(WRAPPER), "--command", "whoami"], cwd=ROOT, text=True, capture_output=True, timeout=15)
    assert result.returncode == 2
    assert "whoami" not in result.stdout


@pytest.mark.parametrize("protocol", ["non_json", "incomplete_json", "unexpected_shape", "unexpected_nonzero"])
def test_parent_rejects_actual_malformed_child_protocol_without_leakage(monkeypatch, protocol):
    monkeypatch.setenv("M8R_06_03_TEST_CHILD_PROTOCOL", protocol)
    with pytest.raises(unified_mode_b2.ModeB2Error, match="mode_b2_execution_child_protocol_invalid") as exc:
        unified_mode_b2_execution.execute_mode_b2_once({
            "control_package_id": "umea-v1-does-not-matter", "confirm_execution": True,
            "operator_confirmation_reference": "protocol-test", "confirm_network_execution": False,
        })
    assert "Traceback" not in str(exc.value)
    assert str(ROOT) not in str(exc.value)


def _parent_payload(package):
    return {
        "control_package_id": package["authorization_id"], "confirm_execution": True,
        "operator_confirmation_reference": "parent-test", "confirm_network_execution": True,
    }


def test_timeout_after_claim_consumes_authorization_and_prevents_retry(tmp_path, monkeypatch):
    package = _package(tmp_path, monkeypatch)
    monkeypatch.setenv("M8R_06_03_CONTROL_ROOT", str(tmp_path))
    monkeypatch.setenv("M8R_06_03_TEST_SOURCE_TRANSPORT", "deterministic")
    monkeypatch.setenv("M8R_06_03_TEST_SOURCE_DELAY_SECONDS", "3")
    monkeypatch.setattr(unified_mode_b2_execution, "MAX_CHILD_TIMEOUT_SECONDS", 1)
    monkeypatch.setattr(unified_mode_b2_execution, "FIXED_OVERHEAD_SECONDS", 0)
    with pytest.raises(unified_mode_b2.ModeB2Error, match="mode_b2_execution_timeout"):
        unified_mode_b2_execution.execute_mode_b2_once(_parent_payload(package))
    claim = tmp_path / package["authorization_id"] / "claims" / f"{package['authorization_id']}.consumption-record.json"
    assert claim.is_file()
    monkeypatch.delenv("M8R_06_03_TEST_SOURCE_DELAY_SECONDS")
    with pytest.raises(unified_mode_b2.ModeB2Error, match="mode_b2_execution_unavailable"):
        unified_mode_b2_execution.execute_mode_b2_once(_parent_payload(package))


def test_concurrent_parent_attempts_have_one_atomic_claim_and_one_dispatch(tmp_path, monkeypatch):
    package = _package(tmp_path, monkeypatch)
    counter = tmp_path / "invocations"
    monkeypatch.setenv("M8R_06_03_CONTROL_ROOT", str(tmp_path))
    monkeypatch.setenv("M8R_06_03_TEST_SOURCE_TRANSPORT", "deterministic")
    monkeypatch.setenv("M8R_06_03_TEST_INVOCATION_COUNTER", str(counter))
    results = []
    barrier = threading.Barrier(2)

    def attempt():
        barrier.wait()
        try:
            results.append(("success", unified_mode_b2_execution.execute_mode_b2_once(_parent_payload(package))))
        except unified_mode_b2.ModeB2Error as exc:
            results.append(("error", exc.code))

    threads = [threading.Thread(target=attempt) for _ in range(2)]
    for thread in threads: thread.start()
    for thread in threads: thread.join(timeout=30)
    assert all(not thread.is_alive() for thread in threads)
    assert [kind for kind, _ in results].count("success") == 1
    assert [kind for kind, _ in results].count("error") == 1
    assert results[[kind for kind, _ in results].index("error")][1] == "mode_b2_execution_unavailable"
    assert len(list(counter.glob("*.invoked"))) == 1
