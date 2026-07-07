from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

OBSERVATION_SCHEMA_VERSION = "m5_live_observation.normalized.v1"
FAILURE_SCHEMA_VERSION = "m5_live_observation.failure.v1"


TWSE_MIS_RICH_FACTS_SCHEMA_VERSION = "m7a_twse_mis_rich_facts.v1"


def _twse_mis_quantity_unit_policy() -> dict[str, object]:
    return {
        "official_mis_ui_unit_label": "交易單位",
        "api_field_dictionary_available": False,
        "market_mode_required": True,
        "unit_verified_for_runtime_normalization": False,
    }


def build_empty_twse_mis_rich_facts() -> dict[str, object]:
    """Build the schema-only TWSE MIS rich facts contract without parsing rows.

    M7A-02 defines the contract shape only. Runtime parsers must not treat this
    helper as evidence that any rich MIS field has been populated or validated.
    """
    quantity_unit_policy = _twse_mis_quantity_unit_policy()
    return {
        "schema_version": TWSE_MIS_RICH_FACTS_SCHEMA_VERSION,
        "source_id": "TWSE_MIS",
        "schema_status": "defined_not_populated_by_runtime_parser",
        "quantity_unit_policy": dict(quantity_unit_policy),
        "market_mode_facts": {
            "market_mode_candidate": None,
            "source_context": None,
            "known_modes": ["regular_board", "intraday_odd_lot", "index", "unknown"],
            "semantic_status": "schema_defined_not_runtime_populated",
        },
        "instrument_facts": {
            "raw_c": None,
            "raw_ch": None,
            "raw_at": None,
            "raw_key": None,
            "raw_ex": None,
            "raw_name": None,
            "raw_full_name": None,
            "instrument_kind_candidate": None,
            "price_domain": None,
            "semantic_status": "schema_defined_candidate_fields",
            "evidence_policy": {"official_documented": False, "requires_row_context": True},
        },
        "price_facts": {
            "last_value": None,
            "previous_close": None,
            "open": None,
            "high": None,
            "low": None,
            "price_domain": None,
            "source_fields": ["z", "y", "o", "h", "l"],
            "last_value_source_field": None,
            "last_value_placeholder": False,
            "fallback_reference_field": None,
            "semantic_status": "schema_defined_candidate_fields",
            "evidence_level": "schema_only_not_runtime_populated",
        },
        "volume_facts": {
            "raw_v": None,
            "raw_tv": None,
            "raw_ps": None,
            "unit_status": "market_context_required",
            "unit_verified": False,
            "community_default_unit_candidate": "non_authoritative_regular_board_quantity_candidate",
            "quantity_unit_policy": dict(quantity_unit_policy),
            "source_fields": ["v", "tv", "ps"],
            "semantic_status": "schema_defined_candidate_fields",
        },
        "displayed_depth_facts": {
            "applicable": None,
            "applicability_reason": None,
            "bid_prices": [],
            "bid_quantities_raw": [],
            "ask_prices": [],
            "ask_quantities_raw": [],
            "best_bid": None,
            "best_ask": None,
            "ladder_source_fields": ["b", "g", "a", "f"],
            "quantity_unit_policy": dict(quantity_unit_policy),
            "quantity_unit_status": "market_context_required",
            "quantity_unit_verified": False,
            "semantic_status": "displayed_depth_snapshot_only_schema",
            "forbidden_interpretations": ["support_resistance", "true_liquidity", "order_book_truth", "main_force", "trading_signal"],
        },
        "limit_or_reference_facts": {
            "limit_up": None,
            "limit_down": None,
            "raw_pz": None,
            "raw_bp": None,
            "raw_ps": None,
            "applicable": None,
            "applicability_reason": None,
            "source_fields": ["u", "w", "pz", "bp", "ps"],
            "semantic_status": "schema_defined_candidate_fields",
        },
        "auction_or_reference_facts": {
            "raw_ps": None,
            "raw_pz": None,
            "raw_bp": None,
            "raw_s": None,
            "raw_ts": None,
            "observed_in_closing_auction_window": False,
            "observed_in_post_close_snapshot": False,
            "ps_candidate_semantic": "state_dependent_reference_or_match_volume_candidate",
            "pz_candidate_semantic": "state_dependent_reference_or_match_price_candidate",
            "s_candidate_semantic": "match_volume_shadow_candidate",
            "ts_candidate_semantic": "session_or_trial_state_flag_candidate",
            "semantic_status": "operator_evidence_supported_not_official_dictionary",
            "unit_policy": dict(quantity_unit_policy),
        },
        "session_state_candidate_facts": {
            "raw_ip": None,
            "raw_p": None,
            "raw_s": None,
            "raw_ts": None,
            "ts_candidate_semantic": "session_or_trial_state_flag_candidate",
            "known_operator_evidence": "ts=1 observed during closing-auction trial window; ts=0 observed after final match",
            "semantic_status": "candidate_only_not_official_dictionary",
        },
        "index_market_facts": {
            "raw_m": None,
            "raw_r": None,
            "m_candidate_semantic": "index_market_traded_quantity_candidate",
            "r_candidate_semantic": "index_market_trade_count_candidate",
            "evidence_level": "official_mis_ui_cross_checked_not_field_dictionary",
            "unit_status": "market_context_required_not_field_dictionary_validated",
            "quantity_unit_policy": dict(quantity_unit_policy),
            "applicable": None,
            "applicability_reason": None,
            "source_fields": ["m", "r"],
            "semantic_status": "schema_defined_index_candidate_fields",
        },
        "timestamp_facts": {
            "raw_d": None,
            "raw_t": None,
            "raw_tlong": None,
            "raw_percent": None,
            "raw_caret": None,
            "raw_ot": None,
            "source_fields": ["d", "t", "tlong", "%", "^", "ot"],
            "semantic_status": "schema_defined_candidate_fields",
        },
        "raw_unknown_facts": {
            "raw_pid": None, "raw_hash": None, "raw_m_percent": None, "raw_mt": None, "raw_ip": None,
            "raw_i": None, "raw_it": None, "raw_p": None, "raw_q": None,
            "raw_oa": None, "raw_ob": None, "raw_ot": None, "raw_nu": None,
            "semantic_status": "unknown_preserve_raw_only",
        },
        "quality_facts": {
            "field_presence": {},
            "placeholder_fields": [],
            "malformed_fields": [],
            "ladder_mismatch_flags": [],
            "unit_unverified_fields": ["v", "tv", "ps", "s", "g", "f", "m", "r"],
            "unknown_or_raw_only_fields": ["pid", "#", "m%", "mt", "ip", "i", "it", "p", "q", "oa", "ob", "ot", "nu"],
            "not_observed_in_m7a_01d_fields": ["q", "oa", "ob", "ot"],
            "semantic_status": "schema_defined_quality_flags",
        },
        "semantic_confidence": {
            "official_documented": False,
            "probe_observed": False,
            "ui_cross_checked": False,
            "community_supported": False,
            "runtime_validated": False,
            "unit_verified": False,
            "evidence_level": "schema_only",
        },
        "ai_exposure_policy": {
            "safe_for_ai_context": False,
            "reason": "schema_defined_not_runtime_populated",
            "forbidden_interpretations": [
                "buy_signal", "sell_signal", "hold", "target_price", "support_resistance", "main_force",
                "true_liquidity", "order_book_truth", "realtime_guarantee", "execution_feed",
            ],
        },
    }



M7C_DETERMINISTIC_METRICS_SCHEMA_VERSION = "m7c_deterministic_metrics.v1"


