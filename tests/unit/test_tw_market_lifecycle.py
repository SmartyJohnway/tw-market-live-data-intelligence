from __future__ import annotations

import json
import copy
import socket
from pathlib import Path
import subprocess
from types import SimpleNamespace
from unittest.mock import patch

from scripts import tw_market_lifecycle as lifecycle


def test_missing_owner_is_not_running_and_stop_is_idempotent(tmp_path):
    owner = tmp_path / "owner.json"
    with patch.object(lifecycle, "_owner_path", return_value=owner):
        result = lifecycle._stop("127.0.0.1", 19371)
    assert result == {"status": "NOT_RUNNING", "reason_code": "NOT_RUNNING"}


def test_status_and_doctor_never_echo_credentials_from_configured_service_url(tmp_path, monkeypatch):
    secret_url = "http://user:TEST-PASSWORD-CANARY-44@127.0.0.1:8000/?token=TEST-TOKEN-CANARY-55"
    monkeypatch.setenv("UNIFIED_MARKET_EVIDENCE_SERVICE_URL", secret_url)
    monkeypatch.setattr(lifecycle, "_owner_path", lambda _port: tmp_path / "owner.json")
    monkeypatch.setattr(lifecycle, "_read_owner", lambda _path: (None, None))
    monkeypatch.setattr(lifecycle, "_owner_state", lambda *_args: "NOT_RUNNING")
    monkeypatch.setattr(lifecycle, "_port_open", lambda *_args: False)
    monkeypatch.setattr(lifecycle, "_sm_status", lambda: {"status": "NOT_INITIALIZED", "root": str(tmp_path)})
    monkeypatch.setattr(lifecycle, "disk_free_bytes", lambda _path: 100)
    monkeypatch.setattr(lifecycle, "_event_path", lambda _port: tmp_path / "events.jsonl")
    subprocess_args = []

    def fake_run(args, **_kwargs):
        subprocess_args.append(list(args))
        return SimpleNamespace(returncode=0, stdout="{}")

    monkeypatch.setattr(lifecycle.subprocess, "run", fake_run)
    status = lifecycle._base("127.0.0.1", 8000, {}, None)
    doctor = lifecycle._doctor("127.0.0.1", 8000, {}, None)
    encoded = json.dumps({"status": status, "doctor": doctor})
    assert status["mcp"]["service_url"] == "UNAVAILABLE"
    assert doctor["mcp"]["service_url"] == "UNAVAILABLE"
    assert "TEST-PASSWORD-CANARY" not in encoded
    assert "TEST-TOKEN-CANARY" not in encoded
    assert all("TEST-" not in " ".join(args) for args in subprocess_args)


def test_occupied_unowned_port_is_never_claimed_or_stopped(tmp_path):
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0)); listener.listen()
    port = listener.getsockname()[1]
    owner = tmp_path / "owner.json"
    try:
        with patch.object(lifecycle, "_owner_path", return_value=owner), patch.object(lifecycle, "_terminate_owned") as terminate:
            start = lifecycle._start("127.0.0.1", port)
            stop = lifecycle._stop("127.0.0.1", port)
        assert start["status"] == "PORT_OCCUPIED_NOT_OWNED"
        assert stop["status"] == "PORT_OCCUPIED_NOT_OWNED"
        assert listener.fileno() >= 0
        assert not owner.exists()
        terminate.assert_not_called()
    finally:
        listener.close()


def test_stale_and_malformed_ownership_is_not_used_to_kill(tmp_path):
    owner_path = tmp_path / "owner.json"
    owner_path.write_text(json.dumps({"schema": 1, "root": str(lifecycle.ROOT.resolve()), "pid": 987654321,
                                      "process_start_token": "old", "executable": str(Path(lifecycle.sys.executable).resolve())}), encoding="utf-8")
    with patch.object(lifecycle, "_owner_path", return_value=owner_path), patch.object(lifecycle, "_port_open", return_value=False):
        result = lifecycle._stop("127.0.0.1", 19372)
    assert result["status"] == "STALE_PROCESS_OWNERSHIP"
    assert result["metadata_cleaned"] is True
    assert not owner_path.exists()


