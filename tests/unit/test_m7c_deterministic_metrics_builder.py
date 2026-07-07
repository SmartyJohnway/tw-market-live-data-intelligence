import json
from copy import deepcopy
from pathlib import Path

import pytest

from scripts.observation_contract import (
    attach_deterministic_metrics_context_from_observation,
    build_deterministic_metrics_context_from_observation,
)


def _obs(**overrides):
    observation = {
        "reference_only": False,
        "data_quality_flags": [],
        "source_risk_flags": [],
        "twse_mis_rich_facts": {
            "price_facts": {
                "last_value": 100,
                "previous_close": 95,
                "open": 98,
                "high": 105,
                "low": 90,
            },
            "displayed_depth_facts": {
                "best_bid": 99,
                "best_ask": 100,
                "sanitized_top5_bid_quantities": [10, 20, 30, 40, 50],
                "sanitized_top5_ask_quantities": [15, 25, 35, 45, 55],
                "bid_quantities_raw": [999],
                "ask_quantities_raw": [999],
                "bid_prices": [98, 97],
                "ask_prices": [101, 102],
            },
            "quality_facts": {
                "malformed_fields": [],
                "placeholder_fields": [],
                "ladder_mismatch_flags": [],
            },
            "raw_unknown_facts": {"raw_pid": "x"},
        },
    }
    for path, value in overrides.items():
        cursor = observation
        parts = path.split("__")
        for part in parts[:-1]:
            cursor = cursor[part]
        if value == "__DELETE__":
            del cursor[parts[-1]]
        else:
            cursor[parts[-1]] = value
    return observation


def _entry(ctx, group, name):
    return ctx[group][name]


def test_valid_regular_security_row_computes_price_and_spread_metrics():
    ctx = build_deterministic_metrics_context_from_observation(_obs())
    assert ctx["metric_status"] == "runtime_computed_candidate"
    assert ctx["runtime_populated"] is True
    assert ctx["safe_for_ai_context"] is False
    assert ctx["not_trading_signal"] is True
    assert ctx["not_recommendation"] is True
    assert _entry(ctx, "price_change_metrics", "change")["value"] == 5
    assert _entry(ctx, "price_change_metrics", "change_percent")["value"] == pytest.approx(5 / 95)
    assert _entry(ctx, "intraday_range_metrics", "intraday_range")["value"] == 15
    assert _entry(ctx, "open_high_low_position_metrics", "position_in_day_range")["value"] == pytest.approx(10 / 15)
    assert _entry(ctx, "open_high_low_position_metrics", "distance_from_high_percent")["value"] == pytest.approx(-5 / 105)
    assert _entry(ctx, "open_high_low_position_metrics", "distance_from_low_percent")["value"] == pytest.approx(10 / 90)
    assert _entry(ctx, "open_high_low_position_metrics", "change_from_open_percent")["value"] == pytest.approx(2 / 98)
    assert _entry(ctx, "displayed_quote_spread_metrics", "displayed_spread")["value"] == 1
    assert _entry(ctx, "displayed_quote_spread_metrics", "displayed_spread_percent")["value"] == pytest.approx(1 / 99.5)


def test_valid_displayed_depth_quantities_compute_sanitized_snapshot_metrics_only():
    ctx = build_deterministic_metrics_context_from_observation(_obs())
    assert _entry(ctx, "displayed_depth_balance_metrics", "top5_displayed_bid_volume")["value"] == 150
    assert _entry(ctx, "displayed_depth_balance_metrics", "top5_displayed_ask_volume")["value"] == 175
    assert _entry(ctx, "displayed_depth_balance_metrics", "displayed_bid_ask_depth_ratio")["value"] == pytest.approx(150 / 175)
    serialized = json.dumps(ctx, ensure_ascii=False)
    for raw_key in ["twse_mis_rich_facts", "bid_prices", "ask_prices", "bid_quantities_raw", "ask_quantities_raw", "raw_unknown_facts"]:
        assert raw_key not in serialized


def test_missing_required_price_fields_block_affected_metrics():
    ctx = build_deterministic_metrics_context_from_observation(_obs(twse_mis_rich_facts__price_facts__last_value="__DELETE__"))
    assert _entry(ctx, "price_change_metrics", "change")["status"] == "blocked_missing_required_fields"
    assert _entry(ctx, "open_high_low_position_metrics", "position_in_day_range")["status"] == "blocked_missing_required_fields"
    assert _entry(ctx, "intraday_range_metrics", "intraday_range")["status"] == "computed"


def test_non_numeric_fields_block_affected_metrics():
    ctx = build_deterministic_metrics_context_from_observation(_obs(twse_mis_rich_facts__price_facts__previous_close="-"))
    assert _entry(ctx, "price_change_metrics", "change")["status"] == "blocked_non_numeric"
    assert _entry(ctx, "price_change_metrics", "change_percent")["status"] == "blocked_non_numeric"


