"""Real localhost closure for the fixed M8R-06-03 execute-once vertical."""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _json(url: str, payload: dict | None = None) -> tuple[int, dict]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(url, data=data, headers={"Content-Type": "application/json"} if data else {}, method="POST" if data else "GET")
    try:
        with urlopen(request, timeout=90) as response:
            return response.status, json.loads(response.read())
    except URLError as exc:
        # HTTP errors carry their safe JSON response body too.
        if not hasattr(exc, "read"):
            raise
        return exc.code, json.loads(exc.read())


def _status(url: str) -> int:
    with urlopen(url, timeout=30) as response:
        return response.status


def test_real_localhost_authorize_execute_once_vertical(tmp_path):
    pointer = json.loads(
        (ROOT / "config" / "m8r_06_mode_a_security_master_pointer.json").read_text(
            encoding="utf-8"
        )
    )
    sealed = ROOT / pointer["index_path"]
    if not sealed.is_file():
        pytest.skip("current pointer-selected governed candidate is Git-ignored and unavailable")
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    control_root, counter = tmp_path / "control", tmp_path / "counter"
    environment = os.environ | {
        "M8R_06_03_CONTROL_ROOT": str(control_root),
        "M8R_06_03_EXECUTION_ENVIRONMENT": "test",
        "M8R_06_03_TEST_SOURCE_TRANSPORT": "deterministic",
        "M8R_06_03_TEST_INVOCATION_COUNTER": str(counter),
    }
    server = subprocess.Popen(
        [sys.executable, "scripts/run_unified_workbench.py", "--host", "127.0.0.1", "--port", str(port)],
        cwd=ROOT, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    base = f"http://127.0.0.1:{port}"
    try:
        deadline = time.monotonic() + 30
        while True:
            try:
                status, _ = _json(base + "/api/health")
                if status == 200:
                    break
            except URLError:
                pass
            if time.monotonic() >= deadline:
                raise AssertionError("supported localhost launcher did not become healthy")
            time.sleep(0.1)

        assert _status(base + "/workbench/mode-a/") == 200
        market_request = {
            "schema_version": "unified_market_evidence_request.v1", "request_id": "localhost-execute-once",
            "execution_mode": "preview", "targets": [{"input": "2330", "market_hint": "TWSE"}],
            "data_needs": [{"type": "current_observation", "priority": "required"}],
        }
        assert _json(base + "/api/unified/validate-request", {"request": market_request})[0] == 200
        status, preview = _json(base + "/api/unified/preview-request", {"request": market_request})
        assert status == 200 and preview["preview"]["status"] == "ready_for_confirmation"
        reference, plan = preview["preview"]["internal_execution_reference"], preview["orchestration_plan"]
        status, authorization = _json(base + "/api/unified/authorizations", {
            "request": market_request, "expected_preview_id": reference["preview_id"],
            "expected_plan_id": plan["plan_id"], "expected_plan_hash": plan["plan_hash"],
            "confirm_authorization": True, "approval_scope_mode": "whole_plan_executable_scope",
        })
        assert status == 200 and authorization["execution_ready"] is True
        execution_payload = {
            "control_package_id": authorization["control_package_id"], "confirm_execution": True,
            "operator_confirmation_reference": "localhost-vertical", "confirm_network_execution": True,
        }
        status, execution = _json(base + "/api/unified/executions", execution_payload)
        assert status == 200 and execution["external_market_network_executed"] is False
        assert execution["transport_mode"] == "deterministic_test_transport"
        assert execution["test_transport_active"] is True
        assert execution["execution_receipt_id"] and execution["evidence_bundle_id"]
        # Mode C is a separate post-execution local projection: no dispatch.
        status, result_package = _json(base + "/api/unified/result-package", {
            "control_package_id": authorization["control_package_id"]
        })
        assert status == 200 and result_package["external_market_network_executed"] is False
        assert result_package["result_id"] and result_package["audit_package_id"]
        assert _status(base + f"/api/unified/result-package/{authorization['control_package_id']}/audit.json") == 200
        status, replay = _json(base + "/api/unified/executions", execution_payload)
        assert status == 409 and replay["error"] == "mode_b2_execution_unavailable"
        assert "traceback" not in json.dumps(replay).lower()
        package = control_root / authorization["authorization_id"]
        assert list((package / "receipts").glob("*.json"))
        assert list((package / "bundles").glob("*.json"))
        evidence = json.loads(next((package / "evidence").glob("*.json")).read_text(encoding="utf-8"))
        assert evidence["transport_mode"] == "deterministic_test_transport"
        assert len(list(counter.glob("*.invoked"))) == 1
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=10)