def test_identity_mismatch_never_signals_occupied_process(tmp_path):
    owner_path = tmp_path / "owner.json"
    owner_path.write_text(json.dumps({"schema": 1, "root": str(lifecycle.ROOT.resolve()), "pid": 4242,
                                      "process_start_token": "old-creation-time", "executable": str(Path(lifecycle.sys.executable).resolve())}), encoding="utf-8")
    with patch.object(lifecycle, "_owner_path", return_value=owner_path), patch.object(lifecycle, "_process_matches", return_value=False), patch.object(lifecycle, "_port_open", return_value=True), patch.object(lifecycle.os, "kill") as kill:
        result = lifecycle._stop("127.0.0.1", 19372)
    assert result["status"] == "STALE_PROCESS_OWNERSHIP"
    assert result["port_status"] == "PORT_OCCUPIED_NOT_OWNED"
    kill.assert_not_called()


def test_cli_endpoint_overrides_environment_and_uses_same_mcp_endpoint():
    with patch.dict(lifecycle.os.environ, {"TW_MARKET_HOST": "localhost", "TW_MARKET_PORT": "9999", "UNIFIED_MARKET_EVIDENCE_SERVICE_URL": "http://127.0.0.1:9123"}):
        host, port, _ = lifecycle._effective("127.0.0.1", 18765)
        service_url = f"http://{host}:{port}"
    assert (host, port, service_url) == ("127.0.0.1", 18765, "http://127.0.0.1:18765")


def test_doctor_and_status_do_not_create_runtime_roots(tmp_path):
    roots = [tmp_path / name for name in ("sm", "watch", "control")]
    env = {"TW_MARKET_SECURITY_MASTER_ROOT": str(roots[0]), "TW_MARKET_WATCHLIST_ROOT": str(roots[1]), "M8R_06_03_CONTROL_ROOT": str(roots[2])}
    with patch.dict(lifecycle.os.environ, env), patch.object(lifecycle, "_port_open", return_value=False), patch.object(lifecycle, "_owner_path", return_value=tmp_path / "owner.json"):
        status = lifecycle._base("127.0.0.1", 19373, {"host": "test", "port": "test"})
        doctor = lifecycle._doctor("127.0.0.1", 19373, {"host": "test", "port": "test"})
    assert status["identity"]["status"] == "NOT_INITIALIZED"
    assert doctor["status"] == "WARN"
    assert all(not root.exists() for root in roots)


def test_current_product_lifecycle_sources_do_not_import_a6():
    sources = [Path("scripts/m8r_06_03_production_adapter.py"), Path("server/services/phase_h_h2_twse_exright_executor.py"),
               Path("server/services/phase_h_h3_twse_stock_day_adapter.py"), Path("scripts/tw_market_lifecycle.py")]
    for source in sources:
        text = source.read_text(encoding="utf-8")
        assert "scripts.a6_session_transport" not in text


def _starting_record():
    return {"schema": 1, "state": "starting", "instance_id": "instance-1", "root": str(lifecycle.ROOT.resolve()),
            "host": "127.0.0.1", "port": 19374, "creator_pid": 4321, "creator_start_token": "creator-token",
            "creator_executable": str(Path(lifecycle.sys.executable).resolve()), "created_at": "2026-10-13T00:00:00+00:00"}


def test_live_creator_starting_reservation_is_preserved(tmp_path):
    owner_path = tmp_path / "owner.json"
    owner_path.write_text(json.dumps(_starting_record()), encoding="utf-8")
    with patch.object(lifecycle, "_owner_path", return_value=owner_path), patch.object(lifecycle, "_identity_matches", return_value=True):
        result = lifecycle._start("127.0.0.1", 19374)
    assert result["status"] == "START_IN_PROGRESS"
    assert json.loads(owner_path.read_text(encoding="utf-8"))["instance_id"] == "instance-1"


