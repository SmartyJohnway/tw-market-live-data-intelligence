import json
from pathlib import Path

from scripts.observation_contract import build_empty_deterministic_metrics_context

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "docs/protocol/M7C_DETERMINISTIC_METRICS_POLICY.md"
INVENTORY_PATH = ROOT / "docs/data_capabilities/twse_mis_rich_field_inventory.json"

REQUIRED_GROUPS = {
    "source_policy",
    "input_requirements",
    "quality_gate_policy",
    "price_change_metrics",
    "intraday_range_metrics",
    "open_high_low_position_metrics",
    "displayed_quote_spread_metrics",
    "displayed_depth_balance_metrics",
    "metric_availability",
    "caveat_context",
    "blocked_interpretations",
    "future_builder_requirements",
}

REQUIRED_METRICS = {
    "change",
    "change_percent",
    "intraday_range",
    "position_in_day_range",
    "distance_from_high_percent",
    "distance_from_low_percent",
    "change_from_open_percent",
    "displayed_spread",
    "displayed_spread_percent",
    "top5_displayed_bid_volume",
    "top5_displayed_ask_volume",
    "displayed_bid_ask_depth_ratio",
}

FORBIDDEN_METRIC_NAME_PARTS = {
    "signal",
    "strength",
    "pressure",
    "support",
    "resistance",
    "breakout",
    "breakdown",
    "main_force",
    "liquidity_signal",
}

FORBIDDEN_POSITIVE_PHRASES = {
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
}


def _metric_entries(ctx):
    for group_name in [
        "price_change_metrics",
        "intraday_range_metrics",
        "open_high_low_position_metrics",
        "displayed_quote_spread_metrics",
        "displayed_depth_balance_metrics",
    ]:
        yield from ctx[group_name].items()


def test_m7c_policy_doc_exists_and_references_m7b_acceptance():
    assert POLICY_PATH.exists()
    text = POLICY_PATH.read_text(encoding="utf-8")
    assert "M7B final acceptance" in text
    assert "pass_with_caveats" in text
    assert "docs/protocol/M7B_AI_SAFE_MARKET_CONTEXT_FINAL_ACCEPTANCE.md" in text


def test_m7c_policy_doc_excludes_source_freshness_governance():
    text = POLICY_PATH.read_text(encoding="utf-8")
    assert "deterministic metrics" in text
    assert "not multi-source/source-freshness governance" in text
    assert "not a trading-signal layer" in text
    assert "not a recommendation layer" in text


def test_empty_m7c_schema_top_level_flags():
    ctx = build_empty_deterministic_metrics_context()
    assert ctx["schema_version"] == "m7c_deterministic_metrics.v1"
    assert ctx["metric_status"] == "schema_defined_not_computed"
    assert ctx["runtime_populated"] is False
    assert ctx["safe_for_ai_context"] is False
    assert ctx["not_trading_signal"] is True
    assert ctx["not_recommendation"] is True


def test_empty_m7c_schema_required_groups_and_metrics():
    ctx = build_empty_deterministic_metrics_context()
    assert REQUIRED_GROUPS <= set(ctx)
    metric_names = {name for name, _entry in _metric_entries(ctx)}
    assert REQUIRED_METRICS <= metric_names


def test_m7c_metric_names_avoid_forbidden_terms():
    ctx = build_empty_deterministic_metrics_context()
    for name, _entry in _metric_entries(ctx):
        for forbidden in FORBIDDEN_METRIC_NAME_PARTS:
            assert forbidden not in name


def test_m7c_displayed_depth_metrics_have_required_caveats():
    ctx = build_empty_deterministic_metrics_context()
    for entry in ctx["displayed_depth_balance_metrics"].values():
        assert entry["displayed_depth_snapshot_only"] is True
        assert entry["not_true_liquidity"] is True
        assert entry["not_full_order_book"] is True
        assert entry["not_support_resistance"] is True
        assert entry["not_signal"] is True


def test_m7c_displayed_spread_metrics_have_required_caveats():
    ctx = build_empty_deterministic_metrics_context()
    for entry in ctx["displayed_quote_spread_metrics"].values():
        assert entry["not_true_liquidity"] is True
        assert entry["not_full_order_book"] is True
        assert entry["not_signal"] is True


def test_m7c_quality_gate_status_values_exist():
    ctx = build_empty_deterministic_metrics_context()
    values = set(ctx["quality_gate_policy"]["metric_status_values"])
    assert {
        "schema_only",
        "not_computed",
        "computed",
        "blocked_missing_required_fields",
        "blocked_quality_flags",
        "blocked_zero_denominator",
        "blocked_non_numeric",
    } <= values


def test_m7c_inventory_registration_exists_and_preserves_disabled_runtime_flags():
    inv = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    m7c = inv["rich_observation_contract"]["m7c_deterministic_metrics"]
    assert m7c["schema_version"] == "m7c_deterministic_metrics.v1"
    assert m7c["runtime_populated"] is False
    assert m7c["safe_for_ai_context"] is False
    assert m7c["metrics_are_signals"] is False
    assert m7c["next_task"] == "M7C-04-CONTROLLED-INTEGRATION-COMPATIBILITY-AND-CLOSURE"
    assert m7c["pure_builder_defined"] is True
    assert m7c["fixture_safety_tests_added"] is True
    assert m7c["builder_output_metric_status"] == "runtime_computed_candidate"


def test_m7c_artifacts_do_not_use_forbidden_positive_language():
    ctx = build_empty_deterministic_metrics_context()
    inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))["rich_observation_contract"]["m7c_deterministic_metrics"]
    combined = "\n".join([
        POLICY_PATH.read_text(encoding="utf-8"),
        json.dumps(ctx, ensure_ascii=False),
        json.dumps(inventory, ensure_ascii=False),
    ]).lower()
    for phrase in FORBIDDEN_POSITIVE_PHRASES:
        assert phrase not in combined


def test_m7c_displayed_depth_inputs_are_sanitized_top5_and_raw_ladders_forbidden():
    ctx = build_empty_deterministic_metrics_context()
    required = ctx["input_requirements"]["displayed_depth_balance_required_fields"]
    assert required == ["sanitized_top5_bid_quantities", "sanitized_top5_ask_quantities"]
    for entry in ctx["displayed_depth_balance_metrics"].values():
        assert "sanitized_top5_bid_quantities" in entry["required_fields"] or "sanitized_top5_ask_quantities" in entry["required_fields"]
        assert "bid_quantities" not in entry["required_fields"]
        assert "ask_quantities" not in entry["required_fields"]
    text = POLICY_PATH.read_text(encoding="utf-8")
    assert "sanitized top-5" in text.lower()
    assert "must not expose raw" in text.lower()
    assert "full ladder arrays" in text.lower()
