import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INVENTORY_PATH = ROOT / "docs/data_capabilities/twse_mis_rich_field_inventory.json"


def load_inventory():
    return json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))


def test_twse_mis_rich_inventory_boundary_flags():
    inv = load_inventory()
    assert inv["schema_version"] == "m7a_twse_mis_rich_field_inventory.v1"
    assert inv["source_id"] == "TWSE_MIS"
    assert inv["runtime_behavior_changed"] is False
    assert inv["normalization_changed"] is False
    assert inv["full_market_scan"] is False
    assert inv["polling"] is False
    assert inv["scheduler"] is False
    assert inv["probe_executed"] is True
    assert inv["manual_probe_harness_added"] is True
    assert inv["probe_evidence_available"] is True
    assert inv["ci_network_required"] is False
    assert inv["last_successful_probe_summary_path"] == "research/probe_runs/m7a_twse_mis_rich_fields/m7a_twse_mis_rich_field_probe_summary_20260707T034516Z.json"
    harness = inv["manual_probe_harness"]
    assert harness["script"] == "scripts/probe_twse_mis_rich_fields.py"
    assert harness["execution_mode"] == "manual_explicit_only"
    assert harness["max_symbols_limit"] <= 10
    assert harness["writes_runtime_artifacts"] is False
    assert harness["writes_m5k_latest_observation"] is False
    assert harness["raw_payload_committed"] is False
    assert harness["ci_invoked"] is False


def test_twse_mis_required_fields_are_inventoried_and_not_discarded():
    inv = load_inventory()
    fields = {row["raw_field"]: row for row in inv["field_inventory"]}
    for required in ["z", "y", "o", "h", "l", "v", "tv", "b", "g", "a", "f", "u", "w", "d", "t", "tlong"]:
        assert required in fields

    assert fields["y"]["candidate_normalized_fact"] in {
        "price_facts.previous_close",
        "price_facts.previous_close_candidate",
    }
    assert fields["y"]["validation_status"] in {
        "partially_validated_from_existing_code",
        "requires_probe_validation",
        "requires_cross_source_validation",
    }

    assert fields["v"]["unit_status"] in {"unverified", "requires_validation"}
    assert fields["tv"]["unit_status"] in {"unverified", "requires_validation"}

    assert fields["b"]["candidate_normalized_fact"].startswith("displayed_depth_facts")
    assert fields["a"]["candidate_normalized_fact"].startswith("displayed_depth_facts")

    for row in inv["field_inventory"]:
        assert row["normalization_status"] != "discard"


def test_twse_mis_unknown_fields_are_preserved_raw_only():
    inv = load_inventory()
    fields = {row["raw_field"]: row for row in inv["field_inventory"]}
    unknown_fields = ["@", "ps", "pid", "pz", "bp", "m%", "^", "#", "mt", "i", "ip", "p", "s", "nf", "ts", "q", "r", "oa", "ob", "m", "nu"]
    for raw_field in unknown_fields:
        row = fields[raw_field]
        assert row["semantic_status"] == "unknown" or row["ai_exposure_status"] == "not_safe_yet"
        assert row["normalization_status"] == "preserve_raw_only" or row["ai_exposure_status"] == "not_safe_yet"


def test_twse_mis_forbidden_language_guardrails_are_explicit():
    inv = load_inventory()
    forbidden = set(inv["semantic_guardrails"]["forbidden_language"])
    for phrase in [
        "buy signal",
        "sell signal",
        "hold",
        "target price",
        "support/resistance",
        "main force",
        "主力",
        "買賣建議",
    ]:
        assert phrase in forbidden


def test_twse_mis_rich_observation_contract_registered_runtime_populated():
    inv = load_inventory()
    contract = inv["rich_observation_contract"]
    assert contract["schema_version"] == "m7a_twse_mis_rich_facts.v1"
    assert contract["schema_defined"] is True
    assert contract["runtime_populated"] is True
    assert contract["parser_populated"] is True
    assert contract["runtime_behavior_changed"] is True
    assert contract["normalization_changed"] is True
    assert contract["rich_facts_normalization_added"] is True
    assert contract["top_level_normalization_changed"] is False
    assert contract["top_level_observation_behavior_preserved"] is True
    assert contract["ai_exposure_safe_for_context"] is False
    assert contract["contract_doc"] == "docs/protocol/TWSE_MIS_RICH_OBSERVATION_CONTRACT.md"
    assert contract["contract_helper"] == "scripts/observation_contract.py::build_empty_twse_mis_rich_facts"
    assert contract["attach_helper"] == "scripts/observation_contract.py::attach_empty_twse_mis_rich_facts"
    assert contract["runtime_parser_helper"] == "scripts/observation_contract.py::build_twse_mis_rich_facts_from_row"
    assert contract["runtime_attach_helper"] == "scripts/observation_contract.py::attach_twse_mis_rich_facts_from_row"
    assert contract["completed_parser_task"] == "M7A-03-TWSE-MIS-RICH-FIELD-PARSER-EXTENSION"
    assert contract["completed_fixture_task"] == "M7A-04-FIXTURE-EXPANSION-AND-NORMALIZATION-TESTS"
    assert contract["next_compatibility_task"] == "completed_by_M7A-05-M7A-06"
    acceptance = contract["m7a_final_acceptance"]
    assert acceptance["status"] == "pass_with_caveats"
    assert acceptance["completed"] is True
    assert acceptance["downstream_compatibility_checked"] is True
    assert acceptance["fastapi_checked"] is True
    assert acceptance["mcp_checked"] is True
    assert acceptance["frontend_watchlist_checked"] is True
    assert acceptance["conversation_context_checked"] is True
    assert acceptance["source_health_checked"] is True
    assert acceptance["non_twse_mis_checked"] is True
    assert acceptance["ai_exposure_safe_for_context"] is False
    assert acceptance["live_probe_executed_in_m7a_05_06"] is False
    assert acceptance["new_probe_output_committed_in_m7a_05_06"] is False


def test_m7b_ai_safe_market_context_projection_registered_schema_only():
    inv = load_inventory()
    m7b = inv["rich_observation_contract"]["m7b_ai_safe_market_context_projection"]
    assert m7b["schema_version"] == "m7b_ai_safe_market_context_projection.v1"
    assert m7b["status"] == "schema_defined_policy_defined_not_runtime_populated"
    assert m7b["m7a_dependency_status"] == "pass_with_caveats"
    assert m7b["policy_doc"] == "docs/protocol/M7B_AI_SAFE_MARKET_CONTEXT_PROJECTION_POLICY.md"
    assert m7b["schema_helper"] == "scripts/observation_contract.py::build_empty_ai_safe_market_context_projection"
    assert m7b["attach_helper"] == "scripts/observation_contract.py::attach_empty_ai_safe_market_context_projection"
    assert m7b["runtime_populated"] is False
    assert m7b["runtime_behavior_changed"] is False
    assert m7b["fastapi_changed"] is False
    assert m7b["mcp_changed"] is False
    assert m7b["frontend_changed"] is False
    assert m7b["conversation_context_changed"] is False
    assert m7b["safe_for_ai_context"] is False
    assert m7b["exposure_status"] == "projection_candidate_not_exposed"
    assert m7b["completed_tasks"] == ["M7B-00", "M7B-01"]
    assert m7b["next_task"] == "M7B-02-M7B-03-PURE-PROJECTION-BUILDER-AND-SAFETY-TESTS"
