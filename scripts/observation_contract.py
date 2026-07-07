from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

OBSERVATION_SCHEMA_VERSION = "m5_live_observation.normalized.v1"
FAILURE_SCHEMA_VERSION = "m5_live_observation.failure.v1"


TWSE_MIS_RICH_FACTS_SCHEMA_VERSION = "m7a_twse_mis_rich_facts.v1"


def build_empty_twse_mis_rich_facts() -> dict[str, Any]:
    """Return the M7A TWSE MIS rich-facts schema without runtime population.

    M7A-02 defines the optional nested contract shape only. Runtime parsers do
    not call this helper yet, so existing M5K/M5N observation output stays
    backward compatible until a later parser task explicitly populates fields.
    """
    return {
        "schema_version": TWSE_MIS_RICH_FACTS_SCHEMA_VERSION,
        "source_id": "TWSE_MIS",
        "schema_status": "defined_not_populated_by_runtime_parser",
        "price_facts": {
            "last_price": None,
            "previous_close": None,
            "open": None,
            "high": None,
            "low": None,
            "price_source_fields": [],
            "semantic_status": "schema_defined_candidate_fields",
        },
        "volume_facts": {
            "raw_v": None,
            "raw_tv": None,
            "unit_status": "unverified",
            "semantic_status": "schema_defined_candidate_fields",
        },
        "displayed_depth_facts": {
            "bid_prices": [],
            "bid_quantities_raw": [],
            "ask_prices": [],
            "ask_quantities_raw": [],
            "best_bid": None,
            "best_ask": None,
            "ladder_source_fields": ["b", "g", "a", "f"],
            "quantity_unit_status": "unverified",
            "semantic_status": "displayed_depth_snapshot_only_schema",
        },
        "limit_or_reference_facts": {
            "limit_up": None,
            "limit_down": None,
            "raw_pz": None,
            "raw_bp": None,
            "raw_ps": None,
            "semantic_status": "schema_defined_candidate_fields",
        },
        "identity_facts": {
            "raw_c": None,
            "raw_ch": None,
            "raw_ex": None,
            "raw_name": None,
            "raw_nf": None,
            "unknown_identity_fields": {"m": None, "nu": None},
            "semantic_status": "schema_defined_candidate_fields",
        },
        "timestamp_facts": {
            "raw_d": None,
            "raw_t": None,
            "raw_tlong": None,
            "raw_percent": None,
            "raw_ot": None,
            "semantic_status": "schema_defined_candidate_fields",
        },
        "quality_facts": {
            "field_presence": {},
            "placeholder_fields": [],
            "malformed_fields": [],
            "ladder_mismatch_flags": [],
            "unit_unverified_fields": ["v", "tv", "g", "f"],
            "unknown_or_raw_only_fields": ["m", "nu"],
            "semantic_status": "schema_defined_quality_flags",
        },
        "ai_exposure_policy": {
            "safe_for_ai_context": False,
            "reason": "schema_defined_not_runtime_populated",
            "forbidden_interpretations": [
                "buy_signal",
                "sell_signal",
                "hold",
                "target_price",
                "support_resistance",
                "main_force",
                "true_liquidity",
                "order_book_truth",
                "realtime_guarantee",
            ],
        },
    }


def attach_empty_twse_mis_rich_facts(observation: Mapping[str, Any]) -> dict[str, Any]:
    """Return an observation copy with empty TWSE MIS rich facts attached.

    This opt-in helper is intentionally not called by the runtime parser in
    M7A-02. It preserves existing top-level observation fields by copying the
    input mapping before adding `twse_mis_rich_facts`.
    """
    copied = dict(observation)
    copied["twse_mis_rich_facts"] = build_empty_twse_mis_rich_facts()
    return copied


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
