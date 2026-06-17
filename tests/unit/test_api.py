import sys
import os
import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'server'))
from main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "TW-Market Live Data Intelligence API is running."}

@pytest.mark.network
def test_probe_endpoints_exist():
    # We only test if the endpoint structure works and does not instantly crash
    # without running everything.
    response = client.get("/api/probe/yahoo")
    assert response.status_code == 200
    assert "probe_id" in response.json()
    assert "source" in response.json()
