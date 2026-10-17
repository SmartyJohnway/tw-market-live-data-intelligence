import platform
import sys

from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from scripts.ssl_policy import platform_ssl_diagnostics
from server.main import app
from server import main as server_main
from server import mcp_server


def test_operator_diagnostics_windows_python313_hint(monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: "Windows")
    monkeypatch.setattr(sys, "version_info", (3, 13, 1, "final", 0))
    diag = platform_ssl_diagnostics(environ={})
    assert diag["windows_detected"] is True
    assert diag["python_313_detected"] is True
    assert "--ssl-policy compatibility" in diag["operator_hint"]
    assert diag["network_calls"] is False


def test_fastapi_cors_local_only_and_noncredentialed():
    cors = next(m for m in app.user_middleware if m.cls is CORSMiddleware)
    opts = cors.kwargs
    assert opts["allow_origins"] == ["null"]
    assert "localhost" in opts["allow_origin_regex"]
    assert "127\\.0\\.0\\.1" in opts["allow_origin_regex"]
    assert opts["allow_credentials"] is False
    assert opts["allow_methods"] == ["GET", "POST"]
    assert "*" not in opts["allow_origins"]


def _minimal_watchlist():
    return {
        "schema_version": "m5n_watchlist.v1",
        "watchlist_id": "m6d_test",
        "items": [
            {
                "id": "twse:2330",
                "symbol": "2330",
                "display_name": "2330",
                "market": "twse",
                "instrument_type": "listed_stock",
                "adapter": "twse_mis_equity_etf_quote",
                "preferred_sources": ["TWSE_MIS"],
                "category": "test",
                "enabled": True,
                "display_order": 1,
                "tags": [],
                "notes": "descriptive",
            }
        ],
    }


def test_fastapi_m5k_legacy_execution_route_is_disabled(monkeypatch):
    calls = []
    monkeypatch.setattr(server_main, "_m5k_execute_live_observation", lambda *a, **k: calls.append("called"), raising=False)
    client = TestClient(server_main.app)
    for query in (
        "confirm_live_observation=true&ssl_policy=invalid",
        "confirm_live_observation=true&ssl_policy=strict",
        "confirm_live_observation=true&ssl_policy=compatibility",
        "confirm_live_observation=true&ssl_policy=unsafe-explicit",
    ):
        response = client.post(f"/api/m5k/live-observation/execute?{query}", json=_minimal_watchlist())
        assert response.status_code == 410
        assert response.json()["detail"]["error"] == "legacy_live_observation_execution_disabled"
    assert calls == []


def test_mcp_ssl_policy_fail_closed_and_valid_values(monkeypatch):
    executed = False
    def fake_execute(*args, **kwargs):
        nonlocal executed
        executed = True
        return {"status": "should_not_execute"}
    monkeypatch.setattr(mcp_server, "_m5k_execute_live_observation", fake_execute)

    result = mcp_server.run_m5k_live_observation_tool({"confirm_live_observation": True, "watchlist": _minimal_watchlist(), "ssl_policy": "invalid"})

    assert result["status"] == "failed_closed"
    assert result["failure_reason"] == "invalid_ssl_policy"
    assert result["network_calls"] is False
    assert result["artifact_writes"] is False
    assert executed is False
    calls = []
    def fake_execute(watchlist, write_latest=True, ssl_policy=None):
        calls.append(ssl_policy)
        return {"status": "ok", "governance": {"ssl_policy": ssl_policy}}
    monkeypatch.setattr(mcp_server, "_m5k_execute_live_observation", fake_execute)

    for policy in ["strict", "compatibility", "unsafe-explicit"]:
        result = mcp_server.run_m5k_live_observation_tool({"confirm_live_observation": True, "watchlist": _minimal_watchlist(), "ssl_policy": policy})
        assert result["status"] == "ok"
        assert result["governance"]["ssl_policy"] == policy
    assert calls == ["strict", "compatibility", "unsafe-explicit"]
