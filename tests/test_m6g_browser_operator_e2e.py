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
        "requested_ssl_policy",
        "effective_server_env_ssl_policy",
        "browser_execute_ssl_policy_source",
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
    assert data["requested_ssl_policy"] == "strict"
    assert data["effective_server_env_ssl_policy"] is None
    assert data["browser_execute_ssl_policy_source"] == "default"


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


def test_server_env_policy_preserves_strict_default():
    assert m6g.server_env_policy_for_mode(execute_live=False, selected_ssl_policy="strict") == (None, "default")
    assert m6g.server_env_policy_for_mode(execute_live=True, selected_ssl_policy="strict") == (None, "default")
    assert m6g.server_env_policy_for_mode(execute_live=True, selected_ssl_policy="compatibility") == ("compatibility", "env")
    assert m6g.server_env_policy_for_mode(execute_live=True, selected_ssl_policy="unsafe-explicit") == ("unsafe-explicit", "env")


def test_check_only_starts_fastapi_without_ssl_env_override_for_strict(monkeypatch):
    calls = []
    monkeypatch.setattr(m6g, "playwright_state", lambda: (True, None))
    monkeypatch.setattr(m6g, "start_fastapi", lambda env_policy=None: (type("Proc", (), {"terminate": lambda self: None, "wait": lambda self, timeout=None: None})(), 12345, True))

    def capture_browser(port, execute_live, ssl_policy):
        calls.append({"port": port, "execute_live": execute_live, "ssl_policy": ssl_policy})
        return {"frontend_loaded": True, "watchlist_payload_checked": True, "watchlist_items_checked": 1, "id_generation_status": "pass", "validate_request_status": "pass", "plan_request_status": "pass", "execute_request_status": "not_executed", "unexpected_execute_requests": 0, "polling_detected": False, "targets": ["0050"]}

    start_calls = []
    def start(env_policy=None):
        start_calls.append(env_policy)
        return (type("Proc", (), {"terminate": lambda self: None, "wait": lambda self, timeout=None: None})(), 12345, True)

    monkeypatch.setattr(m6g, "start_fastapi", start)
    monkeypatch.setattr(m6g, "run_browser_check", capture_browser)
    args = type("Args", (), {"check_only": True, "execute_bounded_live_check": False, "ssl_policy": "strict"})()
    report = m6g.build_report(args)
    assert start_calls == [None]
    assert report["requested_ssl_policy"] == "strict"
    assert report["effective_server_env_ssl_policy"] is None
    assert report["browser_execute_ssl_policy_source"] == "default"
    assert calls[0]["execute_live"] is False


def test_live_strict_does_not_set_compatibility_env(monkeypatch):
    start_calls = []
    monkeypatch.setattr(m6g, "playwright_state", lambda: (True, None))
    monkeypatch.setattr(m6g, "start_fastapi", lambda env_policy=None: (start_calls.append(env_policy) or (type("Proc", (), {"terminate": lambda self: None, "wait": lambda self, timeout=None: None})(), 12345, True)))
    monkeypatch.setattr(m6g, "run_browser_check", lambda port, execute_live, ssl_policy: {"frontend_loaded": True, "watchlist_payload_checked": True, "watchlist_items_checked": 1, "id_generation_status": "pass", "validate_request_status": "pass", "plan_request_status": "pass", "execute_request_status": "executed", "unexpected_execute_requests": 0, "polling_detected": False, "targets": ["0050"]})
    args = type("Args", (), {"check_only": False, "execute_bounded_live_check": True, "ssl_policy": "strict"})()
    report = m6g.build_report(args)
    assert start_calls == [None]
    assert report["effective_server_env_ssl_policy"] is None
    assert report["browser_execute_ssl_policy_source"] == "default"


def test_live_compatibility_sets_explicit_env(monkeypatch):
    start_calls = []
    monkeypatch.setattr(m6g, "playwright_state", lambda: (True, None))
    monkeypatch.setattr(m6g, "start_fastapi", lambda env_policy=None: (start_calls.append(env_policy) or (type("Proc", (), {"terminate": lambda self: None, "wait": lambda self, timeout=None: None})(), 12345, True)))
    monkeypatch.setattr(m6g, "run_browser_check", lambda port, execute_live, ssl_policy: {"frontend_loaded": True, "watchlist_payload_checked": True, "watchlist_items_checked": 1, "id_generation_status": "pass", "validate_request_status": "pass", "plan_request_status": "pass", "execute_request_status": "executed", "unexpected_execute_requests": 0, "polling_detected": False, "targets": ["0050"]})
    args = type("Args", (), {"check_only": False, "execute_bounded_live_check": True, "ssl_policy": "compatibility"})()
    report = m6g.build_report(args)
    assert start_calls == ["compatibility"]
    assert report["requested_ssl_policy"] == "compatibility"
    assert report["effective_server_env_ssl_policy"] == "compatibility"
    assert report["browser_execute_ssl_policy_source"] == "env"


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