def _m7c_metric(formula: str, required_fields: list[str], unit: str, **caveats: object) -> dict[str, object]:
    metric = {
        "formula": formula,
        "required_fields": required_fields,
        "status": "schema_only",
        "value": None,
        "unit": unit,
        "descriptive_only": True,
        "not_signal": True,
    }
    metric.update(caveats)
    return metric


def build_empty_deterministic_metrics_context() -> dict[str, object]:
    """Build the schema-only M7C deterministic metrics context.

    M7C-00/M7C-01 define policy and schema only. This helper does not
    calculate, populate, expose, or integrate metrics into runtime AI context.
    """
    displayed_spread_caveats = {"not_true_liquidity": True, "not_full_order_book": True}
    displayed_depth_caveats = {
        "displayed_depth_snapshot_only": True,
        "not_true_liquidity": True,
        "not_full_order_book": True,
        "not_support_resistance": True,
    }
    return {
        "schema_version": M7C_DETERMINISTIC_METRICS_SCHEMA_VERSION,
        "context_id": "M7C_DETERMINISTIC_METRICS",
        "metric_status": "schema_defined_not_computed",
        "runtime_populated": False,
        "safe_for_ai_context": False,
        "not_trading_signal": True,
        "not_recommendation": True,
        "source_policy": {
            "depends_on": "M7B_AI_SAFE_MARKET_CONTEXT",
            "m7b_final_status": "pass_with_caveats",
            "source_discovery_required": False,
            "live_probe_required": False,
            "official_api_field_dictionary_required": False,
            "realtime_sla_required": False,
            "semantic_status": "schema_only",
        },
        "input_requirements": {
            "price_metrics_required_fields": ["last_value", "previous_close", "open", "high", "low"],
            "displayed_spread_required_fields": ["best_bid", "best_ask"],
            "displayed_depth_balance_required_fields": ["sanitized_top5_bid_quantities", "sanitized_top5_ask_quantities"],
            "quality_inputs": ["reference_only", "malformed_fields", "placeholder_fields", "ladder_mismatch_flags"],
            "semantic_status": "schema_only",
        },
        "quality_gate_policy": {
            "metric_status_values": [
                "schema_only",
                "not_computed",
                "computed",
                "blocked_missing_required_fields",
                "blocked_quality_flags",
                "blocked_zero_denominator",
                "blocked_non_numeric",
            ],
            "block_reference_only_last_value_metrics": True,
            "block_malformed_required_fields": True,
            "block_ladder_mismatch_depth_metrics": True,
            "block_zero_denominator": True,
            "semantic_status": "schema_only",
        },
        "price_change_metrics": {
            "change": _m7c_metric("last_value - previous_close", ["last_value", "previous_close"], "price_points"),
            "change_percent": _m7c_metric("change / previous_close", ["last_value", "previous_close"], "ratio"),
        },
        "intraday_range_metrics": {
            "intraday_range": _m7c_metric("high - low", ["high", "low"], "price_points"),
        },
        "open_high_low_position_metrics": {
            "position_in_day_range": _m7c_metric("(last_value - low) / (high - low)", ["last_value", "high", "low"], "ratio"),
            "distance_from_high_percent": _m7c_metric("(last_value - high) / high", ["last_value", "high"], "ratio"),
            "distance_from_low_percent": _m7c_metric("(last_value - low) / low", ["last_value", "low"], "ratio"),
            "change_from_open_percent": _m7c_metric("(last_value - open) / open", ["last_value", "open"], "ratio"),
        },
        "displayed_quote_spread_metrics": {
            "displayed_spread": _m7c_metric("best_ask - best_bid", ["best_bid", "best_ask"], "price_points", **displayed_spread_caveats),
            "displayed_spread_percent": _m7c_metric("displayed_spread / mid_price", ["best_bid", "best_ask"], "ratio", **displayed_spread_caveats),
        },
        "displayed_depth_balance_metrics": {
            "top5_displayed_bid_volume": _m7c_metric("sum(sanitized_top5_bid_quantities)", ["sanitized_top5_bid_quantities"], "displayed_quantity", **displayed_depth_caveats),
            "top5_displayed_ask_volume": _m7c_metric("sum(sanitized_top5_ask_quantities)", ["sanitized_top5_ask_quantities"], "displayed_quantity", **displayed_depth_caveats),
            "displayed_bid_ask_depth_ratio": _m7c_metric("top5_displayed_bid_volume / top5_displayed_ask_volume", ["sanitized_top5_bid_quantities", "sanitized_top5_ask_quantities"], "ratio", **displayed_depth_caveats),
        },
        "metric_availability": {
            "all_metrics_schema_defined": True,
            "computed_metrics_count": 0,
            "blocked_metrics_count": 0,
            "not_computed_metrics_count": 0,
            "runtime_populated": False,
            "semantic_status": "schema_only",
        },
        "caveat_context": {
            "global_caveats": [
                "schema_only_not_computed",
                "raw_full_ladder_exposure_forbidden",
                "not_trading_signal",
                "not_recommendation",
                "displayed_depth_snapshot_only",
                "not_true_liquidity",
                "not_full_order_book",
                "quality_gated_metrics_required",
            ],
            "semantic_status": "schema_only",
        },
        "blocked_interpretations": [
            "trading_signal", "buy_signal", "sell_signal", "recommendation", "buy_sell_hold",
            "target_price", "support", "resistance", "breakout", "breakdown", "pressure",
            "main_force", "true_liquidity", "full_order_book", "execution_liquidity",
            "predictive_label", "trend_confirmation",
        ],
        "future_builder_requirements": {
            "required_input": "m7b_ai_safe_market_context_projection_or_normalized_observation",
            "must_check_required_fields": True,
            "must_check_quality_flags": True,
            "must_block_zero_denominator": True,
            "must_block_non_numeric": True,
            "must_not_emit_signal_names": True,
            "must_not_emit_recommendations": True,
            "must_keep_safe_for_ai_context_false_until_controlled_integration": True,
            "next_task": "M7C-02-M7C-03-DETERMINISTIC-METRICS-BUILDER-AND-SAFETY-TESTS",
        },
    }


def _m7c_is_number(value: Any) -> bool:
    return _m7c_to_float(value) is not None


