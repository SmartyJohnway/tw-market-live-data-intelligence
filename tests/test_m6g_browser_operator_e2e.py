from __future__ import annotations

import json
from pathlib import Path

import pytest

import scripts.run_m6g_browser_operator_e2e as m6g


def test_report_schema_and_final_status_skip(tmp_path, monkeypatch):
    monkeypatch.setattr(m6g, "REPORT_DIR", tmp_path)
    monkeypatch.setattr(m6g, "JSON_REPORT", tmp_path / "latest_browser_operator_e2e_report.json")
    monkeypatch.setattr(m6g, "MD_REPORT", tmp_path / "latest_browser_operator_e2e_report.md")
    monkeypatch.setattr(m6g, "playwright_state", lambda: (False, "missing playwright test"))
    args = type("Args", (), {"check_only": True, "execute_bounded_live_check": False, "ssl_policy": "strict"})()

    report = m6g.build_report(args)
    m6g.write_report(report)
    data = json.loads((tmp_path / "latest_browser_operator_e2e_report.json").read_text())

    for key in [
        "schema_version",
        "generated_at_utc",
        "mode",
        "browser_engine",
        "playwright_available",
        "fastapi_started",
        "frontend_loaded",
        "watchlist_payload_checked",
        "watchlist_items_checked",
        "id_generation_status",
        "validate_request_status",
        "plan_request_status",
        "execute_request_status",
        "unexpected_execute_requests",
        "polling_detected",
        "network_calls_may_have_occurred",
        "ssl_policy",
        "live_execution",
        "targets",
        "artifacts_written",
        "mode_a_reference",
        "mode_b_observation",
        "mode_c_conversation",
        "governance",
        "final_status",
        "caveats",
        "recommended_next_steps",
    ]:
        assert key in data
    assert data["final_status"] == "skipped_with_caveats"
    assert data["network_calls_may_have_occurred"] is False
    assert data["execute_request_status"] == "not_executed"


def test_final_status_logic_pass_and_fail():
    report = {
        "playwright_available": True,
        "id_generation_status": "pass",
        "validate_request_status": "pass",
        "plan_request_status": "pass",
        "unexpected_execute_requests": 0,
        "polling_detected": False,
        "caveats": [],
        "mode_b_observation": {"ssl_policy_api_checks": {"env_override": True, "query_override": True, "invalid_policy_fail_closed": True}},
    }
    assert m6g.final_status(report) == "pass"
    report["unexpected_execute_requests"] = 1
    assert m6g.final_status(report) == "fail"


def test_no_execution_in_check_only_when_playwright_missing(monkeypatch):
    monkeypatch.setattr(m6g, "playwright_state", lambda: (False, "missing"))
    called = False

    def no_start(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("FastAPI should not start when browser dependency is missing")

    monkeypatch.setattr(m6g, "start_fastapi", no_start)
    args = type("Args", (), {"check_only": True, "execute_bounded_live_check": False, "ssl_policy": "strict"})()
    report = m6g.build_report(args)
    assert called is False
    assert report["live_execution"]["executed"] is False
    assert report["network_calls_may_have_occurred"] is False


def test_report_artifact_paths_are_allowed():
    report = {
        "playwright_available": False,
        "artifacts_written": [m6g.display_path(m6g.JSON_REPORT), m6g.display_path(m6g.MD_REPORT)],
    }
    assert all(path.startswith("research/live_observation_runs/m6g_browser_operator_e2e/") for path in report["artifacts_written"])
    forbidden = ("frontend/public", "research/generated", "production/prod")
    assert not any(path.startswith(forbidden) for path in report["artifacts_written"])


def test_ssl_policy_api_checks_fail_closed_and_override():
    checks = m6g.ssl_policy_api_checks()
    assert checks["env_override"] is True
    assert checks["query_override"] is True
    assert checks["invalid_policy_fail_closed"] is True
    assert [c["ssl_policy"] for c in checks["execution_calls"]] == ["compatibility", "strict"]


def test_item_contract_and_id_generation():
    assert m6g.item_ok({"id": "twse:2330", "category": "twse", "symbol": "2330", "adapter": "TWSE_MIS", "preferred_sources": ["TWSE_MIS"], "enabled": True})
    assert not m6g.item_ok({"category": "twse", "symbol": "2330", "adapter": "TWSE_MIS", "preferred_sources": ["TWSE_MIS"], "enabled": True})
    assert not m6g.item_ok({"id": "bad:2330", "category": "twse", "symbol": "2330", "adapter": "TWSE_MIS", "preferred_sources": ["TWSE_MIS"], "enabled": True})


@pytest.mark.browser
@pytest.mark.e2e
def test_browser_dependency_optional_marker_only():
    available, _ = m6g.playwright_state()
    if not available:
        pytest.skip("Playwright not installed; covered by script skipped_with_caveats behavior.")
