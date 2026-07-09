import json
from pathlib import Path

CATALOG = Path("docs/data_capabilities/rich_fact_display_catalog.json")
INVENTORY = Path("docs/data_capabilities/twse_mis_rich_field_inventory.json")


def _catalog():
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def _fields_by_key():
    return {field["field_key"]: field for field in _catalog()["fields"]}


def test_m7f_catalog_schema_sanity():
    catalog = _catalog()
    assert catalog["schema_version"] == "m7f_rich_fact_display_catalog.v1"
    assert catalog["not_summary_only"] is True
    assert catalog["display_policy"]["display_project_validated_fields"] is True
    assert catalog["display_policy"]["official_per_field_validation_required"] is False
    assert catalog["display_policy"]["prefer_labeling_over_suppression"] is True
    assert catalog["display_policy"]["raw_payload_exposure_allowed"] is False
    assert catalog["display_policy"]["trading_advice_allowed"] is False
    assert catalog["next_task"] == "M7F-02-FRONTEND-RICH-FACT-BROWSER-BASE-UI"


def test_m7f_catalog_field_keys_are_unique():
    keys = [field["field_key"] for field in _catalog()["fields"]]
    assert len(keys) == len(set(keys))


def test_m7f_catalog_required_groups_exist():
    groups = set(_catalog()["field_groups"])
    assert {
        "identity", "source", "timestamp", "price_quote", "price_change",
        "volume_trading", "rich_observation", "deterministic_metrics",
        "bounded_watchlist_context", "market_clock_currentness",
        "trading_calendar_authority", "source_health", "caveats_governance",
        "raw_forbidden",
    } <= groups


def test_m7f_catalog_required_representative_fields_exist():
    fields = set(_fields_by_key())
    assert {
        "symbol", "display_name", "market", "source", "retrieved_at_utc",
        "generated_at_utc", "price_like_value", "previous_close_candidate",
        "open_candidate", "high_candidate", "low_candidate", "change_percent",
        "volume_candidate", "session_state", "freshness_state", "currentness_label",
        "calendar_confidence", "trading_day_status", "not_trading_signal",
        "not_recommendation", "raw_payload", "twse_mis_rich_facts",
        "raw_unknown_facts", "full_ladder", "bid_prices", "ask_prices",
        "source_investigation_notes",
    } <= fields


def test_m7f_raw_forbidden_enforcement():
    fields = _fields_by_key()
    for key in _catalog()["raw_forbidden_fields"]:
        field = fields[key]
        assert field["display_allowed"] is False
        assert field["ai_handoff_allowed"] is False
        assert field["raw_forbidden"] is True
        assert field["exposure_class"] == "raw_forbidden"
        assert field["confidence_level"] == "raw_forbidden"


def test_m7f_ai_handoff_requires_display_and_not_raw():
    for field in _catalog()["fields"]:
        if field["ai_handoff_allowed"] is True:
            assert field["display_allowed"] is True
            assert field["raw_forbidden"] is False


def test_m7f_catalog_avoids_over_conservatism():
    fields = _catalog()["fields"]
    assert any(f["confidence_level"] == "project_validated" and f["display_allowed"] for f in fields)
    assert any(
        f["confidence_level"] in {"source_observed", "semantic_inferred"}
        and f["display_allowed"]
        for f in fields
    )


def test_m7f_currentness_and_calendar_dependencies():
    fields = _fields_by_key()
    assert fields["currentness_label"]["currentness_dependent"] is True
    assert fields["freshness_state"]["currentness_dependent"] is True
    assert fields["calendar_confidence"]["calendar_dependent"] is True
    assert fields["trading_day_status"]["calendar_dependent"] is True


def test_m7f_inventory_status_entry():
    inv = json.loads(INVENTORY.read_text(encoding="utf-8"))
    entry = inv["rich_observation_contract"]["m7f_rich_fact_browser_operator_workbench"]
    assert entry["status"] == "policy_exposure_contract_and_field_catalog_defined"
    assert entry["completed_tasks"] == ["M7F-00", "M7F-01"]
    assert entry["track_name"] == "M7F-FRONTEND-RICH-FACT-BROWSER-OPERATOR-WORKBENCH-AND-AI-DISCUSSION-HANDOFF"
    assert entry["not_summary_only"] is True
    assert entry["raw_payload_exposure_allowed"] is False
    assert entry["project_validated_fields_displayable"] is True
    assert entry["official_per_field_validation_required"] is False
    assert entry["field_level_provenance_required"] is True
    assert entry["field_level_confidence_required"] is True
    assert entry["field_level_caveats_required"] is True
    assert entry["trading_advice_allowed"] is False
    assert entry["next_task"] == "M7F-02-FRONTEND-RICH-FACT-BROWSER-BASE-UI"
