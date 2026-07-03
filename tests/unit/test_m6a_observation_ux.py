from pathlib import Path

from fastapi.testclient import TestClient

from server.main import app, _observation_counts

JS = Path("frontend/readonly-preview/m5k-workbench.js").read_text(encoding="utf-8")
HTML = Path("frontend/readonly-preview/M5KLocalAIWorkbench.html").read_text(encoding="utf-8")


def test_frontend_static_operator_contract_strings():
    assert "file:" in JS
    assert "http://127.0.0.1:8000" in JS
    assert "localhost" in JS
    assert "loc.port !== '8000'" in JS
    assert "return loc.origin" in JS
    assert "uvicorn server.main:app --host 127.0.0.1 --port 8000" in JS + HTML
    for token in ["watchlistSlots", "duplicateWatchlist", "importWatchlist", "exportWatchlist", "Watchlist import validation error"]:
        assert token in JS + HTML
    for token in [
        "/api/m5k/live-observation/history",
        "Observation comparison only. Not a trading signal. Not current price guarantee.",
        "observationTimelineRows",
        "observationDiffRows",
        "/api/source-health/history",
        "sourceHealthTimelineRows",
        "copy JSON",
        "copy Markdown",
        "download JSON",
        "download Markdown",
        "AI safety reminder",
    ]:
        assert token in JS + HTML
    dom_handler = JS.split("window.addEventListener('DOMContentLoaded'", 1)[1]
    assert "executeObservation()" not in dom_handler
    assert "setInterval" not in JS
    assert "setTimeout" not in JS
    forbidden = ["buy/sell/hold", "target price", "ranking"]
    lowered = (JS + HTML).lower()
    for token in forbidden:
        assert token not in lowered
    assert "raw_payload_hidden" in JS
    assert "raw endpoint payload is excluded" in HTML.lower()


def test_fastapi_local_cors_policy_allows_localhost_127_and_file_null_without_credentials():
    client = TestClient(app)
    for origin in ["http://localhost:5173", "http://127.0.0.1:5173", "null"]:
        r = client.options(
            "/api/health",
            headers={"Origin": origin, "Access-Control-Request-Method": "GET"},
        )
        assert r.status_code == 200
        assert r.headers["access-control-allow-origin"] == origin
        assert "access-control-allow-credentials" not in r.headers


def test_fastapi_history_endpoints_are_readonly_summaries():
    client = TestClient(app)
    obs = client.get("/api/m5k/live-observation/history")
    health = client.get("/api/source-health/history")
    assert obs.status_code == 200
    assert health.status_code == 200
    assert obs.json()["governance"]["network_calls"] is False
    assert health.json()["governance"]["network_calls"] is False
    assert obs.json()["governance"]["raw_endpoint_payload_included"] is False
    assert health.json()["governance"]["raw_endpoint_payload_included"] is False


def test_observation_counts_treat_closed_session_rows_as_degraded():
    counts = _observation_counts({"observations": [{"status": "ok", "freshness_assessment": "stale_or_closed_session"}]})
    assert counts["healthy"] == 0
    assert counts["degraded"] == 1
    counts = _observation_counts({"observations": [{"status": "ok", "caveats": ["closed-session data must be treated as degraded"]}]})
    assert counts["healthy"] == 0
    assert counts["degraded"] == 1