def test_mismatched_starting_creator_is_stale(tmp_path):
    record = _starting_record()
    with patch.object(lifecycle, "_identity_matches", return_value=False):
        assert lifecycle._owner_state(record, None) == "STALE_PROCESS_OWNERSHIP"


def test_status_does_not_mutate_stale_starting_reservation(tmp_path):
    owner_path = tmp_path / "owner.json"
    original = json.dumps(_starting_record(), sort_keys=True)
    owner_path.write_text(original, encoding="utf-8")
    preload = subprocess.CompletedProcess([], 0, json.dumps({"canonical_schema_loaded": True, "capability_catalog_loaded": True}), "")
    def run_check(args, **kwargs):
        if "run_unified_workbench.py" in args[1]: return preload
        if "run_unified_market_evidence_mcp.py" in args[1]: return subprocess.CompletedProcess(args, 3, "", "unreachable")
        return subprocess.CompletedProcess(args, 0, "{}", "")

    with patch.object(lifecycle, "_owner_path", return_value=owner_path), patch.object(lifecycle, "_identity_matches", return_value=False), \
         patch.object(lifecycle, "_port_open", return_value=False), patch.object(lifecycle, "_sm_status", return_value={"status": "NOT_INITIALIZED", "root": "unused"}), \
         patch.object(lifecycle.subprocess, "run", side_effect=run_check):
        result = lifecycle._base("127.0.0.1", 19374, {})
        doctor = lifecycle._doctor("127.0.0.1", 19374, {})
    assert result["service"]["process"] == "STALE_PROCESS_OWNERSHIP"
    assert doctor["service"]["process"] == "STALE_PROCESS_OWNERSHIP"
    assert owner_path.read_text(encoding="utf-8") == original


def test_start_recovers_stale_starting_reservation(tmp_path):
    owner_path = tmp_path / "owner.json"
    owner_path.write_text(json.dumps(_starting_record()), encoding="utf-8")

    class Child:
        pid = 54321
        def poll(self): return None

    with patch.object(lifecycle, "_owner_path", return_value=owner_path), patch.object(lifecycle, "_identity_matches", return_value=False), \
         patch.object(lifecycle, "_port_open", return_value=False), patch.object(lifecycle, "_process_start_token", return_value="child-token"), \
         patch.object(lifecycle, "_process_executable", return_value=str(Path(lifecycle.sys.executable).resolve())), \
         patch.object(lifecycle.subprocess, "Popen", return_value=Child()), patch.object(lifecycle, "_health", return_value=(True, {"status": "healthy"})), \
         patch.object(lifecycle.time, "monotonic", return_value=0), patch.object(lifecycle.time, "sleep"):
        result = lifecycle._start("127.0.0.1", 19374)
    assert result["status"] == "STARTED"
    assert json.loads(owner_path.read_text(encoding="utf-8"))["pid"] == 54321


def test_stop_cleans_stale_starting_reservation_explicitly(tmp_path):
    owner_path = tmp_path / "owner.json"
    owner_path.write_text(json.dumps(_starting_record()), encoding="utf-8")
    with patch.object(lifecycle, "_owner_path", return_value=owner_path), patch.object(lifecycle, "_identity_matches", return_value=False):
        result = lifecycle._stop("127.0.0.1", 19374)
    assert result == {"status": "STALE_PROCESS_OWNERSHIP_CLEANED", "reason_code": "STALE_PROCESS_OWNERSHIP", "metadata_cleaned": True}
    assert not owner_path.exists()


