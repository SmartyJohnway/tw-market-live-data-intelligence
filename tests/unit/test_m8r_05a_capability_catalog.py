import json
import pytest
from pathlib import Path
from jsonschema import validate, ValidationError

SCHEMA_PATH = Path(__file__).parent.parent.parent / "schemas" / "unified_market_evidence_capability_catalog.v1.schema.json"
CATALOG_PATH = Path(__file__).parent.parent.parent / "docs" / "data_capabilities" / "unified_market_evidence_capability_catalog.v1.json"

@pytest.fixture(scope="module")
def catalog_schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture(scope="module")
def capability_catalog():
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def test_capability_catalog_is_valid_against_schema(capability_catalog, catalog_schema):
    validate(instance=capability_catalog, schema=catalog_schema)

def test_catalog_market_support_maturity(capability_catalog):
    markets = capability_catalog.get("supported_markets", {})
    assert markets.get("TWSE", {}).get("support_level") == "supported"
    assert markets.get("TPEX", {}).get("support_level") == "supported_with_caveats"
    assert markets.get("TAIFEX", {}).get("support_level") == "provisional"

def test_catalog_current_activation_profile(capability_catalog):
    execution = capability_catalog.get("execution", {})
    assert execution.get("preview_supported") is True
    assert execution.get("explicit_approval_required") is True
    assert execution.get("one_shot_execution") is True
    assert execution.get("scheduler_enabled") is False
    assert execution.get("polling_enabled") is False
    assert execution.get("persistent_watchlist_mutation") is False
    assert execution.get("trading_enabled") is False

def test_catalog_bounds(capability_catalog):
    bounds = capability_catalog.get("bounds", {})
    assert bounds.get("default_target_limit") == 10
    assert bounds.get("hard_target_limit") == 50
    assert bounds.get("default_operation_limit") == 30
    assert bounds.get("hard_operation_limit") == 100

def test_catalog_fallback_semantics(capability_catalog):
    fallbacks = capability_catalog.get("fallback_semantics", {})
    assert fallbacks.get("fallback_must_be_explicit") is True
    assert fallbacks.get("fallback_timing_class_downgrade_allowed") is True

def test_catalog_known_limitations_exist(capability_catalog):
    limitations = capability_catalog.get("known_limitations", [])
    assert "not every requested evidence need is runtime-executable yet" in limitations
    assert "target name resolution implementation belongs to M8R-06" in limitations
    assert "Unified orchestrator is not implemented in M8R-05A" in limitations
