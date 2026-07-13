import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs" / "protocol"
REGISTRY_PATH = ROOT / "docs" / "data_capabilities" / "m8_source_capability_registry.json"
INVENTORY_PATH = ROOT / "docs" / "data_capabilities" / "twse_mis_rich_field_inventory.json"
PROFILE_PATH = ROOT / "config" / "test_execution_profiles.json"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def source_by_id(registry, source_id):
    return next(source for source in registry["sources"] if source["source_id"] == source_id)


def flattened_text(value):
    return json.dumps(value, ensure_ascii=False)


def test_governance_docs_exist_and_contain_expected_status_strings():
    docs = [
        DOCS / "M8_SOURCE_TIMING_AUTHORITY_GOVERNANCE_PREFLIGHT.md",
        DOCS / "M8_SOURCE_CAPABILITY_REGISTRY_SCHEMA.md",
        DOCS / "M8_FRESHNESS_TIMESTAMP_DELAY_SEMANTICS.md",
        DOCS / "M8_MULTI_SOURCE_MARKET_CONTEXT_SCHEMA.md",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in docs)
    for path in docs:
        assert path.exists(), path
    for phrase in [
        "m8_00_governance_foundation_defined",
        "m8_source_capability_registry.v1",
        "m8_freshness_timestamp_delay_semantics.v1_defined",
        "m8_00_multi_source_market_context.v1",
        "no TPEX_MIS",
        "no rotc_",
        "no trading advice",
        "EOD must not be realtime",
        "retrieved_at_utc is not exchange timestamp",
    ]:
        assert phrase in combined


def test_registry_json_shape_and_required_source_ids():
    registry = load_json(REGISTRY_PATH)
    assert registry["schema_version"] == "m8_source_capability_registry.v1"
    assert registry["status"] in {"m8_00_governance_foundation_defined", "m8_through_m8b_implemented_with_caveats", "m8c_01_taifex_mis_bounded_snapshot_runtime_pass_with_caveats", "m8_through_m8c_consolidated_acceptance_pass_with_caveats"}
    source_ids = {source["source_id"] for source in registry["sources"]}
    assert {
        "TWSE_MIS",
        "TAIFEX_MIS",
        "TWSE_OPENAPI",
        "TPEX_OPENAPI",
        "TAIFEX_OPENAPI",
        "MOPS",
        "MANUAL_OPERATOR_EVIDENCE",
        "EXTERNAL_VALIDATION_ONLY",
        "CREDENTIAL_GATED_PROVIDER",
    }.issubset(source_ids)


def test_twse_mis_route_semantics():
    registry = load_json(REGISTRY_PATH)
    twse_mis = source_by_id(registry, "TWSE_MIS")
    assert twse_mis["market_scope"]["listed"]["route"] == "tse_{symbol}.tw"
    assert twse_mis["market_scope"]["tpex_otc"]["route"] == "otc_{symbol}.tw"
    assert all(source["source_id"] != "TPEX_MIS" for source in registry["sources"])
    route_text = flattened_text([source.get("market_scope", {}) for source in registry["sources"]])
    assert "rotc_" not in route_text
    assert registry["global_ai_interpretation_policy"]["no_emerging_stock_live_route"] is True
    assert twse_mis["market_scope"]["emerging_stock_live_supported"] is False


def test_official_eod_source_semantics():
    registry = load_json(REGISTRY_PATH)
    twse = source_by_id(registry, "TWSE_OPENAPI")
    tpex = source_by_id(registry, "TPEX_OPENAPI")
    taifex = source_by_id(registry, "TAIFEX_OPENAPI")
    assert twse["timing_class"] == "official_eod"
    assert tpex["timing_class"] == "official_eod"
    assert taifex["timing_class"] in {"official_statistics_eod", "official_eod"}
    assert twse["runtime_executable"] is True
    assert tpex["runtime_executable"] is True
    assert taifex["runtime_executable"] is True
    for source in [twse, tpex, taifex]:
        assert source["ai_exposure_level"] != "safe_context_allowed"
        blocked = " ".join(source["blocked_interpretation"])
        assert "not realtime" in blocked
        assert "not current price" in blocked or source["source_id"] == "TAIFEX_OPENAPI"


def test_manual_validation_only_and_credential_gated_semantics():
    registry = load_json(REGISTRY_PATH)
    manual = source_by_id(registry, "MANUAL_OPERATOR_EVIDENCE")
    validation = source_by_id(registry, "EXTERNAL_VALIDATION_ONLY")
    credential = source_by_id(registry, "CREDENTIAL_GATED_PROVIDER")
    assert manual["authority_level"] == "manual_operator_evidence"
    assert "not official source" in manual["blocked_interpretation"]
    assert validation["authority_level"] == "external_validation_only"
    assert "cannot be promoted to primary source" in validation["blocked_interpretation"]
    assert credential["credential_required"] is True
    assert "not runtime dependency" in credential["blocked_interpretation"]


def test_inventory_m8_entry():
    inventory = load_json(INVENTORY_PATH)
    entry = inventory["rich_observation_contract"]["milestone_snapshots"]["state_at_m8_00_acceptance"]
    assert entry["status"] in {"m8_00_source_freshness_evaluator_defined", "m8_00_multi_source_context_builder_defined", "m8_00_controlled_conversation_context_integration_and_compatibility_hardening_defined", "m8_00_final_acceptance_pass_with_caveats"}
    assert entry["completed_tasks"][:5] == ["M8-00-00", "M8-00-01", "M8-00-02", "M8-00-03", "M8-00-04"]
    for key in [
        "governance_preflight_doc",
        "source_capability_registry_schema_doc",
        "source_capability_registry",
        "freshness_timestamp_delay_semantics_doc",
        "multi_source_market_context_schema_doc",
    ]:
        assert (ROOT / entry[key]).exists()
    for key in [
        "runtime_behavior_changed",
        "frontend_changed",
        "server_changed",
        "network_fetch_added",
        "adapter_added",
        "conversation_context_integration_added",
        "tpex_mis_introduced",
        "rotc_route_introduced",
        "trading_advice_allowed",
    ]:
        assert entry[key] is False
    assert entry["freshness_evaluator_added"] is True
    assert entry["freshness_evaluator_is_pure_helper"] is True
    assert entry["freshness_evaluator_runtime_integration_added"] is False
    assert entry["source_freshness_assessment_schema_version"] == "m8_source_freshness_assessment.v1"
    assert entry["next_task"] in {"M8-00-05-MULTI-SOURCE-CONTEXT-BUILDER", "M8-00-06-CONTROLLED-CONVERSATION-CONTEXT-INTEGRATION", "M8-00-08-FINAL-ACCEPTANCE-AND-CLOSURE", "M8A-00-OFFICIAL-EOD-ADAPTER-SCOPE-AND-CONTRACT-PREFLIGHT"}


def test_default_ci_includes_m8_governance_test():
    profile = load_json(PROFILE_PATH)
    assert (
        "tests/unit/test_m8_source_governance_foundation.py"
        in profile["profiles"]["default-ci"]["pytest_paths"]
    )
