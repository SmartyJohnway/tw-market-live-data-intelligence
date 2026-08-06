import json
from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app)

from pathlib import Path
import pytest

@pytest.fixture()
def mock_validation(monkeypatch):
    from server import unified_workbench_router
    def fake_validate(req):
        return {
            "request_id": req.get("request_id"),
            "validation_status": "valid",
            "target_results": [{"canonical_identity": {"market": "TWSE"}}]
        }
    monkeypatch.setattr(unified_workbench_router, "validate_mode_a_request", fake_validate)

def test_production_boundary_enforced():
    # In a fresh environment without the monkeypatch above, the router would attempt
    # to load the production snapshot which doesn't exist, and return 409.
    # We test the raw adapter function here to ensure it raises correctly.
    from server.services.unified_mode_a import validate_mode_a_request
    from pathlib import Path
    import pytest
    
    req = {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": "test-prod",
        "execution_mode": "preview",
        "targets": [{"input": "2330"}],
        "data_needs": []
    }
    with pytest.raises(FileNotFoundError):
        validate_mode_a_request(req) # defaults to allow_fixture_snapshot=False

def test_api_returns_409_when_production_security_master_missing():
    req = {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": "test-prod",
        "execution_mode": "preview",
        "targets": [{"input": "2330"}],
        "data_needs": []
    }
    response = client.post("/api/unified/validate-request", json={"request": req})
    assert response.status_code == 409
    data = response.json()
    assert data["error"] == "canonical_security_master_unavailable"
    assert "trace_id" in data
    # Ensure no absolute paths or tracebacks are leaked
    error_str = str(data).lower()
    assert "tests/fixtures" not in error_str
    assert "traceback" not in error_str
    assert "\\" not in error_str and "/" not in data.get("detail", "")

def test_non_root_cwd_isolation(monkeypatch):
    import os
    from server.services.unified_mode_a import validate_mode_a_request
    
    # Change CWD to something else
    original_cwd = os.getcwd()
    try:
        os.chdir(os.path.dirname(__file__))
        req = {
            "schema_version": "unified_market_evidence_request.v1",
            "request_id": "test-prod",
            "execution_mode": "preview",
            "targets": [{"input": "2330"}],
            "data_needs": [{"type": "identity", "priority": "required"}]
        }
        # It should still find the files correctly and raise FileNotFoundError for production snapshot
        # rather than crashing with some other random path error, or if we pass allow_fixture_snapshot=True,
        # it should succeed!
        result = validate_mode_a_request(req, allow_fixture_snapshot=True)
        assert result["validation_status"] == "valid"
    finally:
        os.chdir(original_cwd)

def test_validate_request_valid_envelope(mock_validation):
    req = {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": "api-test",
        "execution_mode": "preview",
        "targets": [{"input": "2330"}],
        "data_needs": [{"type": "identity", "priority": "required"}]
    }
    response = client.post("/api/unified/validate-request", json={"request": req})
    assert response.status_code == 200
    data = response.json()
    assert data["validation_status"] == "valid"
    assert data["target_results"][0]["canonical_identity"]["market"] == "TWSE"

def test_validate_request_oversized_body(mock_validation):
    large_payload = "a" * (1 * 1024 * 1024 + 1)
    response = client.post("/api/unified/validate-request", content=large_payload)
    assert response.status_code == 413

def test_validate_request_missing_envelope(mock_validation):
    response = client.post("/api/unified/validate-request", json={})
    assert response.status_code == 422
    assert "missing 'request' key" in response.json()["detail"]

def test_validate_request_malformed_json(mock_validation):
    response = client.post("/api/unified/validate-request", content="{invalid json", headers={"Content-Type": "application/json"})
    assert response.status_code == 400
    assert response.json()["detail"] == "malformed_json_body"

def test_validate_request_too_large():
    large_req = {"request": {"targets": [{"input": "A" * (1 * 1024 * 1024)}]}}
    response = client.post("/api/unified/validate-request", json=large_req)
    assert response.status_code == 413
    assert response.json()["detail"] == "request_too_large"
