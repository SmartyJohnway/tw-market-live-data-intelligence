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
    assert m6e.final_status([{"status": "pass_with_caveats"}], []) == "pass_with_caveats"
    assert m6e.final_status([{"status": "fail"}], []) == "fail"


def test_run_json_propagates_operator_preflight_caveats(monkeypatch):
    class Completed:
        returncode = 0
        stdout = json.dumps({"status": "PASS WITH CAVEATS", "caveats": ["Virtual environment not detected."]})
        stderr = ""

    monkeypatch.setattr(m6e.subprocess, "run", lambda *args, **kwargs: Completed())
    result = m6e.run_json("operator preflight", ["python", "scripts/run_operator_preflight.py", "--json", "--timeout-seconds", "300"])
    assert result["status"] == "pass_with_caveats"
    assert result["caveats"] == ["Virtual environment not detected."]
    assert m6e.final_status([result], result["caveats"]) == "pass_with_caveats"


def test_run_json_extracts_nested_operator_preflight_caveats(monkeypatch):
    class Completed:
        returncode = 0
        stdout = json.dumps({
            "status": "PASS WITH CAVEATS",
            "caveats": [],
            "results": [{"label": "Environment", "status": "PASS", "checks": [{"name": "Virtual environment", "status": "CAVEAT", "detail": "not detected"}]}],
        })
        stderr = ""

    monkeypatch.setattr(m6e.subprocess, "run", lambda *args, **kwargs: Completed())
    result = m6e.run_json("operator preflight", ["python", "scripts/run_operator_preflight.py", "--json", "--timeout-seconds", "300"])
    assert result["status"] == "pass_with_caveats"
    assert result["caveats"] == ["operator preflight: Virtual environment caveat (not detected)."]


def test_markdown_caveats_section_not_none_when_child_caveats(tmp_path, monkeypatch):
    monkeypatch.setattr(m6e, "REPORT_DIR", tmp_path)
    monkeypatch.setattr(m6e, "JSON_REPORT", tmp_path / "latest_operator_acceptance_report.json")
    monkeypatch.setattr(m6e, "MD_REPORT", tmp_path / "latest_operator_acceptance_report.md")
    report = {
        "generated_at_utc": "2026-07-03T00:00:00Z",
        "final_status": "pass_with_caveats",
        "operator_acceptance_summary": {"operator_ready": True},
        "caveats": ["Virtual environment not detected."],
        "recommended_next_steps": ["python scripts/run_operator_preflight.py --json --timeout-seconds 300"],
    }
    m6e.write_report(report)
    markdown = m6e.MD_REPORT.read_text(encoding="utf-8")
    assert "## Caveats" in markdown
    assert "- Virtual environment not detected." in markdown
    assert "- None" not in markdown


def test_report_schema_and_mode_fields_from_check_only(monkeypatch):
    def deny_network(*args, **kwargs):
        raise AssertionError("M6E check-only test attempted network socket creation")
    monkeypatch.setattr(socket, "create_connection", deny_network)
    report = m6e.build_report("check-only", "strict", False)
    for key in ["schema_version", "generated_at_utc", "mode", "network_calls_may_have_occurred", "ssl_policy", "repository", "python", "platform", "checks", "mode_a", "mode_b", "mode_c", "fastapi", "mcp", "frontend", "conversation_package", "operator_workbench", "operator_preflight", "child_workflow_caveats", "governance", "final_status", "caveats", "recommended_next_steps"]:
        assert key in report
    assert report["network_calls_may_have_occurred"] is False
    assert report["final_status"] == "pass_with_caveats"
    assert report["operator_preflight"]["status"] == "pass_with_caveats"
    assert report["child_workflow_caveats"]["operator_preflight"]
    assert report["caveats"]
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
