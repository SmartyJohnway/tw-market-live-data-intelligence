import json
from pathlib import Path

from scripts.observation_contract import build_empty_bounded_watchlist_cross_context

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "docs/protocol/M7D_BOUNDED_WATCHLIST_CROSS_CONTEXT_POLICY.md"
INVENTORY = ROOT / "docs/data_capabilities/twse_mis_rich_field_inventory.json"

REQUIRED_IDS = {
    "bounded_observed_market_snapshot", "current_price_state", "session_position",
    "market_index_context", "futures_context", "watchlist_breadth",
    "cross_instrument_differences", "current_volume_observations",
    "displayed_order_book_depth_snapshot", "source_freshness_delay_failure",
    "missing_fields_context", "stale_observations_context", "official_eod_context",
    "recent_historical_context", "source_health_caveats", "data_provenance",
    "semantic_limitations", "frontend_operator_presentation", "ai_discussion_handoff",
}
REQUIRED_GROUPS = {
    "source_policy", "input_requirements", "coverage_catalog", "grouping_policy",
    "watchlist_observation_coverage", "bounded_breadth_summary",
    "bounded_relative_change_summary", "index_relative_context", "futures_relative_context",
    "etf_group_context", "source_freshness_summary", "missing_context_summary",
    "degraded_context_summary", "provenance_summary", "semantic_limitations",
    "quality_gate_policy", "blocked_interpretations", "future_builder_requirements",
}
BLOCKED = {
    "full_market_breadth", "market_wide_trend", "sector_rotation", "capital_flow",
    "main_force", "trading_signal", "buy_signal", "sell_signal", "recommendation",
    "buy_sell_hold", "target_price", "support", "resistance", "breakout", "breakdown",
    "true_liquidity", "full_order_book", "prediction", "confirmation",
}
POSITIVE_PHRASES = [
    "buy opportunity", "sell pressure", "support level", "resistance level",
    "target price estimate", "main force accumulation", "liquidity signal",
    "confirmed trend", "market breadth improved", "sector rotation confirmed",
    "capital inflow confirmed",
]


def _inventory():
    return json.loads(INVENTORY.read_text(encoding="utf-8"))


def _walk_keys(obj, prefix=()):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield prefix + (str(k),)
            yield from _walk_keys(v, prefix + (str(k),))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk_keys(v, prefix + (str(i),))


def test_m7d_policy_doc_exists_and_documents_dependencies_guardrails():
    assert POLICY.exists()
    text = POLICY.read_text(encoding="utf-8")
    for token in ["M7A pass_with_caveats", "M7B pass_with_caveats", "M7C pass_with_caveats"]:
        assert token in text
    assert "bounded watchlist only" in text
    for phrase in ["full market breadth", "sector rotation", "capital flow", "prediction", "signal", "recommendation"]:
        assert phrase in text
    for item_id in REQUIRED_IDS:
        assert item_id in text
    for status in ["in_scope_m7d", "referenced_dependency", "deferred_m7e", "deferred_m8", "deferred_m7f"]:
        assert status in text


def test_m7d_schema_top_level_and_required_groups():
    ctx = build_empty_bounded_watchlist_cross_context()
    assert ctx["schema_version"] == "m7d_bounded_watchlist_cross_context.v1"
    assert ctx["context_status"] == "schema_defined_not_computed"
    assert ctx["runtime_populated"] is False
    assert ctx["safe_for_ai_context"] is False
    assert ctx["bounded_watchlist_only"] is True
    assert ctx["not_full_market_breadth"] is True
    assert ctx["not_trading_signal"] is True
    assert ctx["not_recommendation"] is True
    assert REQUIRED_GROUPS <= set(ctx)


def test_m7d_coverage_catalog_has_19_required_items_and_keys():
    catalog = build_empty_bounded_watchlist_cross_context()["coverage_catalog"]
    assert len(catalog) == 19
    required_keys = {"id", "name", "scope_status", "description", "allowed_interpretation", "forbidden_interpretation", "depends_on", "m7d_schema_group"}
    assert {item["id"] for item in catalog} == REQUIRED_IDS
    assert {item["scope_status"] for item in catalog} >= {"in_scope_m7d", "referenced_dependency", "deferred_m7e", "deferred_m8", "deferred_m7f"}
    for item in catalog:
        assert required_keys <= set(item)
        assert isinstance(item["depends_on"], list)


