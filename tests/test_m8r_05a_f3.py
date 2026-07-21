import json
import pytest
from scripts.m8r_05a_f3.request_intake import validate_unified_market_evidence_request

@pytest.fixture
def test_schema():
    with open("schemas/unified_market_evidence_request.v1.schema.json", "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture
def test_catalog():
    with open("docs/data_capabilities/unified_market_evidence_capability_catalog.v1.json", "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture
def test_security_master():
    # Use the local mock snapshot for deterministic testing
    return [
        {
            "identity": {
                "security_code": "2330",
                "security_name_zh": "台積電"
            },
            "classification": {
                "market": "TWSE",
                "instrument_type": "EQUITY"
            }
        },
        {
            "identity": {
                "security_code": "5347",
                "security_name_zh": "世界"
            },
            "classification": {
                "market": "TPEX",
                "instrument_type": "EQUITY"
            }
        }
    ]

def test_valid_request(test_schema, test_catalog, test_security_master):
    req = {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": "req-1",
        "targets": [
            {
                "input": "2330",
                "market_hint": "TWSE",
                "resolution_requirement": "exact"
            }
        ],
        "data_needs": [
            {
                "type": "official_eod_reference",
                "priority": "required"
            }
        ],
        "execution_mode": "preview"
    }
    
    res = validate_unified_market_evidence_request(
        req, 
        security_master=test_security_master, 
        capability_catalog=test_catalog, 
        request_schema=test_schema
    )
    
    assert res["validation_status"] == "valid"
    assert res["target_results"][0]["resolution_status"] == "resolved"
    assert res["target_results"][0]["canonical_identity"]["market"] == "TWSE"

def test_market_mismatch(test_schema, test_catalog, test_security_master):
    req = {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": "req-2",
        "targets": [
            {
                "input": "2330",
                "market_hint": "TPEX",
                "resolution_requirement": "exact"
            }
        ],
        "data_needs": [
            {
                "type": "official_eod_reference",
                "priority": "required"
            }
        ],
        "execution_mode": "preview"
    }
    
    res = validate_unified_market_evidence_request(
        req, 
        security_master=test_security_master, 
        capability_catalog=test_catalog, 
        request_schema=test_schema
    )
    
    assert res["validation_status"] == "invalid"
    assert res["target_validation_status"] == "invalid"
    assert res["target_results"][0]["resolution_status"] == "market_mismatch"
    assert "TARGET_MARKET_MISMATCH" in res["target_results"][0]["reason_codes"]

def test_invalid_schema(test_schema, test_catalog, test_security_master):
    req = {
        "schema_version": "unified_market_evidence_request.v1",
        "targets": [] # missing required fields
    }
    
    res = validate_unified_market_evidence_request(
        req, 
        security_master=test_security_master, 
        capability_catalog=test_catalog, 
        request_schema=test_schema
    )
    
    assert res["validation_status"] == "invalid"
    assert res["request_schema_status"] == "invalid"
    assert res["blocking_issues"][0]["reason_code"] == "REQUEST_SCHEMA_INVALID"

def test_unsupported_capability(test_schema, test_catalog, test_security_master):
    # Modify the catalog specifically for this test
    # We will make official_eod_reference not supported for TWSE
    modified_catalog = json.loads(json.dumps(test_catalog))
    for cap in modified_catalog["data_need_capabilities"]:
        if cap["capability_id"] == "official_eod_reference":
            cap["supported_markets"] = ["TPEX"] # Exclude TWSE
            
    req = {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": "req-3",
        "targets": [
            {
                "input": "2330",
                "market_hint": "TWSE",
                "resolution_requirement": "exact"
            }
        ],
        "data_needs": [
            {
                "type": "official_eod_reference",
                "priority": "required"
            }
        ],
        "execution_mode": "preview"
    }
    
    res = validate_unified_market_evidence_request(
        req, 
        security_master=test_security_master, 
        capability_catalog=modified_catalog, 
        request_schema=test_schema
    )
    
    assert res["validation_status"] == "unsupported"
    assert res["capability_validation_status"] == "unsupported"
    assert res["capability_results"][0]["status"] == "unsupported"
    assert "CAPABILITY_UNSUPPORTED_FOR_MARKET" in res["capability_results"][0]["reason_codes"]

def test_ambiguous_resolution(test_schema, test_catalog):
    ambiguous_master = [
        {
            "identity": {
                "security_code": "2330",
                "security_name_zh": "台積電"
            },
            "classification": {
                "market": "TWSE",
                "instrument_type": "EQUITY"
            }
        },
        {
            "identity": {
                "security_code": "2330",
                "security_name_zh": "台積電"
            },
            "classification": {
                "market": "TPEX",
                "instrument_type": "EQUITY"
            }
        }
    ]
    
    req = {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": "req-4",
        "targets": [
            {
                "input": "2330",
                "resolution_requirement": "exact"
            }
        ],
        "data_needs": [
            {
                "type": "official_eod_reference",
                "priority": "required"
            }
        ],
        "execution_mode": "preview"
    }
    
    res = validate_unified_market_evidence_request(
        req, 
        security_master=ambiguous_master, 
        capability_catalog=test_catalog, 
        request_schema=test_schema
    )
    
    assert res["validation_status"] == "requires_clarification"
    assert res["target_validation_status"] == "requires_clarification"
    assert res["target_results"][0]["resolution_status"] == "ambiguous"
    assert len(res["target_results"][0]["candidate_matches"]) == 2