def test_start_timeout_terminates_only_verified_child_and_cleans_record(tmp_path):
    owner_path = tmp_path / "owner.json"

    class Child:
        pid = 54322
        def poll(self): return None

    def terminate(record, path):
        assert record["pid"] == 54322
        assert record["process_start_token"] == "child-token"
        path.unlink()
        return {"status": "STOPPED"}

    with patch.object(lifecycle, "_owner_path", return_value=owner_path), patch.object(lifecycle, "_port_open", return_value=False), \
         patch.object(lifecycle, "_process_start_token", return_value="child-token"), patch.object(lifecycle, "_process_executable", return_value=str(Path(lifecycle.sys.executable).resolve())), \
         patch.object(lifecycle.subprocess, "Popen", return_value=Child()), patch.object(lifecycle, "_health", return_value=(False, None)), \
         patch.object(lifecycle, "_terminate_owned", side_effect=terminate) as stop_owned, patch.object(lifecycle.time, "monotonic", side_effect=[0, 0, 16]), \
         patch.object(lifecycle.time, "sleep"):
        result = lifecycle._start("127.0.0.1", 19374)
    assert result["status"] == "START_TIMEOUT"
    assert result["cleanup_status"] == "STOPPED"
    assert result["child_terminated"] is True
    stop_owned.assert_called_once()
    assert not owner_path.exists()


def test_doctor_severity_and_exit_code_aggregation():
    assert lifecycle._aggregate_doctor_status([{"status": "PASS"}]) == "PASS"
    assert lifecycle._exit_code("PASS") == 0
    assert lifecycle._exit_code("STOPPED") == 0
    assert lifecycle._exit_code("STOP_FAILED") == 1
    assert lifecycle._aggregate_doctor_status([{"status": "PASS"}, {"status": "WARN", "reason_code": "SECURITY_MASTER_NOT_INITIALIZED"}]) == "WARN"
    assert lifecycle._exit_code("WARN") == 0
    assert lifecycle._aggregate_doctor_status([{"status": "PASS"}, {"status": "FAIL"}]) == "FAIL"
    assert lifecycle._exit_code("FAIL") != 0


def test_not_initialized_remains_doctor_warning():
    assert lifecycle._aggregate_doctor_status([{"status": "PASS"}, {"status": "WARN", "reason_code": "SECURITY_MASTER_NOT_INITIALIZED"}]) == "WARN"


def test_doctor_uses_severity_aggregation_and_keeps_not_initialized_warning(tmp_path):
    base = {"status": "SERVICE_ALIVE", "service": {"process": "RUNNING", "alive": True},
            "identity": {"status": "ACTIVE", "root": str(tmp_path)},
            "paths": {**{key: str(tmp_path) for key in ("security_master_root", "watchlist_root", "control_root")},
                      "operational_event_path": str(tmp_path / "operational-events.jsonl")},
            "readiness": {"routes": {"projection": "READY"}},
            "mcp": {"status": "READY", "service_url": "http://127.0.0.1:8000", "local_service_reachable": True},
            "resources": {"managed_service_process_memory_bytes": 64 * 1024 * 1024,
                          "application_root_disk_free_bytes": 10 * 1024 * 1024,
                          "runtime_root_disk_free_bytes": 10 * 1024 * 1024},
            "checks": []}

    def run_ok(args, **kwargs):
        stdout = json.dumps({"canonical_schema_loaded": True, "capability_catalog_loaded": True}) if "run_unified_workbench.py" in args[1] else ""
        return subprocess.CompletedProcess(args, 0, stdout, "")

    with patch.object(lifecycle, "_base", side_effect=lambda *args, **kwargs: copy.deepcopy(base)), patch.object(lifecycle.subprocess, "run", side_effect=run_ok):
        assert lifecycle._doctor("127.0.0.1", 8000, {})["status"] == "PASS"

    fresh = {**base, "identity": {"status": "NOT_INITIALIZED", "root": str(tmp_path)}}
    with patch.object(lifecycle, "_base", side_effect=lambda *args, **kwargs: copy.deepcopy(fresh)), patch.object(lifecycle.subprocess, "run", side_effect=run_ok):
        report = lifecycle._doctor("127.0.0.1", 8000, {})
    assert report["status"] == "WARN"
    assert next(check for check in report["checks"] if check["name"] == "security_master")["reason_code"] == "SECURITY_MASTER_NOT_INITIALIZED"

    def mcp_failure(args, **kwargs):
        if "run_unified_market_evidence_mcp.py" in args[1]:
            return subprocess.CompletedProcess(args, 4, "", "mcp mismatch")
        return run_ok(args, **kwargs)

    with patch.object(lifecycle, "_base", side_effect=lambda *args, **kwargs: copy.deepcopy(base)), patch.object(lifecycle.subprocess, "run", side_effect=mcp_failure):
        assert lifecycle._doctor("127.0.0.1", 8000, {})["status"] == "FAIL"

    with patch.object(lifecycle, "_base", side_effect=lambda *args, **kwargs: copy.deepcopy(base)), \
         patch.object(lifecycle.subprocess, "run", side_effect=run_ok), \
         patch("server.unified_mcp.tool_contracts.build_tool_contract_snapshot", return_value=SimpleNamespace(tools=())):
        report = lifecycle._doctor("127.0.0.1", 8000, {})
    assert report["status"] == "FAIL"
    assert next(check for check in report["checks"] if check["name"] == "mcp_tool_contract")["reason_code"] == "MCP_TOOL_SURFACE_MISMATCH"