def test_m7d_schema_bounded_summaries_and_context_requirements():
    ctx = build_empty_bounded_watchlist_cross_context()
    breadth = ctx["bounded_breadth_summary"]
    assert all(k.startswith("bounded_") or k in {"not_full_market_breadth", "status"} for k in breadth)
    assert breadth["not_full_market_breadth"] is True
    assert ctx["index_relative_context"]["bounded_watchlist_only"] is True
    assert ctx["index_relative_context"]["requires_index_item_in_watchlist"] is True
    assert ctx["futures_relative_context"]["bounded_watchlist_only"] is True
    assert ctx["futures_relative_context"]["requires_futures_item_in_watchlist"] is True
    assert ctx["etf_group_context"]["bounded_watchlist_only"] is True


def test_m7d_semantic_limitations_and_quality_gates():
    ctx = build_empty_bounded_watchlist_cross_context()
    limitations = ctx["semantic_limitations"]
    for key in [
        "not_full_market_breadth", "not_market_wide_trend", "not_sector_rotation",
        "not_capital_flow", "not_trading_signal", "not_recommendation",
        "not_support_resistance", "not_true_liquidity", "not_full_order_book",
    ]:
        assert limitations[key] is True
    assert set(ctx["blocked_interpretations"]) >= BLOCKED
    assert set(ctx["quality_gate_policy"]["context_status_values"]) >= {
        "schema_only", "not_computed", "computed", "blocked_missing_watchlist",
        "blocked_missing_latest_observation", "blocked_missing_m7c_metrics",
        "blocked_insufficient_observed_items", "blocked_quality_flags",
        "blocked_deferred_dependency",
    }


def test_m7d_schema_field_names_do_not_use_unbounded_positive_names():
    ctx = build_empty_bounded_watchlist_cross_context()
    forbidden = ["market_breadth", "sector_rotation", "capital_flow", "strength", "pressure", "support", "resistance", "breakout", "breakdown", "main_force"]
    allowed_prefixes = ("not_", "must_not_")
    allowed_containers = {"blocked_interpretations", "forbidden_interpretation", "semantic_limitations", "deferred_grouping_dimensions"}
    for path in _walk_keys(ctx):
        key = path[-1]
        if any(container in path for container in allowed_containers):
            continue
        if any(term in key for term in forbidden):
            assert key.startswith(allowed_prefixes), path
        if "signal" in key:
            assert key.startswith(allowed_prefixes), path


def test_m7d_inventory_registration():
    m7d = _inventory()["rich_observation_contract"]["m7d_bounded_watchlist_cross_context"]
    assert m7d["coverage_catalog_items"] == 19
    assert m7d["completed_tasks"] == ["M7D-00", "M7D-01", "M7D-02", "M7D-03", "M7D-04"]
    assert m7d["pure_builder_defined"] is True
    assert m7d["controlled_exposure_enabled"] is True
    assert m7d["runtime_exposure_enabled"] is True
    assert m7d["safe_for_ai_context"] is True
    assert m7d["builder_output_safe_for_ai_context"] is False
    assert m7d["next_task"] == "M7E-MARKET-CLOCK-AND-SESSION-STATE"
    assert m7d["runtime_populated"] is True
    assert m7d["bounded_watchlist_only"] is True
    assert m7d["not_full_market_breadth"] is True
    assert m7d["cross_context_is_signal"] is False


def test_m7d_no_forbidden_positive_language_in_new_artifacts():
    texts = [
        POLICY.read_text(encoding="utf-8").lower(),
        json.dumps(build_empty_bounded_watchlist_cross_context(), ensure_ascii=False).lower(),
        json.dumps(_inventory()["rich_observation_contract"]["m7d_bounded_watchlist_cross_context"], ensure_ascii=False).lower(),
    ]
    combined = "\n".join(texts)
    for phrase in POSITIVE_PHRASES:
        assert phrase not in combined