def _m7c_to_float(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip()
        if stripped in {"", "-"}:
            return None
        try:
            return float(stripped)
        except ValueError:
            return None
    return None


def _m7c_safe_divide(numerator: float, denominator: float) -> tuple[float | None, str | None]:
    if denominator == 0:
        return None, "zero_denominator"
    return numerator / denominator, None


def _m7c_metric_groups(ctx: Mapping[str, Any]) -> list[str]:
    return [
        "price_change_metrics",
        "intraday_range_metrics",
        "open_high_low_position_metrics",
        "displayed_quote_spread_metrics",
        "displayed_depth_balance_metrics",
    ]


def _m7c_block_metric(entry: dict[str, object], status: str, reason: str) -> None:
    entry["status"] = status
    entry["value"] = None
    entry["blocked_reason"] = reason


def _m7c_compute_metric(entry: dict[str, object], value: float) -> None:
    entry["status"] = "computed"
    entry["value"] = value
    entry.pop("blocked_reason", None)


def _m7c_quality_blocked(required: list[str], malformed: set[str], placeholders: set[str]) -> str | None:
    if any(field in malformed for field in required):
        return "malformed_required_fields"
    if any(field in placeholders for field in required):
        return "placeholder_required_fields"
    return None


def _m7c_numeric_values(fields: Mapping[str, Any], required: list[str]) -> tuple[dict[str, float], str | None, str | None]:
    missing = [field for field in required if field not in fields or fields[field] is None]
    if missing:
        return {}, "blocked_missing_required_fields", "missing_required_fields"
    values: dict[str, float] = {}
    for field in required:
        converted = _m7c_to_float(fields[field])
        if converted is None:
            return {}, "blocked_non_numeric", "non_numeric_required_fields"
        values[field] = converted
    return values, None, None


def _m7c_sanitized_top5(values: Any) -> list[float] | None:
    if not isinstance(values, list):
        return None
    sanitized: list[float] = []
    for value in values[:5]:
        converted = _m7c_to_float(value)
        if converted is None:
            return None
        sanitized.append(converted)
    return sanitized


def _m7c_block_or_compute(
    ctx: dict[str, object],
    group: str,
    name: str,
    fields: Mapping[str, Any],
    malformed: set[str],
    placeholders: set[str],
    reference_only: bool,
    calculator: Any,
    *,
    reference_blocks: bool = False,
    denominator_reason: str | None = None,
) -> None:
    entry = ctx[group][name]  # type: ignore[index]
    required = list(entry["required_fields"])  # type: ignore[index]
    if reference_only and reference_blocks:
        _m7c_block_metric(entry, "blocked_quality_flags", "reference_only_blocks_last_value_metrics")
        return
    quality_reason = _m7c_quality_blocked(required, malformed, placeholders)
    if quality_reason:
        _m7c_block_metric(entry, "blocked_quality_flags", quality_reason)
        return
    values, status, reason = _m7c_numeric_values(fields, required)
    if status:
        _m7c_block_metric(entry, status, reason or status)
        return
    value, zero_reason = calculator(values)
    if zero_reason:
        _m7c_block_metric(entry, "blocked_zero_denominator", denominator_reason or zero_reason)
        return
    _m7c_compute_metric(entry, value)  # type: ignore[arg-type]


def build_deterministic_metrics_context_from_observation(observation: Mapping[str, Any]) -> dict[str, object]:
    """Compute M7C deterministic metrics from normalized rich facts without I/O.

    The builder is a pure candidate helper only. It does not expose raw rich facts,
    does not alter runtime behavior, and keeps AI-context exposure disabled.
    """
    ctx = build_empty_deterministic_metrics_context()
    if not isinstance(observation, Mapping):
        ctx["metric_status"] = "blocked_missing_required_input"
        ctx["blocked_reason"] = "missing_required_observation"
        return ctx

    rich = observation.get("twse_mis_rich_facts")
    if not isinstance(rich, Mapping):
        ctx["metric_status"] = "blocked_missing_required_input"
        ctx["blocked_reason"] = "missing_required_observation"
        return ctx

    price = rich.get("price_facts") if isinstance(rich.get("price_facts"), Mapping) else {}
    depth = rich.get("displayed_depth_facts") if isinstance(rich.get("displayed_depth_facts"), Mapping) else {}
    quality = rich.get("quality_facts") if isinstance(rich.get("quality_facts"), Mapping) else {}
    malformed = set(quality.get("malformed_fields", []) if isinstance(quality, Mapping) else []) | set(observation.get("data_quality_flags", []) or [])
    placeholders = set(quality.get("placeholder_fields", []) if isinstance(quality, Mapping) else [])
    ladder_mismatch = list(quality.get("ladder_mismatch_flags", []) if isinstance(quality, Mapping) else [])
    source_risk = set(observation.get("source_risk_flags", []) or [])
    reference_only = bool(observation.get("reference_only")) or "reference_only" in source_risk

    fields: dict[str, Any] = {}
    if isinstance(price, Mapping):
        fields.update({k: price.get(k) for k in ["last_value", "previous_close", "open", "high", "low"]})
    if isinstance(depth, Mapping):
        fields.update({k: depth.get(k) for k in ["best_bid", "best_ask", "sanitized_top5_bid_quantities", "sanitized_top5_ask_quantities"]})
        if fields.get("sanitized_top5_bid_quantities") is None and isinstance(depth.get("bid_quantities"), list):
            fields["sanitized_top5_bid_quantities"] = _m7c_sanitized_top5(depth.get("bid_quantities"))
        if fields.get("sanitized_top5_ask_quantities") is None and isinstance(depth.get("ask_quantities"), list):
            fields["sanitized_top5_ask_quantities"] = _m7c_sanitized_top5(depth.get("ask_quantities"))
        if fields.get("sanitized_top5_bid_quantities") is None and isinstance(depth.get("bid_quantities_raw"), list):
            fields["sanitized_top5_bid_quantities"] = _m7c_sanitized_top5(depth.get("bid_quantities_raw"))
        if fields.get("sanitized_top5_ask_quantities") is None and isinstance(depth.get("ask_quantities_raw"), list):
            fields["sanitized_top5_ask_quantities"] = _m7c_sanitized_top5(depth.get("ask_quantities_raw"))

    _m7c_block_or_compute(ctx, "price_change_metrics", "change", fields, malformed, placeholders, reference_only, lambda v: (v["last_value"] - v["previous_close"], None), reference_blocks=True)
    _m7c_block_or_compute(ctx, "price_change_metrics", "change_percent", fields, malformed, placeholders, reference_only, lambda v: _m7c_safe_divide(v["last_value"] - v["previous_close"], v["previous_close"]), reference_blocks=True)
    _m7c_block_or_compute(ctx, "intraday_range_metrics", "intraday_range", fields, malformed, placeholders, reference_only, lambda v: (v["high"] - v["low"], None))
    _m7c_block_or_compute(ctx, "open_high_low_position_metrics", "position_in_day_range", fields, malformed, placeholders, reference_only, lambda v: _m7c_safe_divide(v["last_value"] - v["low"], v["high"] - v["low"]), reference_blocks=True)
    _m7c_block_or_compute(ctx, "open_high_low_position_metrics", "distance_from_high_percent", fields, malformed, placeholders, reference_only, lambda v: _m7c_safe_divide(v["last_value"] - v["high"], v["high"]), reference_blocks=True)
    _m7c_block_or_compute(ctx, "open_high_low_position_metrics", "distance_from_low_percent", fields, malformed, placeholders, reference_only, lambda v: _m7c_safe_divide(v["last_value"] - v["low"], v["low"]), reference_blocks=True)
    _m7c_block_or_compute(ctx, "open_high_low_position_metrics", "change_from_open_percent", fields, malformed, placeholders, reference_only, lambda v: _m7c_safe_divide(v["last_value"] - v["open"], v["open"]), reference_blocks=True)
    _m7c_block_or_compute(ctx, "displayed_quote_spread_metrics", "displayed_spread", fields, malformed, placeholders, reference_only, lambda v: (v["best_ask"] - v["best_bid"], None))
    _m7c_block_or_compute(ctx, "displayed_quote_spread_metrics", "displayed_spread_percent", fields, malformed, placeholders, reference_only, lambda v: _m7c_safe_divide(v["best_ask"] - v["best_bid"], (v["best_bid"] + v["best_ask"]) / 2))

    depth_names = ["top5_displayed_bid_volume", "top5_displayed_ask_volume", "displayed_bid_ask_depth_ratio"]
    if ladder_mismatch:
        for name in depth_names:
            _m7c_block_metric(ctx["displayed_depth_balance_metrics"][name], "blocked_quality_flags", "ladder_mismatch_blocks_depth_metrics")  # type: ignore[index]
    else:
        bids = _m7c_sanitized_top5(fields.get("sanitized_top5_bid_quantities"))
        asks = _m7c_sanitized_top5(fields.get("sanitized_top5_ask_quantities"))
        if bids is None:
            _m7c_block_metric(ctx["displayed_depth_balance_metrics"]["top5_displayed_bid_volume"], "blocked_missing_required_fields", "missing_required_fields")  # type: ignore[index]
        else:
            _m7c_compute_metric(ctx["displayed_depth_balance_metrics"]["top5_displayed_bid_volume"], sum(bids))  # type: ignore[index]
        if asks is None:
            _m7c_block_metric(ctx["displayed_depth_balance_metrics"]["top5_displayed_ask_volume"], "blocked_missing_required_fields", "missing_required_fields")  # type: ignore[index]
        else:
            _m7c_compute_metric(ctx["displayed_depth_balance_metrics"]["top5_displayed_ask_volume"], sum(asks))  # type: ignore[index]
        ratio_entry = ctx["displayed_depth_balance_metrics"]["displayed_bid_ask_depth_ratio"]  # type: ignore[index]
        if bids is None or asks is None:
            _m7c_block_metric(ratio_entry, "blocked_missing_required_fields", "missing_required_fields")
        else:
            ratio, reason = _m7c_safe_divide(sum(bids), sum(asks))
            if reason:
                _m7c_block_metric(ratio_entry, "blocked_zero_denominator", "zero_denominator")
            else:
                _m7c_compute_metric(ratio_entry, ratio)  # type: ignore[arg-type]

    computed: list[str] = []
    blocked: list[str] = []
    not_computed = 0
    caveats = set(ctx["caveat_context"]["global_caveats"])  # type: ignore[index]
    for group in _m7c_metric_groups(ctx):
        for name, entry in ctx[group].items():  # type: ignore[index,union-attr]
            if entry["status"] == "computed":
                computed.append(name)
            elif str(entry["status"]).startswith("blocked_"):
                blocked.append(name)
                if entry.get("blocked_reason"):
                    caveats.add(str(entry["blocked_reason"]))
            else:
                not_computed += 1
    caveats.update({"displayed_depth_snapshot_only", "not_true_liquidity", "not_full_order_book", "not_trading_signal", "not_recommendation"})
    ctx["metric_status"] = "runtime_computed_candidate"
    ctx["runtime_populated"] = True
    ctx["safe_for_ai_context"] = False
    ctx["metric_availability"] = {
        "all_metrics_schema_defined": True,
        "computed_metrics_count": len(computed),
        "blocked_metrics_count": len(blocked),
        "not_computed_metrics_count": not_computed,
        "runtime_populated": True,
        "semantic_status": "runtime_computed_candidate",
        "computed_metric_names": computed,
        "blocked_metric_names": blocked,
    }
    ctx["caveat_context"]["global_caveats"] = sorted(caveats)  # type: ignore[index]
    ctx["caveat_context"]["semantic_status"] = "runtime_computed_candidate"  # type: ignore[index]
    return ctx


def attach_deterministic_metrics_context_from_observation(observation: Mapping[str, Any]) -> dict[str, Any]:
    """Return a copy of observation with a candidate M7C metrics context attached."""
    attached = dict(observation)
    attached["deterministic_metrics_context"] = build_deterministic_metrics_context_from_observation(observation)
    return attached


AI_SAFE_MARKET_CONTEXT_PROJECTION_SCHEMA_VERSION = "m7b_ai_safe_market_context_projection.v1"


def build_empty_ai_safe_market_context_projection() -> dict[str, object]:
    """Build the schema-only M7B AI-safe market context projection.

    M7B-00/M7B-01 define policy and schema only. This helper does not parse,
    project, expose, or enable runtime AI context from M7A rich facts.
    """
    return {
        "schema_version": AI_SAFE_MARKET_CONTEXT_PROJECTION_SCHEMA_VERSION,
        "projection_id": "TWSE_MIS_AI_SAFE_MARKET_CONTEXT",
        "source_family": "TWSE_MIS",
        "projection_status": "schema_defined_not_runtime_populated",
        "exposure_status": "projection_candidate_not_exposed",
        "safe_for_ai_context": False,
        "source_policy": {
            "official_api_field_dictionary_available": False,
            "realtime_sla_verified": False,
            "unit_verified_for_runtime_normalization": False,
            "source_may_be_delayed_or_unavailable": True,
            "m7a_status": "pass_with_caveats",
            "m7a_dependency": "docs/protocol/M7A_TWSE_MIS_RICH_FACTS_FINAL_ACCEPTANCE.md",
        },
        "instrument_context": {
            "instrument_kind": None,
            "price_domain": None,
            "market_mode": None,
            "source_symbol": None,
            "display_name": None,
            "semantic_status": "schema_only",
        },
        "market_session_context": {
            "session_state_candidate": None,
            "session_state_confidence": "candidate_only",
            "closing_auction_candidate": False,
            "post_close_candidate": False,
            "odd_lot_mode_supported": False,
            "semantic_status": "schema_only",
        },
        "price_snapshot_context": {
            "last_value_available": None,
            "last_value": None,
            "previous_close": None,
            "open": None,
            "high": None,
            "low": None,
            "direction_vs_previous_close": "unknown",
            "descriptive_only": True,
            "not_recommendation": True,
            "semantic_status": "schema_only",
        },
        "reference_context": {
            "fallback_reference_field": None,
            "reference_only": None,
            "auction_or_reference_price_available": None,
            "auction_or_reference_volume_available": None,
            "pz_does_not_override_last_value": True,
            "ps_does_not_override_current_volume": True,
            "semantic_status": "schema_only",
        },
        "index_market_context": {
            "applicable": None,
            "traded_quantity_candidate_available": None,
            "trade_count_candidate_available": None,
            "quantity_unit_verified": False,
            "evidence_level": "official_mis_ui_cross_checked_not_field_dictionary",
            "semantic_status": "schema_only",
        },
        "displayed_depth_context": {
            "available": None,
            "best_bid_available": None,
            "best_ask_available": None,
            "full_ladder_exposed": False,
            "interpretation_policy": "displayed_depth_snapshot_only",
            "not_support_resistance": True,
            "not_true_liquidity": True,
            "not_full_order_book": True,
            "not_trading_signal": True,
            "semantic_status": "schema_only",
        },
        "data_quality_context": {
            "placeholder_fields": [],
            "malformed_fields": [],
            "ladder_mismatch_flags": [],
            "quality_warnings": [],
            "semantic_status": "schema_only",
        },
        "freshness_context": {
            "source_timestamp": None,
            "retrieved_at_utc": None,
            "delay_seconds": None,
            "freshness_assessment": None,
            "not_realtime_guaranteed": True,
            "semantic_status": "schema_only",
        },
        "caveat_context": {
            "global_caveats": [
                "no_official_twse_mis_api_field_dictionary",
                "not_realtime_guaranteed",
                "unit_verification_unavailable",
                "displayed_depth_snapshot_only",
                "not_trading_signal",
                "ai_projection_not_enabled",
            ],
            "semantic_status": "schema_only",
        },
        "evidence_context": {
            "allowed_evidence_levels": [
                "runtime_parsed_candidate",
                "operator_evidence_supported_not_official_dictionary",
                "official_mis_ui_cross_checked_not_field_dictionary",
                "probe_observed",
                "market_context_required",
            ],
            "official_documented": False,
            "unit_verified": False,
            "semantic_status": "schema_only",
        },
        "blocked_interpretations": [
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
        ],
        "future_builder_requirements": {
            "required_input": "normalized_observation_with_twse_mis_rich_facts",
            "must_preserve_top_level_z_y_fallback": True,
            "must_preserve_reference_only": True,
            "must_not_use_pz_as_last_value": True,
            "must_not_use_ps_as_current_volume": True,
            "must_not_expose_full_ladder_by_default": True,
            "must_keep_safe_for_ai_context_false_until_policy_enabled": True,
            "next_task": "M7B-02-M7B-03-PURE-PROJECTION-BUILDER-AND-SAFETY-TESTS",
        },
    }


def attach_empty_ai_safe_market_context_projection(observation: Mapping[str, Any]) -> dict[str, Any]:
    """Return a copy with the empty M7B schema attached without mutating input."""
    projected = dict(observation)
    projected["ai_safe_market_context_projection"] = build_empty_ai_safe_market_context_projection()
    return projected



def _m7b_meaningful(value: Any) -> bool:
    return value not in (None, "", "-")


def _m7b_direction(last_value: Any, previous_close: Any) -> str:
    if isinstance(last_value, (int, float)) and isinstance(previous_close, (int, float)):
        if last_value > previous_close:
            return "up"
        if last_value < previous_close:
            return "down"
        return "flat"
    return "unknown"


def _m7b_copy_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def build_ai_safe_market_context_projection_from_observation(
    observation: Mapping[str, Any],
) -> dict[str, object]:
    """Build a pure M7B projection from a normalized TWSE MIS observation.

    The builder is intentionally side-effect free: it performs no I/O, does not
    mutate the input observation, and keeps runtime exposure disabled.
    """
    projection = build_empty_ai_safe_market_context_projection()

    if observation.get("source") != "TWSE_MIS":
        projection["projection_status"] = "blocked_missing_required_input"
        projection["exposure_status"] = "blocked"
        projection["safe_for_ai_context"] = False
        projection["blocked_reason"] = "non_twse_mis_source"
        return projection

    rich = observation.get("twse_mis_rich_facts")
    if not isinstance(rich, Mapping):
        projection["projection_status"] = "blocked_missing_required_input"
        projection["exposure_status"] = "blocked"
        projection["safe_for_ai_context"] = False
        projection["blocked_reason"] = "missing_twse_mis_rich_facts"
        return projection

    market_mode = rich.get("market_mode_facts") if isinstance(rich.get("market_mode_facts"), Mapping) else {}
    instrument = rich.get("instrument_facts") if isinstance(rich.get("instrument_facts"), Mapping) else {}
    session = rich.get("session_state_candidate_facts") if isinstance(rich.get("session_state_candidate_facts"), Mapping) else {}
    price = rich.get("price_facts") if isinstance(rich.get("price_facts"), Mapping) else {}
    auction = rich.get("auction_or_reference_facts") if isinstance(rich.get("auction_or_reference_facts"), Mapping) else {}
    index = rich.get("index_market_facts") if isinstance(rich.get("index_market_facts"), Mapping) else {}
    depth = rich.get("displayed_depth_facts") if isinstance(rich.get("displayed_depth_facts"), Mapping) else {}
    quality = rich.get("quality_facts") if isinstance(rich.get("quality_facts"), Mapping) else {}

    projection["projection_status"] = "runtime_projected_candidate"
    projection["exposure_status"] = "ai_safe_projection_candidate"
    projection["safe_for_ai_context"] = False

    projection["instrument_context"].update({
        "instrument_kind": instrument.get("instrument_kind_candidate"),
        "price_domain": instrument.get("price_domain"),
        "market_mode": market_mode.get("market_mode_candidate"),
        "source_symbol": instrument.get("raw_c") or observation.get("symbol"),
        "display_name": instrument.get("raw_name") or observation.get("display_symbol"),
        "semantic_status": "runtime_projected_candidate",
    })
    projection["market_session_context"].update({
        "session_state_candidate": session.get("session_state_candidate"),
        "closing_auction_candidate": auction.get("observed_in_closing_auction_window") is True,
        "post_close_candidate": auction.get("observed_in_post_close_snapshot") is True,
        "odd_lot_mode_supported": False,
        "semantic_status": "runtime_projected_candidate",
    })

    last_value = price.get("last_value")
    previous_close = price.get("previous_close")
    projection["price_snapshot_context"].update({
        "last_value_available": last_value is not None,
        "last_value": last_value,
        "previous_close": previous_close,
        "open": price.get("open"),
        "high": price.get("high"),
        "low": price.get("low"),
        "direction_vs_previous_close": _m7b_direction(last_value, previous_close),
        "descriptive_only": True,
        "not_recommendation": True,
        "semantic_status": "runtime_projected_candidate",
    })
    projection["reference_context"].update({
        "fallback_reference_field": price.get("fallback_reference_field"),
        "reference_only": observation.get("reference_only"),
        "auction_or_reference_price_available": _m7b_meaningful(auction.get("raw_pz")),
        "auction_or_reference_volume_available": _m7b_meaningful(auction.get("raw_ps")),
        "pz_does_not_override_last_value": True,
        "ps_does_not_override_current_volume": True,
        "semantic_status": "runtime_projected_candidate",
    })

    index_applicable = index.get("applicable") is True
    projection["index_market_context"].update({
        "applicable": index_applicable,
        "traded_quantity_candidate_available": index_applicable and _m7b_meaningful(index.get("raw_m")),
        "trade_count_candidate_available": index_applicable and _m7b_meaningful(index.get("raw_r")),
        "quantity_unit_verified": False,
        "evidence_level": "official_mis_ui_cross_checked_not_field_dictionary",
        "semantic_status": "runtime_projected_candidate",
    })

    ladder_flags = _m7b_copy_list(depth.get("ladder_mismatch_flags")) or _m7b_copy_list(quality.get("ladder_mismatch_flags"))
    projection["displayed_depth_context"].update({
        "available": depth.get("applicable") is True,
        "best_bid_available": depth.get("best_bid") is not None,
        "best_ask_available": depth.get("best_ask") is not None,
        "full_ladder_exposed": False,
        "interpretation_policy": "displayed_depth_snapshot_only",
        "not_support_resistance": True,
        "not_true_liquidity": True,
        "not_full_order_book": True,
        "not_trading_signal": True,
        "ladder_quality_warnings": ladder_flags,
        "semantic_status": "runtime_projected_candidate",
    })

    quality_warnings = sorted(set(_m7b_copy_list(observation.get("data_quality_flags")) + _m7b_copy_list(observation.get("source_risk_flags")) + _m7b_copy_list(quality.get("malformed_fields")) + ladder_flags))
    projection["data_quality_context"].update({
        "placeholder_fields": _m7b_copy_list(quality.get("placeholder_fields")),
        "malformed_fields": _m7b_copy_list(quality.get("malformed_fields")),
        "ladder_mismatch_flags": ladder_flags,
        "quality_warnings": quality_warnings,
        "semantic_status": "runtime_projected_candidate",
    })
    projection["freshness_context"].update({
        "source_timestamp": observation.get("source_timestamp"),
        "retrieved_at_utc": observation.get("retrieved_at_utc"),
        "delay_seconds": observation.get("delay_seconds"),
        "freshness_assessment": observation.get("freshness_assessment"),
        "not_realtime_guaranteed": True,
        "semantic_status": "runtime_projected_candidate",
    })

    dynamic_caveats = []
    if observation.get("reference_only") is True:
        dynamic_caveats.append("reference_only_value")
    if last_value is None:
        dynamic_caveats.append("current_last_value_unavailable")
    if quality.get("malformed_fields"):
        dynamic_caveats.append("malformed_fields_present")
    if ladder_flags:
        dynamic_caveats.append("ladder_mismatch_present")
    dynamic_caveats.append("index_row_candidate_fields" if index_applicable else "non_index_security_row")
    projection["caveat_context"].update({
        "dynamic_caveats": sorted(set(dynamic_caveats)),
        "semantic_status": "runtime_projected_candidate",
    })
    projection["evidence_context"].update({
        "official_documented": False,
        "unit_verified": False,
        "semantic_status": "runtime_projected_candidate",
    })
    return projection



def promote_ai_safe_market_context_projection_for_controlled_context(
    projection: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a controlled-conversation copy of a valid M7B projection.

    The pure M7B builder remains a non-exposed candidate.  This promotion
    layer is the only place that may mark the projection safe for AI context,
    and it only does so for the M7B projection schema -- never for M7A rich
    facts or raw source payloads.
    """
    promoted = dict(projection)
    promoted.setdefault("raw_rich_facts_exposed", False)
    promoted.setdefault("full_ladder_exposed", False)

    valid_candidate = (
        promoted.get("schema_version") == AI_SAFE_MARKET_CONTEXT_PROJECTION_SCHEMA_VERSION
        and promoted.get("projection_status") == "runtime_projected_candidate"
        and promoted.get("exposure_status") == "ai_safe_projection_candidate"
    )
    if not valid_candidate:
        promoted["safe_for_ai_context"] = False
        promoted["exposure_status"] = "blocked"
        promoted["blocked_reason"] = "not_valid_m7b_projection_candidate"
        promoted["controlled_exposure_policy"] = "m7b_controlled_context_projection_v1"
        promoted["exposure_scope"] = "blocked_not_exposed"
        promoted["raw_rich_facts_exposed"] = False
        promoted["full_ladder_exposed"] = False
        return promoted

    promoted.pop("future_builder_requirements", None)
    source_policy = promoted.get("source_policy")
    if isinstance(source_policy, dict):
        source_policy = dict(source_policy)
        source_policy.pop("m7a_dependency", None)
        promoted["source_policy"] = source_policy
    promoted["safe_for_ai_context"] = True
    promoted["exposure_status"] = "ai_safe_context_enabled"
    promoted["controlled_exposure_policy"] = "m7b_controlled_context_projection_v1"
    promoted["exposure_scope"] = "conversation_context_only"
    promoted["raw_rich_facts_exposed"] = False
    promoted["full_ladder_exposed"] = False
    promoted["not_trading_signal"] = True
    promoted["not_recommendation"] = True
    return promoted

def attach_ai_safe_market_context_projection_from_observation(
    observation: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a copy with the pure M7B projection attached without mutating input."""
    projected = dict(observation)
    projected["ai_safe_market_context_projection"] = build_ai_safe_market_context_projection_from_observation(observation)
    return projected

def _twse_mis_is_placeholder(value: Any) -> bool:
    return value in (None, "", "-")


def _parse_twse_mis_decimal(
    row: Mapping[str, Any],
    field: str,
    malformed_fields: list[str],
    *,
    placeholder_is_malformed: bool = False,
) -> float | None:
    value = row.get(field)
    if _twse_mis_is_placeholder(value):
        if placeholder_is_malformed and value not in (None, ""):
            malformed_fields.append(field)
        return None
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        malformed_fields.append(field)
        return None


def _parse_twse_mis_ladder_prices(raw: Any, field: str, malformed_fields: list[str]) -> list[float]:
    if _twse_mis_is_placeholder(raw):
        return []
    values: list[float] = []
    for part in str(raw).split("_"):
        if part == "":
            continue
        try:
            values.append(float(part.replace(",", "")))
        except ValueError:
            malformed_fields.append(field)
    return values


def _parse_twse_mis_ladder_raw(raw: Any) -> list[str]:
    if _twse_mis_is_placeholder(raw):
        return []
    return [part for part in str(raw).split("_") if part != ""]


def _twse_mis_instrument_kind(row: Mapping[str, Any]) -> tuple[str, str, str]:
    c = str(row.get("c") or "")
    ch = str(row.get("ch") or "")
    i = str(row.get("i") or "")
    ex = str(row.get("ex") or "")
    if c == "t00" or ch == "t00.tw" or i == "tidx.tw":
        return "index", "index", "index_level"
    if ex in {"tse", "otc"} and c.isdigit():
        return "security", "regular_board", "equity_price"
    return "unknown", "unknown", "unknown"


def build_twse_mis_rich_facts_from_row(row: Mapping[str, Any]) -> dict[str, object]:
    """Build conservative runtime-parsed TWSE MIS rich facts from one raw MIS row.

    This parser preserves raw/candidate semantics only; it does not claim an
    official API field dictionary, realtime guarantee, or verified quantity unit.
    """
    facts = build_empty_twse_mis_rich_facts()
    malformed_fields: list[str] = []
    placeholder_fields = sorted(str(k) for k, v in row.items() if v == "-")
    instrument_kind, market_mode, price_domain = _twse_mis_instrument_kind(row)
    is_index = instrument_kind == "index"

    facts["schema_status"] = "runtime_parsed_candidate"
    facts["market_mode_facts"].update({
        "market_mode_candidate": market_mode,
        "source_context": "runtime_parsed_candidate",
        "semantic_status": "runtime_parsed_candidate",
    })
    facts["instrument_facts"].update({
        "raw_c": row.get("c"), "raw_ch": row.get("ch"), "raw_at": row.get("@"),
        "raw_key": row.get("key"), "raw_ex": row.get("ex"), "raw_name": row.get("n"),
        "raw_full_name": row.get("nf"), "instrument_kind_candidate": instrument_kind,
        "price_domain": price_domain, "semantic_status": "runtime_parsed_candidate",
    })

    z_value = _parse_twse_mis_decimal(row, "z", malformed_fields)
    y_value = _parse_twse_mis_decimal(row, "y", malformed_fields)
    fallback_reference_field = "y" if z_value is None and y_value is not None else None
    price_facts = facts["price_facts"]
    price_facts.update({
        "last_value": z_value,
        "last_value_source_field": "z" if z_value is not None else None,
        "last_value_placeholder": row.get("z") in (None, "", "-"),
        "previous_close": y_value,
        "open": _parse_twse_mis_decimal(row, "o", malformed_fields),
        "high": _parse_twse_mis_decimal(row, "h", malformed_fields),
        "low": _parse_twse_mis_decimal(row, "l", malformed_fields),
        "price_domain": price_domain,
        "fallback_reference_field": fallback_reference_field,
        "semantic_status": "runtime_parsed_candidate",
        "evidence_level": "runtime_parsed_candidate",
    })

    facts["volume_facts"].update({
        "raw_v": row.get("v"), "raw_tv": row.get("tv"), "raw_ps": row.get("ps"),
        "semantic_status": "runtime_parsed_candidate",
    })

    depth = facts["displayed_depth_facts"]
    if is_index:
        depth.update({"applicable": False, "applicability_reason": "index_observation_has_no_displayed_depth_fields"})
    else:
        bid_prices = _parse_twse_mis_ladder_prices(row.get("b"), "b", malformed_fields)
        ask_prices = _parse_twse_mis_ladder_prices(row.get("a"), "a", malformed_fields)
        bid_qty = _parse_twse_mis_ladder_raw(row.get("g"))
        ask_qty = _parse_twse_mis_ladder_raw(row.get("f"))
        depth.update({
            "applicable": any(k in row for k in ("a", "b", "f", "g")),
            "applicability_reason": None,
            "bid_prices": bid_prices, "bid_quantities_raw": bid_qty,
            "ask_prices": ask_prices, "ask_quantities_raw": ask_qty,
            "best_bid": bid_prices[0] if bid_prices else None,
            "best_ask": ask_prices[0] if ask_prices else None,
            "semantic_status": "runtime_parsed_candidate_displayed_depth_snapshot_only",
        })

    limit = facts["limit_or_reference_facts"]
    if is_index:
        limit.update({"applicable": False, "applicability_reason": "index_observation_has_no_limit_up_down_fields"})
    else:
        limit.update({
            "applicable": True, "applicability_reason": None,
            "limit_up": _parse_twse_mis_decimal(row, "u", malformed_fields),
            "limit_down": _parse_twse_mis_decimal(row, "w", malformed_fields),
            "raw_pz": row.get("pz"), "raw_bp": row.get("bp"), "raw_ps": row.get("ps"),
            "semantic_status": "runtime_parsed_candidate",
        })

    z_numeric = z_value is not None
    tv_numeric = _parse_twse_mis_decimal(row, "tv", malformed_fields) is not None
    auction = facts["auction_or_reference_facts"]
    post_close = row.get("ts") == "0" and z_numeric and tv_numeric and row.get("ps") == row.get("tv") and row.get("pz") == row.get("z")
    auction.update({
        "raw_ps": row.get("ps"), "raw_pz": row.get("pz"), "raw_bp": row.get("bp"),
        "raw_s": row.get("s"), "raw_ts": row.get("ts"),
        "observed_in_closing_auction_window": row.get("ts") == "1",
        "observed_in_post_close_snapshot": post_close,
    })

    session = facts["session_state_candidate_facts"]
    session.update({
        "raw_ip": row.get("ip"), "raw_p": row.get("p"), "raw_s": row.get("s"), "raw_ts": row.get("ts"),
        "session_state_candidate": "closing_auction_candidate" if row.get("ts") == "1" else ("regular_or_post_close_candidate" if row.get("ts") == "0" and z_numeric else None),
    })

    index_facts = facts["index_market_facts"]
    if is_index:
        index_facts.update({
            "applicable": True, "applicability_reason": None, "raw_m": row.get("m"), "raw_r": row.get("r"),
            "m_candidate_semantic": "index_market_traded_quantity_candidate",
            "r_candidate_semantic": "index_market_trade_count_candidate",
            "evidence_level": "official_mis_ui_cross_checked_not_field_dictionary",
            "semantic_status": "runtime_parsed_candidate",
        })
    else:
        index_facts.update({"applicable": False, "applicability_reason": "non_index_security_row"})

    facts["timestamp_facts"].update({
        "raw_d": row.get("d"), "raw_t": row.get("t"), "raw_tlong": row.get("tlong"),
        "raw_percent": row.get("%"), "raw_caret": row.get("^"), "raw_ot": row.get("ot"),
        "semantic_status": "runtime_parsed_candidate",
    })
    facts["raw_unknown_facts"].update({
        "raw_pid": row.get("pid"), "raw_hash": row.get("#"), "raw_m_percent": row.get("m%"),
        "raw_mt": row.get("mt"), "raw_ip": row.get("ip"), "raw_i": row.get("i"),
        "raw_it": row.get("it"), "raw_p": row.get("p"), "raw_q": row.get("q"),
        "raw_oa": row.get("oa"), "raw_ob": row.get("ob"), "raw_ot": row.get("ot"), "raw_nu": row.get("nu"),
        **({"raw_m": row.get("m")} if not is_index and "m" in row else {}),
    })

    ladder_flags: list[str] = []
    if not is_index:
        if len(depth["bid_prices"]) != len(depth["bid_quantities_raw"]):
            ladder_flags.append("bid_ladder_length_mismatch")
        if len(depth["ask_prices"]) != len(depth["ask_quantities_raw"]):
            ladder_flags.append("ask_ladder_length_mismatch")
    facts["quality_facts"].update({
        "field_presence": {str(k): v not in (None, "") for k, v in row.items()},
        "placeholder_fields": placeholder_fields,
        "malformed_fields": sorted(set(malformed_fields)),
        "ladder_mismatch_flags": ladder_flags,
        "semantic_status": "runtime_parsed_candidate",
    })
    facts["semantic_confidence"].update({
        "official_documented": False, "runtime_validated": True, "unit_verified": False,
        "evidence_level": "runtime_parsed_candidate",
    })
    facts["ai_exposure_policy"].update({
        "safe_for_ai_context": False,
        "reason": "runtime_parsed_candidate_not_exposed_pending_m7a_05",
    })
    return facts


def attach_twse_mis_rich_facts_from_row(observation: Mapping[str, Any], row: Mapping[str, Any]) -> dict[str, Any]:
    attached = dict(observation)
    attached["twse_mis_rich_facts"] = build_twse_mis_rich_facts_from_row(row)
    return attached

def attach_empty_twse_mis_rich_facts(observation: Mapping[str, Any]) -> dict[str, Any]:
    """Return a copy of an observation with schema-only empty TWSE MIS rich facts."""
    attached = dict(observation)
    attached["twse_mis_rich_facts"] = build_empty_twse_mis_rich_facts()
    return attached


def normalize_timestamp(value: Any, *, retrieved_at_utc: str | None = None, source_timezone: timezone = timezone.utc) -> dict[str, Any]:
    """Normalize common source timestamp shapes without claiming realtime status."""
    if value in (None, "", "-"):
        return {"source_timestamp": None, "delay_seconds": None, "flags": ["source_time_unavailable"]}
    flags: list[str] = []
    try:
        if isinstance(value, (int, float)) or str(value).isdigit() and len(str(value)) >= 12:
            dt = datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc)
        else:
            text = str(value)
            if len(text) == 17 and text[:8].isdigit():
                dt = datetime.strptime(text, "%Y%m%d %H:%M:%S").replace(tzinfo=source_timezone).astimezone(timezone.utc)
            else:
                dt = datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)
    except (TypeError, ValueError, OSError):
        return {"source_timestamp": None, "delay_seconds": None, "flags": ["malformed_source_timestamp"]}
    delay_seconds = None
    if retrieved_at_utc:
        try:
            retrieved_dt = datetime.fromisoformat(retrieved_at_utc.replace("Z", "+00:00"))
            delay_seconds = max(0, int((retrieved_dt - dt).total_seconds()))
        except ValueError:
            flags.append("malformed_retrieved_timestamp")
    return {"source_timestamp": dt.strftime("%Y-%m-%dT%H:%M:%SZ"), "delay_seconds": delay_seconds, "flags": flags}


