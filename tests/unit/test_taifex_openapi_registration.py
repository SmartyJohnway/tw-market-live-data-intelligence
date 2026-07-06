import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_json(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_taifex_openapi_endpoint_inventory_schema_and_guardrails():
    inv = load_json("docs/data_capabilities/taifex_openapi_endpoint_inventory.json")
    assert inv["schema_version"] == "m7_01_taifex_openapi_endpoint_inventory.v1"
    assert inv["source_id"] == "TAIFEX_OpenAPI"
    assert inv["runtime_integrated"] is False
    assert inv["live_observation_enabled"] is False
    assert inv["network_calls_in_runtime"] is False
    assert "TAIFEX_MIS" in inv["distinct_from_source_ids"]
    assert inv["overall_classification"]["authority_class"] == "official_openapi"
    assert inv["overall_classification"]["timing_class"] != "live_or_intraday"
    forbidden = set(inv["semantic_guardrails"]["forbidden_language"])
    assert {"buy signal", "sell signal", "hold", "target price"} <= forbidden
    assert len(inv["endpoint_categories"]) >= 9
    assert len(inv["endpoints"]) >= 10
    assert all(endpoint["source_id"] == "TAIFEX_OpenAPI" for endpoint in inv["endpoints"])
    assert all(endpoint["runtime_candidate"] is False for endpoint in inv["endpoints"])


def test_taifex_openapi_separate_source_family_in_generated_inventory():
    data = load_json("docs/data_capabilities/validated_endpoint_data_capability_inventory.json")
    families = {source["source_id"]: source for source in data["source_families"]}
    assert "TAIFEX_OpenAPI" in families
    assert "TAIFEX_MIS" in families
    assert families["TAIFEX_OpenAPI"] is not families["TAIFEX_MIS"]
    assert families["TAIFEX_OpenAPI"]["authority_class"] == "official_openapi"
    assert families["TAIFEX_OpenAPI"]["runtime_integrated"] is False
    assert families["TAIFEX_MIS"]["runtime_integrated"] is True
    assert families["TAIFEX_OpenAPI"]["timing_class"] != "live_or_intraday"
    assert "TAIFEX_OpenAPI" in data["source_taxonomy_summary"]["official_eod_contract_sources"]
    assert "TAIFEX_MIS" in data["source_taxonomy_summary"]["external_runtime_sources"]


def test_taifex_openapi_source_authority_registry_entry():
    registry = load_json("docs/source_registry/source_authority_registry.json")
    sources = {source["source_id"]: source for source in registry["sources"]}
    assert "TAIFEX_OpenAPI" in sources
    source = sources["TAIFEX_OpenAPI"]
    assert source["source_family"] == "official_exchange"
    assert source["production_current_state_allowed"] is False
    assert "live_observation" in source["forbidden_roles"]
    assert "trading_signal" in source["forbidden_roles"]
