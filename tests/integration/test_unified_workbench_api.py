import json
from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app)

def test_validate_request_valid_envelope():
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

def test_validate_request_missing_envelope():
    req = {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": "api-test"
    }
    response = client.post("/api/unified/validate-request", json=req)
    assert response.status_code == 422
    assert "missing 'request' key" in response.json()["detail"]

def test_validate_request_malformed_json():
    response = client.post("/api/unified/validate-request", content="{invalid json", headers={"Content-Type": "application/json"})
    assert response.status_code == 400
    assert response.json()["detail"] == "malformed_json_body"

def test_validate_request_too_large():
    large_req = {"request": {"targets": [{"input": "A" * (1 * 1024 * 1024)}]}}
    response = client.post("/api/unified/validate-request", json=large_req)
    assert response.status_code == 413
    assert response.json()["detail"] == "request_too_large"