def normalize_freshness(delay_seconds: int | None, *, fresh_threshold_seconds: int = 900) -> str:
    if delay_seconds is None:
        return "unknown"
    return "fresh" if delay_seconds <= fresh_threshold_seconds else "stale_or_closed_session"


def normalize_observation(
    *,
    symbol: str,
    source: str,
    adapter_id: str,
    status: str,
    retrieved_at_utc: str,
    display_symbol: str | None = None,
    market: str | None = None,
    instrument_type: str | None = None,
    category_id: str | None = None,
    source_type: str | None = None,
    price_like_value: float | None = None,
    value: float | None = None,
    price_semantics: str | None = None,
    source_timestamp: str | None = None,
    freshness_assessment: str = "unknown",
    delay_status: str = "not_realtime_guaranteed",
    delay_seconds: int | None = None,
    reference_only: bool = False,
    contract: str | None = None,
    contract_month: str | None = None,
    contract_selector: str | None = None,
    data_quality_flags: list[str] | None = None,
    source_risk_flags: list[str] | None = None,
    caveats: list[str] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": OBSERVATION_SCHEMA_VERSION,
        "symbol": symbol,
        "display_symbol": display_symbol or symbol,
        "category_id": category_id,
        "instrument_type": instrument_type,
        "status": status,
        "source": source,
        "adapter_id": adapter_id,
        "market": market,
        "source_type": source_type,
        "price_like_value": price_like_value,
        "value": value if value is not None else price_like_value,
        "price_semantics": price_semantics,
        "source_timestamp": source_timestamp,
        "retrieved_at_utc": retrieved_at_utc,
        "freshness_assessment": freshness_assessment,
        "delay_status": delay_status,
        "delay_seconds": delay_seconds,
        "staleness_seconds": delay_seconds,
        "reference_only": reference_only,
        "contract": contract,
        "contract_month": contract_month,
        "contract_selector": contract_selector,
        "data_quality_flags": sorted(set(data_quality_flags or [])),
        "source_risk_flags": sorted(set(source_risk_flags or [])),
        "caveats": sorted(set(caveats or [])),
    }
    if extra:
        payload.update(extra)
    return payload


