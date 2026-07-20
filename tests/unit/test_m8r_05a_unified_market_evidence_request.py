import json
import pytest
from pathlib import Path
from jsonschema import validate, ValidationError

SCHEMA_PATH = Path(__file__).parent.parent.parent / "schemas" / "unified_market_evidence_request.v1.schema.json"
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "m8r_05a"

@pytest.fixture(scope="module")
def request_schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def test_valid_request_from_fixture(request_schema):
    with open(FIXTURES_DIR / "valid_request.json", "r", encoding="utf-8") as f:
        req = json.load(f)
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

def test_invalid_request_from_fixture(request_schema):
    with open(FIXTURES_DIR / "invalid_request.json", "r", encoding="utf-8") as f:
        req = json.load(f)
    with pytest.raises(ValidationError):
        validate(instance=req, schema=request_schema)

def test_invalid_request_market_hint(request_schema):
    req = {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": "req-invalid",
        "targets": [{"input": "台積電", "market_hint": "INVALID"}],
        "data_needs": [{"type": "current_observation", "priority": "required"}],
        "execution_mode": "preview"
    }
    with pytest.raises(ValidationError, match="INVALID"):
        validate(instance=req, schema=request_schema)

def test_invalid_request_parameters(request_schema):
    req = {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": "req-invalid",
        "targets": [{"input": "台積電"}],
        "data_needs": [{"type": "current_observation", "priority": "required", "parameters": {"adapter": "twse_mis"}}],
        "execution_mode": "preview"
    }
    with pytest.raises(ValidationError):
        validate(instance=req, schema=request_schema)

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
