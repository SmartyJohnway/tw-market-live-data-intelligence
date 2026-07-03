from __future__ import annotations

import json
import socket
from pathlib import Path

from fastapi.testclient import TestClient

from scripts import run_m6e_operator_acceptance as m6e
from server.main import app
from server.mcp_server import run_m5k_live_observation_tool

ROOT = Path(__file__).resolve().parents[1]


def test_final_status_logic():
    assert m6e.final_status([{"status": "pass"}], []) == "pass"
    assert m6e.final_status([{"status": "pass"}], ["caveat"]) == "pass_with_caveats"
    assert m6e.final_status([{"status": "fail"}], []) == "fail"


def test_report_schema_and_mode_fields_from_check_only(monkeypatch):
    def deny_network(*args, **kwargs):
        raise AssertionError("M6E check-only test attempted network socket creation")
    monkeypatch.setattr(socket, "create_connection", deny_network)
    report = m6e.build_report("check-only", "strict", False)
    for key in ["schema_version", "generated_at_utc", "mode", "network_calls_may_have_occurred", "ssl_policy", "repository", "python", "platform", "checks", "mode_a", "mode_b", "mode_c", "fastapi", "mcp", "frontend", "conversation_package", "operator_workbench", "operator_preflight", "governance", "final_status", "caveats", "recommended_next_steps"]:
        assert key in report
    assert report["network_calls_may_have_occurred"] is False
    assert report["mode_a"]["m5f_exists"] is True
    assert report["mode_b"]["default_watchlist_exists"] is True
    assert report["mode_c"]["status"] in {"pass", "fail"}


def test_check_only_writes_only_m6e_report_folder(tmp_path):
    report = m6e.build_report("check-only", "strict", False)
    m6e.write_report(report)
    assert m6e.JSON_REPORT.exists()
    assert m6e.MD_REPORT.exists()
    allowed = ROOT / "research/live_observation_runs/m6e_operator_acceptance"
    assert m6e.JSON_REPORT.resolve().is_relative_to(allowed.resolve())
    assert m6e.MD_REPORT.resolve().is_relative_to(allowed.resolve())


def test_fastapi_invalid_ssl_policy_acceptance():
    client = TestClient(app)
    watchlist = json.loads((ROOT / "config/m5k_default_watchlist.json").read_text(encoding="utf-8"))
    assert client.post("/api/m5k/live-observation/execute?confirm_live_observation=true&ssl_policy=invalid", json=watchlist).status_code == 400
    assert client.post("/api/m5k/live-observation/execute", json=watchlist).status_code == 400


def test_mcp_invalid_ssl_policy_acceptance():
    watchlist = json.loads((ROOT / "config/m5k_default_watchlist.json").read_text(encoding="utf-8"))
    result = run_m5k_live_observation_tool({"confirm_live_observation": True, "watchlist": watchlist, "ssl_policy": "invalid"})
    assert result["status"] == "failed_closed"
    assert result["failure_reason"] == "invalid_ssl_policy"
    assert result["network_calls"] is False


def test_frontend_static_acceptance_and_forbidden_behavior_scan():
    frontend = m6e.frontend_acceptance()
    assert frontend["status"] == "pass"
    conv = m6e.conversation_acceptance()
    assert any(c["name"] == "no forbidden raw/trading fields" and c["status"] == "pass" for c in conv["checks"])