def normalize_failure(
    *,
    symbol: str,
    source: str | None,
    adapter_id: str | None,
    reason: str,
    status: str = "failed",
    stage: str = "observation",
    investigation_summary: dict[str, Any] | None = None,
    recommended_next_step: str | None = None,
    retryable: bool | None = None,
    caveats: list[str] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": FAILURE_SCHEMA_VERSION,
        "symbol": symbol,
        "source": source,
        "adapter_id": adapter_id,
        "status": status,
        "reason": reason,
        "stage": stage,
        "investigation_summary": investigation_summary,
        "recommended_next_step": recommended_next_step,
        "retryable": retryable,
        "caveats": sorted(set(caveats or [])),
    }
    if extra:
        payload.update(extra)
    return payload


def normalize_twse_mis_row(item: dict[str, Any], instrument: dict[str, Any], retrieved_at_utc: str, *, caveats: list[str] | None = None) -> dict[str, Any]:
    from scripts.m5k_common import _select_mis_price  # shared legacy parser, not duplicate semantics

    symbol = instrument["symbol"]
    price, price_source_field = _select_mis_price(item)
    raw_ts = item.get("tlong") or (f"{item.get('d')} {item.get('t')}" if item.get("d") and item.get("t") else None)
    ts = normalize_timestamp(raw_ts, retrieved_at_utc=retrieved_at_utc, source_timezone=timezone(timedelta(hours=8)))
    flags = list(ts["flags"])
    if item.get("z") in (None, "", "-"):
        flags.append("missing_z")
    if item.get("t") in (None, "", "-") and item.get("tlong") in (None, "", "-"):
        flags.append("missing_t")
    if item.get("d") in (None, "", "-") and item.get("tlong") in (None, "", "-"):
        flags.append("missing_d")
    if price_source_field == "z":
        status = "ok"
        price_semantics = "last_or_current_quote_as_reported_by_source"
        reference_only = False
    elif price_source_field == "y":
        status = "reference_value_only"
        price_semantics = "previous_close_or_reference_fallback_not_current_trade"
        reference_only = True
        flags.append("current_z_unavailable_used_y_reference")
    else:
        status = "value_unavailable"
        price_semantics = "value_unavailable_no_numeric_z_or_y"
        reference_only = False
        flags.append("missing_price")
    risk = ["unofficial_source_risk", "fragile_frontend_contract", "not_official_realtime_api"]
    observation = normalize_observation(
        symbol=symbol,
        display_symbol=instrument.get("display_symbol", symbol),
        category_id=instrument.get("category_id"),
        instrument_type=instrument.get("instrument_type"),
        status=status,
        source="TWSE_MIS",
        adapter_id=instrument.get("adapter_id") or ("twse_mis_taiex_index_quote" if symbol == "TAIEX" or instrument.get("instrument_type") == "index" else "twse_mis_equity_etf_quote"),
        market=instrument.get("market"),
        source_type="official_browser_json_endpoint_candidate",
        price_like_value=price,
        price_semantics=price_semantics,
        source_timestamp=ts["source_timestamp"],
        retrieved_at_utc=retrieved_at_utc,
        freshness_assessment="current observation candidate; realtime status not guaranteed by M5K",
        delay_status="not_realtime_guaranteed",
        delay_seconds=ts["delay_seconds"],
        reference_only=reference_only,
        data_quality_flags=flags,
        source_risk_flags=risk,
        caveats=(caveats or []) + risk,
        extra={"price_source_field": price_source_field},
    )
    return attach_twse_mis_rich_facts_from_row(observation, item)


