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
    """A fresh Local Service starts but refuses identity work without a release."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    control_root, counter = tmp_path / "control", tmp_path / "counter"
    environment = os.environ | {
        "M8R_06_03_CONTROL_ROOT": str(control_root),
        "M8R_06_03_EXECUTION_ENVIRONMENT": "test",
        "M8R_06_03_TEST_SOURCE_TRANSPORT": "deterministic",
        "M8R_06_03_TEST_INVOCATION_COUNTER": str(counter),
        "TW_MARKET_SECURITY_MASTER_ROOT": str(tmp_path / "security_master"),
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

        assert _status(base + "/workbench/") == 200
        market_request = {
            "schema_version": "unified_market_evidence_request.v1", "request_id": "localhost-execute-once",
            "execution_mode": "preview", "targets": [{"input": "2330", "market_hint": "TWSE"}],
            "data_needs": [{"type": "current_observation", "priority": "required"}],
        }
        status, body = _json(base + "/api/unified/validate-request", {"request": market_request})
        assert status == 503
        assert body["error"] == "SECURITY_MASTER_NOT_INITIALIZED"
        assert not control_root.exists()
        assert not counter.exists()
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=10)