def test_base_reports_owned_service_memory_and_disk_snapshots():
    owner = {"pid": 4321}
    startup = subprocess.CompletedProcess([], 0, json.dumps({
        "canonical_schema_loaded": True, "capability_catalog_loaded": True,
    }), "")
    with patch.object(lifecycle, "_read_owner", return_value=(owner, None)), \
         patch.object(lifecycle, "_owner_state", return_value="RUNNING"), \
         patch.object(lifecycle, "_port_open", return_value=False), \
         patch.object(lifecycle, "_sm_status", return_value={"status": "NOT_INITIALIZED", "root": str(lifecycle.ROOT)}), \
         patch.object(lifecycle.subprocess, "run", return_value=startup), \
         patch.object(lifecycle, "process_memory_bytes", return_value=7654321) as memory, \
         patch.object(lifecycle, "disk_free_bytes", side_effect=[111, 222]):
        report = lifecycle._base("127.0.0.1", 8000, {})
    assert report["resources"] == {
        "managed_service_process_memory_bytes": 7654321,
        "application_root_disk_free_bytes": 111,
        "runtime_root_disk_free_bytes": 222,
    }
    memory.assert_called_once_with(4321)


def test_doctor_warns_on_partial_resource_snapshot(tmp_path):
    base = {"status": "SERVICE_ALIVE", "service": {"process": "RUNNING", "alive": True},
            "identity": {"status": "ACTIVE", "root": str(tmp_path)},
            "paths": {**{key: str(tmp_path) for key in ("security_master_root", "watchlist_root", "control_root")},
                      "operational_event_path": str(tmp_path / "operational-events.jsonl")},
            "readiness": {"routes": {"projection": "READY"}},
            "mcp": {"status": "READY", "service_url": "http://127.0.0.1:8000", "local_service_reachable": True},
            "resources": {"managed_service_process_memory_bytes": None,
                          "application_root_disk_free_bytes": 100,
                          "runtime_root_disk_free_bytes": 100}, "checks": []}
    def run_ok(args, **kwargs):
        stdout = json.dumps({"canonical_schema_loaded": True, "capability_catalog_loaded": True}) if "run_unified_workbench.py" in args[1] else ""
        return subprocess.CompletedProcess(args, 0, stdout, "")
    with patch.object(lifecycle, "_base", side_effect=lambda *args, **kwargs: copy.deepcopy(base)), \
         patch.object(lifecycle.subprocess, "run", side_effect=run_ok):
        report = lifecycle._doctor("127.0.0.1", 8000, {})
    resource_check = next(check for check in report["checks"] if check["name"] == "resource_snapshot")
    assert resource_check["status"] == "WARN"
    assert resource_check["reason_code"] == "RESOURCE_SNAPSHOT_PARTIAL"
