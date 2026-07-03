import pytest
import os
import sys

# Ensure scripts directory can be imported
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'server'))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "running locally" in response.json()["message"]

def test_matrix_endpoint_returns_validated_m5f_capability_summary():
    response = client.get("/api/matrix")
    assert response.status_code == 200
    data = response.json()
    assert data["source_path"] == "research/staging/m5f/m5f_canonical_market_context_01/capability_summary.json"
    assert data["content"]["canonical_context"] == "available"
    assert data["content"]["symbol_count"] == 3

def test_governance_endpoint_describes_manual_probe_boundary():
    response = client.get("/api/governance")
    assert response.status_code == 200
    data = response.json()
    assert data["api_mode"] == "local_first_governed_workbench"
    assert data["probe_endpoints"]["requires_query"] is None
    assert data["probe_endpoints"]["production_refresh"] is False
    assert "legacy_probe_surface_disabled_pending_m5i" in data["probe_endpoints"]["caveats"]


@pytest.mark.parametrize(
    "path",
    [
        "/api/probe/twse",
        "/api/probe/tpex",
        "/api/probe/yahoo",
        "/api/probe/twse_mis",
        "/api/probe/finmind",
        "/api/probe/feasibility",
    ],
)
def test_probe_endpoints_disabled_without_live_imports(path):
    import main
    for attr in ["probe_twse", "probe_tpex", "probe_yahoo", "probe_mis", "probe_finmind", "probe_fugle_fubon"]:
        assert not hasattr(main, attr)
    response = client.get(path)

    assert response.status_code == 410
    assert response.json()["detail"]["error"] == "legacy_probe_endpoint_disabled_pending_m5i_authorization"
    assert response.json()["detail"]["required_query"] is None
    assert "no_production_artifact_refresh" in response.json()["detail"]["caveats"]


def test_probe_endpoint_with_manual_confirmation_still_disabled():
    response = client.get("/api/probe/twse?confirm_manual_probe=true")

    assert response.status_code == 410
    assert response.json()["detail"]["error"] == "legacy_probe_endpoint_disabled_pending_m5i_authorization"

@pytest.mark.parametrize(
    ("env_policy", "query_policy", "expected"),
    [
        (None, None, "strict"),
        ("compatibility", None, "compatibility"),
        ("unsafe-explicit", None, "unsafe-explicit"),
        ("compatibility", "strict", "strict"),
        ("strict", "compatibility", "compatibility"),
        ("not-a-policy", "unsafe-explicit", "unsafe-explicit"),
    ],
)
def test_fastapi_live_observation_resolves_ssl_policy_env_and_query(monkeypatch, env_policy, query_policy, expected):
    import main

    calls = []

    def fake_execute(watchlist, write_latest=True, ssl_policy="strict"):
        calls.append({"watchlist": watchlist, "write_latest": write_latest, "ssl_policy": ssl_policy})
        return {"status": "ok", "diagnostics": {"ssl_policy": {"selected": ssl_policy}}}

    if env_policy is None:
        monkeypatch.delenv("TW_MARKET_SSL_POLICY", raising=False)
    else:
        monkeypatch.setenv("TW_MARKET_SSL_POLICY", env_policy)
    monkeypatch.setattr(main, "_m5k_execute_live_observation", fake_execute)

    url = "/api/m5k/live-observation/execute?confirm_live_observation=true"
    if query_policy is not None:
        url += f"&ssl_policy={query_policy}"
    response = client.post(url, json={"schema_version": "m5n_watchlist.v1", "items": []})

    assert response.status_code == 200
    assert calls == [{"watchlist": {"schema_version": "m5n_watchlist.v1", "items": []}, "write_latest": True, "ssl_policy": expected}]
    assert response.json()["diagnostics"]["ssl_policy"]["selected"] == expected


@pytest.mark.parametrize(
    ("env_policy", "query_policy"),
    [
        ("strict", "invalid"),
        ("invalid", None),
    ],
)
def test_fastapi_live_observation_invalid_ssl_policy_fails_before_execution(monkeypatch, env_policy, query_policy):
    import main

    calls = []
    monkeypatch.setenv("TW_MARKET_SSL_POLICY", env_policy)
    monkeypatch.setattr(main, "_m5k_execute_live_observation", lambda *args, **kwargs: calls.append((args, kwargs)))

    url = "/api/m5k/live-observation/execute?confirm_live_observation=true"
    if query_policy is not None:
        url += f"&ssl_policy={query_policy}"
    response = client.post(url, json={"schema_version": "m5n_watchlist.v1", "items": []})

    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "invalid_ssl_policy"
    assert calls == []
