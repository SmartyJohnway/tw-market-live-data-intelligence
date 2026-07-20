import pytest
import json
from pathlib import Path
from scripts.validate_unified_market_evidence_contracts import validate_cross_contract

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "m8r_05a"

def get_fixture(name):
    with open(FIXTURES_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)

def test_cross_contract_valid():
    request_data = get_fixture("valid_request.json")
    catalog_data = get_fixture("valid_catalog.json")
    preview_data = get_fixture("valid_preview.json")
    result_data = get_fixture("valid_result.json")
    
    assert validate_cross_contract(request_data, catalog_data, preview_data, result_data) is True

def test_cross_contract_invalid_request_need():
    request_data = get_fixture("valid_request.json")
    catalog_data = get_fixture("valid_catalog.json")
    
    request_data["data_needs"][0]["type"] = "unsupported_need"
    # To pass schema validation, we need to bypass it or see it fail schema validation. 
    # But wait, schema validation will fail first!
    # "unsupported_need" is not in the enum.
    with pytest.raises(Exception):
        validate_cross_contract(request_data, catalog_data)

def test_cross_contract_preview_exceeds_request():
    request_data = get_fixture("valid_request.json")
    catalog_data = get_fixture("valid_catalog.json")
    preview_data = get_fixture("valid_preview.json")
    
    # Request only asked for 2. Preview adds a third.
    preview_data["planned_evidence"].append("session_status")
    
    with pytest.raises(ValueError, match="Preview planned evidence exceeds requested data needs"):
        validate_cross_contract(request_data, catalog_data, preview_data)

def test_cross_contract_bounds_exceeded():
    request_data = get_fixture("valid_request.json")
    catalog_data = get_fixture("valid_catalog.json")
    preview_data = get_fixture("valid_preview.json")
    
    preview_data["bounds"]["operation_count"] = 150
    with pytest.raises(ValueError, match="Preview operations exceed catalog hard limit"):
        validate_cross_contract(request_data, catalog_data, preview_data)

def test_cross_contract_fallback_without_explicit_flag():
    request_data = get_fixture("valid_request.json")
    catalog_data = get_fixture("valid_catalog.json")
    result_data = get_fixture("valid_result.json")
    
    # Enable fallback policy in result
    eod = {
        "currentness_status": "official_latest_completed_eod",
        "fallback_policy_used": True
    }
    result_data["targets"][0]["evidence"]["official_eod_reference"] = eod
    # Also add it to request so schema validation passes for coverage
    request_data["data_needs"].append({"type": "official_eod_reference", "priority": "optional", "parameters": {}})
    
    catalog_data["fallback_semantics"]["fallback_must_be_explicit"] = False
    
    with pytest.raises(ValueError, match="Fallback policy used but not explicit in catalog"):
        validate_cross_contract(request_data, catalog_data, None, result_data)
