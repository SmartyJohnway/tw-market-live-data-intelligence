import pytest
from datetime import datetime
import os
import sys

# Ensure scripts directory can be imported
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))

from probe_utils import generate_standard_envelope

def test_generate_standard_envelope():
    env = generate_standard_envelope(
        probe_id="test_123",
        source="Test_Source",
        source_type="official_api",
        contract_status="normalized_pass",
        http_status=200,
        url="http://test.com",
        raw_sample={"id": 1, "val": "A"},
        normalized_sample={"value": "A"},
        freshness_status="realtime",
        staleness_seconds=10,
        delay_status="realtime"
    )

    assert env["probe_id"] == "test_123"
    assert env["is_usable_now"] is True
    assert env["http_ok"] is True
    assert env["parse_status"] == "success"
    assert env["normalization_status"] == "success"
    assert "schema_fingerprint" in env
    assert env["schema_fingerprint"]["type"] == "dict"
    assert env["schema_fingerprint"]["keys"] == ["value"]

def test_envelope_doc_only_classification():
    env = generate_standard_envelope(
        probe_id="test_123",
        source="Test_Doc",
        source_type="broker_api",
        contract_status="doc_only",
        http_status="N/A",
        url="http://test.com",
        requires_auth=True
    )

    assert env["is_usable_now"] is False
    assert env["potentially_usable_with_credentials"] is True
    assert env["http_ok"] is False
    assert env["parse_status"] == "unknown"
    assert env["normalization_status"] == "unknown"

def test_envelope_auth_required_classification():
    env = generate_standard_envelope(
        probe_id="test_123",
        source="Test_Auth",
        source_type="commercial_api",
        contract_status="auth_required",
        http_status=401,
        url="http://test.com",
        requires_auth=True
    )

    assert env["is_usable_now"] is False
    assert env["potentially_usable_with_credentials"] is True

def test_envelope_failed_classification():
    env = generate_standard_envelope(
        probe_id="test_123",
        source="Test_Fail",
        source_type="official_api",
        contract_status="failed",
        http_status=500,
        url="http://test.com",
        errors=["Internal Server Error"]
    )

    assert env["is_usable_now"] is False
    assert env["http_ok"] is False
    assert env["parse_status"] == "failed"
    assert env["normalization_status"] == "failed"
