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
    return normalize_observation(
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
