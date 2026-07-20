import json
import pytest
from pathlib import Path
from jsonschema import validate, ValidationError

SCHEMA_PATH = Path(__file__).parent.parent.parent / "schemas" / "unified_market_evidence_request.v1.schema.json"

@pytest.fixture(scope="module")
def request_schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def test_valid_request_chinese_company_name(request_schema):
    req = {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": "req-001",
        "targets": [{"input": "台積電", "resolution_requirement": "allow_ambiguity"}],
        "data_needs": [{"type": "current_observation", "priority": "required"}],
        "execution_mode": "preview"
    }
    validate(instance=req, schema=request_schema)

def test_valid_request_numeric_code_with_market_hint(request_schema):
    req = {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": "req-002",
        "targets": [{"input": "2330", "market_hint": "TWSE", "resolution_requirement": "exact"}],
        "data_needs": [{"type": "official_eod_reference", "priority": "required"}],
        "execution_mode": "preview"
    }
    validate(instance=req, schema=request_schema)

def test_valid_request_multiple_targets_and_needs(request_schema):
    req = {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": "req-003",
        "targets": [
            {"input": "2330"},
            {"input": "聯發科"}
        ],
        "data_needs": [
            {"type": "identity", "priority": "required"},
            {"type": "recent_performance", "priority": "optional", "parameters": {"lookback_trading_days": 20}}
        ],
        "execution_mode": "preview"
    }
    validate(instance=req, schema=request_schema)

def test_valid_request_execute_mode(request_schema):
    req = {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": "req-004",
        "targets": [{"input": "台積電"}],
        "data_needs": [{"type": "session_status", "priority": "required"}],
        "execution_mode": "execute",
        "response_preferences": {"include_citations": True}
    }
    validate(instance=req, schema=request_schema)

# Negative Fixtures

def test_invalid_request_empty_targets(request_schema):
    req = {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": "req-invalid",
        "targets": [],
        "data_needs": [{"type": "current_observation", "priority": "required"}],
        "execution_mode": "preview"
    }
    with pytest.raises(ValidationError):
        validate(instance=req, schema=request_schema)

def test_invalid_request_empty_data_needs(request_schema):
    req = {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": "req-invalid",
        "targets": [{"input": "台積電"}],
        "data_needs": [],
        "execution_mode": "preview"
    }
    with pytest.raises(ValidationError):
        validate(instance=req, schema=request_schema)

def test_invalid_request_unknown_data_need(request_schema):
    req = {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": "req-invalid",
        "targets": [{"input": "台積電"}],
        "data_needs": [{"type": "unknown_need_type", "priority": "required"}],
        "execution_mode": "preview"
    }
    with pytest.raises(ValidationError):
        validate(instance=req, schema=request_schema)

def test_invalid_request_hardcoded_internal_fields(request_schema):
    req = {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": "req-invalid",
        "targets": [{"input": "台積電"}],
        "data_needs": [{"type": "current_observation", "priority": "required"}],
        "execution_mode": "preview",
        "source_family": "twse_mis",  # Prohibited
        "adapter": "some_adapter"     # Prohibited
    }
    with pytest.raises(ValidationError, match="Additional properties are not allowed"):
        validate(instance=req, schema=request_schema)

def test_invalid_request_target_hardcoded_internal_fields(request_schema):
    req = {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": "req-invalid",
        "targets": [{"input": "台積電", "url": "http://example.com"}], # Prohibited
        "data_needs": [{"type": "current_observation", "priority": "required"}],
        "execution_mode": "preview"
    }
    with pytest.raises(ValidationError, match="Additional properties are not allowed"):
        validate(instance=req, schema=request_schema)