def test_zero_denominators_are_blocked_per_metric():
    ctx = build_deterministic_metrics_context_from_observation(
        _obs(
            twse_mis_rich_facts__price_facts__previous_close=0,
            twse_mis_rich_facts__price_facts__high=0,
            twse_mis_rich_facts__price_facts__low=0,
            twse_mis_rich_facts__price_facts__open=0,
            twse_mis_rich_facts__displayed_depth_facts__best_bid=-1,
            twse_mis_rich_facts__displayed_depth_facts__best_ask=1,
            twse_mis_rich_facts__displayed_depth_facts__sanitized_top5_ask_quantities=[0, 0, 0, 0, 0],
        )
    )
    assert _entry(ctx, "price_change_metrics", "change_percent")["status"] == "blocked_zero_denominator"
    assert _entry(ctx, "open_high_low_position_metrics", "position_in_day_range")["status"] == "blocked_zero_denominator"
    assert _entry(ctx, "open_high_low_position_metrics", "distance_from_high_percent")["status"] == "blocked_zero_denominator"
    assert _entry(ctx, "open_high_low_position_metrics", "distance_from_low_percent")["status"] == "blocked_zero_denominator"
    assert _entry(ctx, "open_high_low_position_metrics", "change_from_open_percent")["status"] == "blocked_zero_denominator"
    assert _entry(ctx, "displayed_quote_spread_metrics", "displayed_spread_percent")["status"] == "blocked_zero_denominator"
    assert _entry(ctx, "displayed_depth_balance_metrics", "displayed_bid_ask_depth_ratio")["status"] == "blocked_zero_denominator"


def test_reference_only_blocks_last_value_dependent_metrics_but_not_valid_intraday_range():
    ctx = build_deterministic_metrics_context_from_observation(_obs(reference_only=True))
    for group, name in [
        ("price_change_metrics", "change"),
        ("price_change_metrics", "change_percent"),
        ("open_high_low_position_metrics", "position_in_day_range"),
        ("open_high_low_position_metrics", "distance_from_high_percent"),
        ("open_high_low_position_metrics", "distance_from_low_percent"),
        ("open_high_low_position_metrics", "change_from_open_percent"),
    ]:
        assert _entry(ctx, group, name)["status"] == "blocked_quality_flags"
        assert _entry(ctx, group, name)["blocked_reason"] == "reference_only_blocks_last_value_metrics"
    assert _entry(ctx, "intraday_range_metrics", "intraday_range")["status"] == "computed"


def test_malformed_required_fields_block_affected_metrics():
    ctx = build_deterministic_metrics_context_from_observation(_obs(twse_mis_rich_facts__quality_facts__malformed_fields=["last_value"]))
    assert _entry(ctx, "price_change_metrics", "change")["status"] == "blocked_quality_flags"
    assert _entry(ctx, "price_change_metrics", "change")["blocked_reason"] == "malformed_required_fields"


def test_ladder_mismatch_blocks_depth_balance_but_not_best_quote_spread():
    ctx = build_deterministic_metrics_context_from_observation(_obs(twse_mis_rich_facts__quality_facts__ladder_mismatch_flags=["quantity_length_mismatch"]))
    assert _entry(ctx, "displayed_quote_spread_metrics", "displayed_spread")["status"] == "computed"
    for name in ["top5_displayed_bid_volume", "top5_displayed_ask_volume", "displayed_bid_ask_depth_ratio"]:
        assert _entry(ctx, "displayed_depth_balance_metrics", name)["status"] == "blocked_quality_flags"
        assert _entry(ctx, "displayed_depth_balance_metrics", name)["blocked_reason"] == "ladder_mismatch_blocks_depth_metrics"


def test_unsupported_observation_returns_blocked_context_without_raise():
    ctx = build_deterministic_metrics_context_from_observation({"source_id": "OTHER"})
    assert ctx["metric_status"] == "blocked_missing_required_input"
    assert ctx["runtime_populated"] is False
    assert ctx["safe_for_ai_context"] is False


def test_attach_helper_is_pure_copy_and_keeps_ai_context_disabled():
    observation = _obs()
    original = deepcopy(observation)
    attached = attach_deterministic_metrics_context_from_observation(observation)
    assert observation == original
    assert attached is not observation
    assert "deterministic_metrics_context" in attached
    assert attached["deterministic_metrics_context"]["safe_for_ai_context"] is False


def test_builder_output_forbidden_positive_language_and_keys():
    ctx = build_deterministic_metrics_context_from_observation(_obs())
    serialized = json.dumps(ctx, ensure_ascii=False).lower()
    for phrase in [
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
    ]:
        assert phrase not in serialized
    def walk_keys(value, path=()):
        if isinstance(value, dict):
            for item_key, item_value in value.items():
                item_path = path + (item_key,)
                yield item_path
                yield from walk_keys(item_value, item_path)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                yield from walk_keys(item, path + (str(index),))

    for key_path in walk_keys(ctx):
        if "blocked_interpretations" in key_path:
            continue
        assert key_path[-1] not in {
            "recommendation",
            "buy_sell_hold",
            "target_price_estimate",
            "support_level",
            "resistance_level",
            "liquidity_signal",
            "main_force",
        }


def test_runtime_code_does_not_call_builder_or_attach_helper():
    root = Path(__file__).resolve().parents[2]
    allowed = {
        "scripts/observation_contract.py",
        "tests/unit/test_m7c_deterministic_metrics_builder.py",
        "tests/unit/test_m7c_deterministic_metrics_schema.py",
        "tests/unit/test_twse_mis_rich_field_inventory.py",
    }
    names = ["build_deterministic_metrics_context_from_observation", "attach_deterministic_metrics_context_from_observation"]
    for base in ["server", "frontend", "scripts", "tests/unit"]:
        for path in (root / base).rglob("*.py"):
            rel = path.relative_to(root).as_posix()
            text = path.read_text(encoding="utf-8")
            if any(name in text for name in names):
                assert rel in allowed
