import pytest
import sys
from pathlib import Path
from server.services.unified_mode_a import validate_mode_a_request

def test_valid_mode_a_request():
    req = {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": "test-req",
        "execution_mode": "preview",
        "targets": [
            {"input": "2330", "market_hint": "TWSE"}
        ],
        "data_needs": [
            {"type": "identity", "priority": "required"}
        ]
    }
    result = validate_mode_a_request(req)
    assert result["validation_status"] == "valid"
    assert result["validation_metadata"]["offline"] is True
    assert result["validation_metadata"]["deterministic"] is True
    assert len(result["blocking_issues"]) == 0
    assert result["target_results"][0]["canonical_identity"]["market"] == "TWSE"

def test_invalid_mode_a_request_target_limit():
    req = {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": "test-limit",
        "execution_mode": "preview",
        "targets": [{"input": str(i)} for i in range(100)],
        "data_needs": [{"type": "identity", "priority": "required"}]
    }
    result = validate_mode_a_request(req)
    assert result["validation_status"] == "invalid"
    assert any(b["code"] == "TARGET_LIMIT_EXCEEDED" for b in result["blocking_issues"])

def test_no_network_monkeypatch(monkeypatch):
    """
    Ensure no network calls are made during validation.
    """
    import socket
    import urllib.request
    
    def mock_socket(*args, **kwargs):
        raise RuntimeError("Network access forbidden in Mode A")
    
    def mock_urllib(*args, **kwargs):
        raise RuntimeError("Network access forbidden in Mode A")
        
    monkeypatch.setattr(socket, "socket", mock_socket)
    monkeypatch.setattr(urllib.request, "urlopen", mock_urllib)
    
    if "requests" in sys.modules:
        monkeypatch.setattr(sys.modules["requests"], "get", mock_urllib)
    if "httpx" in sys.modules:
        monkeypatch.setattr(sys.modules["httpx"], "get", mock_urllib)

    req = {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": "test-offline",
        "execution_mode": "preview",
        "targets": [{"input": "2330"}],
        "data_needs": [{"type": "identity", "priority": "required"}]
    }
    # Should not raise any network errors
    result = validate_mode_a_request(req)
    assert result["validation_status"] == "valid"
