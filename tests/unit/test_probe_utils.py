import sys
import os
import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
from probe_utils import generate_standard_envelope

def test_generate_standard_envelope():
    envelope = generate_standard_envelope(
        probe_id="test_123",
        source="Test_Source",
        source_type="test_type",
        contract_status="normalized_pass",
        http_status=200,
        url="http://example.com",
        normalized_sample={"symbol": "1234", "price": 100},
        freshness_status="eod_batch",
        staleness_seconds=3600,
        risk_level="low",
        ai_suitability="historical_and_eod",
        unsupported_targets=["funds"],
        failed_targets=["9999"]
    )

    assert envelope["probe_id"] == "test_123"
    assert envelope["source"] == "Test_Source"
    assert envelope["contract_status"] == "normalized_pass"
    assert envelope["status"] == "pass"
    assert envelope["http_status"] == 200
    assert "retrieved_at_utc" in envelope
    assert envelope["schema_hash"] is not None
    assert envelope["unsupported_targets"] == ["funds"]
    assert envelope["failed_targets"] == ["9999"]

def test_generate_standard_envelope_error():
    envelope = generate_standard_envelope(
        probe_id="test_456",
        source="Test_Source_Error",
        source_type="test_type",
        contract_status="failed",
        http_status="Error",
        url="http://example.com",
        error="Connection Timeout"
    )

    assert envelope["contract_status"] == "failed"
    assert envelope["status"] == "failed"
    assert envelope["error"] == "Connection Timeout"
    assert envelope["schema_hash"] is None