def normalize_taifex_row(item: dict[str, Any], instrument: dict[str, Any], retrieved_at_utc: str, *, caveats: list[str] | None = None) -> dict[str, Any]:
    from scripts.m5k_common import _parse_taifex_price, _taifex_contract_month, _taifex_timestamp

    raw_price = item.get("CLastPrice") or item.get("SettlementPrice") or item.get("CRefPrice")
    value = _parse_taifex_price(raw_price)
    source_ts = _taifex_timestamp(str(item.get("CDate") or ""), str(item.get("CTime") or ""))
    normalized_ts = normalize_timestamp(source_ts, retrieved_at_utc=retrieved_at_utc) if source_ts else {"source_timestamp": None, "delay_seconds": None, "flags": ["source_time_unavailable"]}
    flags = list(normalized_ts["flags"])
    if item.get("CLastPrice") in (None, "", "-"):
        flags.append("missing_last_price")
    if raw_price not in (None, "", "-") and value is None:
        flags.append("invalid_numeric_field")
    if item.get("CDate") in (None, "", "-") or item.get("CTime") in (None, "", "-"):
        flags.append("source_time_unavailable")
    status_text = str(item.get("Status") or "").lower()
    freshness = normalize_freshness(normalized_ts["delay_seconds"])
    if "close" in status_text or "closed" in status_text:
        freshness = "stale_or_closed_session"
        flags.append("stale_or_closed_session")
    return normalize_observation(
        symbol=instrument["symbol"],
        display_symbol=instrument.get("display_symbol", instrument["symbol"]),
        category_id=instrument.get("category_id"),
        instrument_type=instrument.get("instrument_type"),
        status="ok" if value is not None else "missing_value",
        source="TAIFEX",
        adapter_id="taifex_mis_tx_futures_quote",
        market="taifex",
        source_type="official_browser_json_endpoint",
        price_like_value=value,
        price_semantics="last_trade_price_or_settlement_fallback_as_reported_by_taifex_mis",
        source_timestamp=source_ts or normalized_ts["source_timestamp"],
        retrieved_at_utc=retrieved_at_utc,
        freshness_assessment=freshness,
        delay_status="delay_seconds_measured_from_source_timestamp_not_exchange_realtime_sla",
        delay_seconds=normalized_ts["delay_seconds"],
        contract=item.get("SymbolID"),
        contract_month=_taifex_contract_month(item),
        contract_selector=instrument.get("contract_selector", "front_month"),
        data_quality_flags=flags,
        caveats=caveats or [],
        extra={"source_status": item.get("Status"), "normalization": {"product_code": "TXF", "selector": "front_month", "source_contract_symbol": item.get("SymbolID"), "source_display_name": item.get("DispEName")}},
    )
