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
    with pytest.raises(Exception):
        validate_cross_contract(request_data, catalog_data)

def test_cross_contract_preview_exceeds_request():
    request_data = get_fixture("valid_request.json")
    catalog_data = get_fixture("valid_catalog.json")
    preview_data = get_fixture("valid_preview.json")
    
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

def test_cross_contract_fallback_upgrade_fails():
    request_data = get_fixture("valid_request.json")
    catalog_data = get_fixture("valid_catalog.json")
    result_data = get_fixture("valid_result.json")
    
    # recent_performance does not have liveish_intraday_snapshot in its possible_fallbacks
    result_data["targets"][0]["evidence"]["recent_performance"]["timing_class"] = "official_eod"
    result_data["targets"][0]["evidence"]["recent_performance"]["currentness"] = {
        "timing_class": "official_eod",
        "fallback_timing_class": "liveish_intraday_snapshot"
    }
    
    with pytest.raises(ValueError, match="Fallback timing class liveish_intraday_snapshot not allowed for recent_performance"):
        validate_cross_contract(request_data, catalog_data, None, result_data)

def test_cross_contract_forbidden_fields():
    request_data = get_fixture("valid_request.json")
    catalog_data = get_fixture("valid_catalog.json")
    result_data = get_fixture("valid_result.json")
    
    result_data["targets"][0]["evidence"]["current_observation"]["observed_fields"]["bullish"] = True
    
    with pytest.raises(ValueError, match="Forbidden key 'bullish' found in result payload"):
        validate_cross_contract(request_data, catalog_data, None, result_data)

def test_cross_contract_provisional_market_caveat():
    request_data = get_fixture("valid_request.json")
    catalog_data = get_fixture("valid_catalog.json")
    preview_data = get_fixture("valid_preview.json")
    
    # Change target market to TAIFEX, which is provisional for recent_performance
    request_data["targets"][0]["market_hint"] = "TAIFEX"
    # Ensure it's not supported for current_observation so we remove that
    request_data["data_needs"].pop()
    preview_data["requested_data_needs"].pop()
    preview_data["planned_evidence"].pop()
    
    # Should fail if no caveat
    with pytest.raises(ValueError, match="Provisional market capability planned but no caveat provided"):
        validate_cross_contract(request_data, catalog_data, preview_data)
        
    # With caveat, it should pass
    preview_data["caveats"] = ["TAIFEX is provisional"]
    assert validate_cross_contract(request_data, catalog_data, preview_data) is True

def test_cross_contract_market_support_fail():
    request_data = get_fixture("valid_request.json")
    catalog_data = get_fixture("valid_catalog.json")
    
    request_data["targets"][0]["market_hint"] = "TAIFEX"
    # TAIFEX is unsupported for current_observation
    with pytest.raises(ValueError, match="capability current_observation unsupported for market TAIFEX"):
        validate_cross_contract(request_data, catalog_data)

def test_cross_contract_not_executable_plan():
    request_data = get_fixture("valid_request.json")
    catalog_data = get_fixture("valid_catalog.json")
    preview_data = get_fixture("valid_preview.json")
    
    # Change recent_performance to contract_supported only
    catalog_data["data_need_capabilities"][4]["support_status"] = "contract_supported"
    
    with pytest.raises(ValueError, match="Planned evidence recent_performance is not runtime executable"):
        validate_cross_contract(request_data, catalog_data, preview_data)
