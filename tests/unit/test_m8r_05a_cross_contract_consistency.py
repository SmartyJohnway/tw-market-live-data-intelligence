import pytest
from scripts.validate_unified_market_evidence_contracts import validate_cross_contract

def test_cross_contract_valid():
    catalog = {
        "data_need_capabilities": [{"capability_id": "current_observation"}],
        "bounds": {"hard_operation_limit": 100},
        "fallback_semantics": {"fallback_must_be_explicit": True}
    }
    request = {
        "data_needs": [{"type": "current_observation"}]
    }
    preview = {
        "planned_evidence": ["current_observation"],
        "bounds": {"operation_count": 5}
    }
    result = {
        "targets": [
            {
                "evidence": {
                    "current_observation": {}
                }
            }
        ]
    }
    assert validate_cross_contract(request, catalog, preview, result) is True

def test_cross_contract_invalid_request_need():
    catalog = {
        "data_need_capabilities": [{"capability_id": "current_observation"}]
    }
    request = {
        "data_needs": [{"type": "unknown_need"}]
    }
    with pytest.raises(ValueError, match="not found in catalog"):
        validate_cross_contract(request, catalog, None, None)

def test_cross_contract_preview_exceeds_request():
    catalog = {
        "data_need_capabilities": [{"capability_id": "current_observation"}, {"capability_id": "official_eod_reference"}]
    }
    request = {
        "data_needs": [{"type": "current_observation"}]
    }
    preview = {
        "planned_evidence": ["current_observation", "official_eod_reference"]
    }
    with pytest.raises(ValueError, match="exceeds requested data needs"):
        validate_cross_contract(request, catalog, preview, None)

def test_cross_contract_bounds_exceeded():
    catalog = {
        "data_need_capabilities": [{"capability_id": "current_observation"}],
        "bounds": {"hard_operation_limit": 10}
    }
    request = {
        "data_needs": [{"type": "current_observation"}]
    }
    preview = {
        "planned_evidence": ["current_observation"],
        "bounds": {"operation_count": 15}
    }
    with pytest.raises(ValueError, match="exceed catalog hard limit"):
        validate_cross_contract(request, catalog, preview, None)

def test_cross_contract_fallback_without_explicit_flag():
    catalog = {
        "data_need_capabilities": [{"capability_id": "official_eod_reference"}],
        "fallback_semantics": {"fallback_must_be_explicit": False}
    }
    request = {
        "data_needs": [{"type": "official_eod_reference"}]
    }
    result = {
        "targets": [
            {
                "evidence": {
                    "official_eod_reference": {
                        "fallback_policy_used": True
                    }
                }
            }
        ]
    }
    with pytest.raises(ValueError, match="not explicit in catalog"):
        validate_cross_contract(request, catalog, None, result)
