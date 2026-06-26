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

def test_matrix_endpoint_error_if_not_run():
    # If matrix.json doesn't exist, it should return 404
    # We rename it temporarily if it exists to test the 404 path
    matrix_path = os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'public', 'matrix.json')
    temp_path = matrix_path + ".bak"
    if os.path.exists(matrix_path):
        os.rename(matrix_path, temp_path)

    try:
        response = client.get("/api/matrix")
        assert response.status_code == 404
    finally:
        if os.path.exists(temp_path):
            os.rename(temp_path, matrix_path)

def test_governance_endpoint_describes_manual_probe_boundary():
    response = client.get("/api/governance")
    assert response.status_code == 200
    data = response.json()
    assert data["api_mode"] == "local_first_governed_workbench"
    assert data["probe_endpoints"]["requires_query"] == "confirm_manual_probe=true"
    assert data["probe_endpoints"]["production_refresh"] is False
    assert "manual_legacy_probe_surface" in data["probe_endpoints"]["caveats"]


@pytest.mark.parametrize(
    ("path", "probe_attr"),
    [
        ("/api/probe/twse", "probe_twse"),
        ("/api/probe/tpex", "probe_tpex"),
        ("/api/probe/yahoo", "probe_yahoo"),
        ("/api/probe/twse_mis", "probe_mis"),
        ("/api/probe/finmind", "probe_finmind"),
        ("/api/probe/feasibility", "probe_fugle_fubon"),
    ],
)
def test_probe_endpoints_require_manual_confirmation_without_executing_probe(monkeypatch, path, probe_attr):
    called = {"value": False}

    def fake_probe(*args, **kwargs):
        called["value"] = True
        return {"source": "mock"}

    monkeypatch.setattr(f"main.{probe_attr}", fake_probe)
    response = client.get(path)

    assert response.status_code == 403
    assert response.json()["detail"]["error"] == "manual_probe_confirmation_required"
    assert response.json()["detail"]["required_query"] == "confirm_manual_probe=true"
    assert "no_production_artifact_refresh" in response.json()["detail"]["caveats"]
    assert called["value"] is False


def test_probe_endpoint_with_manual_confirmation_wraps_governance(monkeypatch):
    def fake_probe():
        return {"source": "TWSE_OpenAPI", "contract_status": "normalized_pass"}

    monkeypatch.setattr("main.probe_twse", fake_probe)
    response = client.get("/api/probe/twse?confirm_manual_probe=true")

    assert response.status_code == 200
    data = response.json()
    assert data["governance"]["execution_mode"] == "manual_explicit_probe"
    assert data["governance"]["production_refresh"] is False
    assert data["governance"]["frontend_refresh"] is False
    assert data["governance"]["source_id"] == "TWSE_OpenAPI"
    assert data["result"]["contract_status"] == "normalized_pass"
