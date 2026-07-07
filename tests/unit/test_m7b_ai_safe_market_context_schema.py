import json
from pathlib import Path

from scripts.observation_contract import (
    attach_empty_ai_safe_market_context_projection,
    build_empty_ai_safe_market_context_projection,
)

ROOT = Path(__file__).resolve().parents[2]
POLICY_DOC = ROOT / "docs/protocol/M7B_AI_SAFE_MARKET_CONTEXT_PROJECTION_POLICY.md"
INVENTORY_PATH = ROOT / "docs/data_capabilities/twse_mis_rich_field_inventory.json"

REQUIRED_GROUPS = {
    "source_policy",
    "instrument_context",
    "market_session_context",
    "price_snapshot_context",
    "reference_context",
    "index_market_context",
    "displayed_depth_context",
    "data_quality_context",
    "freshness_context",
    "caveat_context",
    "evidence_context",
    "blocked_interpretations",
    "future_builder_requirements",
}

BLOCKED_MEANINGS = {
    "buy_signal",
    "sell_signal",
    "hold",
    "recommendation",
    "target_price",
    "support_resistance",
    "main_force",
    "true_liquidity",
    "order_book_truth",
    "realtime_guarantee",
    "execution_feed",
    "official_api_definition",
    "verified_quantity_unit",
}


def test_policy_doc_exists_and_references_m7a_final_acceptance():
    assert POLICY_DOC.exists()
    text = POLICY_DOC.read_text(encoding="utf-8")
    assert "M7A_TWSE_MIS_RICH_FACTS_FINAL_ACCEPTANCE.md" in text
    assert "TWSE_MIS_RICH_OBSERVATION_CONTRACT.md" in text
    assert "twse_mis_rich_field_inventory.json" in text
    assert "M7A completed as pass_with_caveats" in text


def test_empty_projection_schema_top_level_and_required_groups():
    projection = build_empty_ai_safe_market_context_projection()
    assert projection["schema_version"] == "m7b_ai_safe_market_context_projection.v1"
    assert projection["projection_id"] == "TWSE_MIS_AI_SAFE_MARKET_CONTEXT"
    assert projection["source_family"] == "TWSE_MIS"
    assert projection["projection_status"] == "schema_defined_not_runtime_populated"
    assert projection["safe_for_ai_context"] is False
    assert projection["exposure_status"] == "projection_candidate_not_exposed"
    assert REQUIRED_GROUPS.issubset(projection)


def test_empty_projection_policy_caveats_and_depth_guardrails():
    projection = build_empty_ai_safe_market_context_projection()
    source_policy = projection["source_policy"]
    assert source_policy["official_api_field_dictionary_available"] is False
    assert source_policy["realtime_sla_verified"] is False
    assert source_policy["unit_verified_for_runtime_normalization"] is False

    depth = projection["displayed_depth_context"]
    assert depth["full_ladder_exposed"] is False
    assert depth["not_support_resistance"] is True
    assert depth["not_true_liquidity"] is True
    assert depth["not_full_order_book"] is True
    assert depth["not_trading_signal"] is True

    reference = projection["reference_context"]
    assert reference["pz_does_not_override_last_value"] is True
    assert reference["ps_does_not_override_current_volume"] is True


def test_blocked_interpretations_include_forbidden_meanings():
    projection = build_empty_ai_safe_market_context_projection()
    assert BLOCKED_MEANINGS.issubset(set(projection["blocked_interpretations"]))


def test_attach_helper_does_not_mutate_input_and_attaches_empty_projection_only():
    observation = {"symbol": "2330", "nested": {"preserve": True}}
    attached = attach_empty_ai_safe_market_context_projection(observation)
    assert "ai_safe_market_context_projection" not in observation
    assert attached is not observation
    assert attached["symbol"] == "2330"
    assert attached["nested"] == {"preserve": True}
    projection = attached["ai_safe_market_context_projection"]
    assert projection == build_empty_ai_safe_market_context_projection()
    assert projection["projection_status"] == "schema_defined_not_runtime_populated"


def test_attach_helper_is_not_called_by_runtime_code():
    helper_name = "attach_empty_ai_safe_market_context_projection"
    runtime_files = [
        ROOT / "server",
        ROOT / "scripts",
    ]
    references = []
    for base in runtime_files:
        for path in base.rglob("*.py"):
            if path.name == "observation_contract.py":
                continue
            text = path.read_text(encoding="utf-8")
            if helper_name in text:
                references.append(str(path.relative_to(ROOT)))
    assert references == []


def test_inventory_has_m7b_schema_only_registration():
    inv = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    m7b = inv["rich_observation_contract"]["m7b_ai_safe_market_context_projection"]
    assert m7b["runtime_populated"] is False
    assert m7b["safe_for_ai_context"] is False
    assert m7b["exposure_status"] == "projection_candidate_not_exposed"
    assert m7b["pure_builder_defined"] is True
    assert m7b["fixture_safety_tests_added"] is True
    assert m7b["runtime_exposure_enabled"] is False
    assert m7b["next_task"] == "M7B-04-M7B-05-CONTROLLED-EXPOSURE-INTEGRATION-AND-COMPATIBILITY-HARDENING"


def test_new_m7b_docs_and_metadata_avoid_positive_forbidden_language():
    inv = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    m7b_metadata = json.dumps(
        inv["rich_observation_contract"]["m7b_ai_safe_market_context_projection"],
        ensure_ascii=False,
    ).lower()
    policy_text = POLICY_DOC.read_text(encoding="utf-8").lower()
    combined = policy_text + "\n" + m7b_metadata
    positive_forbidden_phrases = [
        "buy opportunity",
        "sell pressure",
        "support level",
        "resistance level",
        "target price estimate",
        "main force accumulation",
        "liquidity signal",
        "confirmed trend",
        "realtime feed",
        "official api definition validated",
        "verified quantity unit available",
    ]
    for phrase in positive_forbidden_phrases:
        assert phrase not in combined
