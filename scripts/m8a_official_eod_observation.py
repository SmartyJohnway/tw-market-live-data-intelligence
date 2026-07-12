"""M8A official EOD normalized observation helpers.

Pure helpers: no network, no filesystem writes, and no raw source payload
retention. Prices are normalized as Decimal-compatible strings, never floats.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

SCHEMA_VERSION = "m8a_official_eod_observation.v1"
ADAPTER_RESULT_SCHEMA_VERSION = "m8a_official_eod_adapter_result.v1"
ALLOWED_MARKETS = {"listed", "tpex_otc"}
ALLOWED_SOURCES = {"TWSE_OPENAPI", "TPEX_OPENAPI"}
PRICE_FIELDS = ("open", "high", "low", "close", "previous_close", "change", "change_percent")
ACTIVITY_FIELDS = ("trade_volume", "trade_value", "transaction_count")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_roc_yyyymmdd(value: Any) -> tuple[str | None, dict]:
    if not isinstance(value, str) or len(value) != 7 or not value.isdigit():
        return None, {"valid": False, "reason": "roc_date_must_be_7_digits"}
    try:
        parsed = date(int(value[:3]) + 1911, int(value[3:5]), int(value[5:7]))
    except ValueError as exc:
        return None, {"valid": False, "reason": f"invalid_roc_date:{exc}"}
    return parsed.isoformat(), {"valid": True, "source_format": "ROC_YYYMMDD"}


def parse_decimal_text(value: Any, *, allow_negative: bool = False) -> tuple[str | None, dict]:
    if value in (None, "", "--", "---", "N/A"):
        return None, {"valid": False, "reason": "missing"}
    if not isinstance(value, str):
        value = str(value)
    text = value.strip().replace(",", "")
    if text.startswith("+"):
        text = text[1:]
    try:
        dec = Decimal(text)
    except (InvalidOperation, ValueError):
        return None, {"valid": False, "reason": "invalid_decimal"}
    if not allow_negative and dec < 0:
        return None, {"valid": False, "reason": "negative_not_allowed"}
    return format(dec, "f"), {"valid": True, "numeric_type": "decimal_string"}


def parse_int_text(value: Any) -> tuple[int | None, dict]:
    if value in (None, "", "--", "---", "N/A"):
        return None, {"valid": False, "reason": "missing"}
    if not isinstance(value, str):
        value = str(value)
    text = value.strip().replace(",", "")
    if not text.isdigit():
        return None, {"valid": False, "reason": "invalid_integer"}
    integer = int(text)
    if integer < 0:
        return None, {"valid": False, "reason": "negative_not_allowed"}
    return integer, {"valid": True, "numeric_type": "integer"}


def _identity_validation(market: str, symbol: str) -> dict:
    return {"valid": market in ALLOWED_MARKETS and isinstance(symbol, str) and bool(symbol.strip()), "market": market, "symbol_present": bool(isinstance(symbol, str) and symbol.strip())}


def create_observation(*, source_id: str, endpoint_contract_id: str, market: str, symbol: str, name: str | None, instrument_type: str = "unknown", trade_date: str | None, retrieved_at_utc: str | None = None, source_status: str = "ok", price: dict | None = None, activity: dict | None = None, field_validation: dict | None = None, source_fields_present: list | None = None, omitted_source_fields: list | None = None, derived_fields: list | None = None, caveats: list | None = None, provenance: dict | None = None) -> dict:
    field_validation = dict(field_validation or {})
    field_validation["identity"] = _identity_validation(market, symbol)
    try:
        date.fromisoformat(trade_date or "")
        date_valid = True
    except ValueError:
        date_valid = False
    field_validation["trade_date"] = {"valid": date_valid}
    price_out = {k: None for k in PRICE_FIELDS}
    for k, v in (price or {}).items():
        if k in price_out:
            price_out[k] = v
    activity_out = {k: None for k in ACTIVITY_FIELDS}
    for k, v in (activity or {}).items():
        if k in activity_out:
            activity_out[k] = v
    valid_required = field_validation["identity"]["valid"] and date_valid
    factual_count = sum(v is not None for v in price_out.values()) + sum(v is not None for v in activity_out.values())
    status = "complete" if valid_required and factual_count >= 4 else ("partial" if valid_required else "invalid")
    return {
        "schema_version": SCHEMA_VERSION,
        "source_id": source_id,
        "endpoint_contract_id": endpoint_contract_id,
        "authority_level": "official_documented",
        "timing_class": "official_eod",
        "market": market,
        "symbol": symbol,
        "name": name,
        "instrument_type": instrument_type or "unknown",
        "trade_date": trade_date,
        "retrieved_at_utc": retrieved_at_utc or utc_now(),
        "source_status": source_status,
        "observation_status": status,
        "currency": "TWD",
        "price": price_out,
        "activity": activity_out,
        "field_validation": field_validation,
        "source_fields_present": list(source_fields_present or []),
        "omitted_source_fields": list(omitted_source_fields or []),
        "derived_fields": list(derived_fields or []),
        "caveats": list(caveats or []),
        "provenance": dict(provenance or {}),
    }


def observation_to_context_observation(obs: dict, *, currentness_status: str | None = None) -> dict:
    if obs.get("instrument_type") == "unknown":
        caveats = list(obs.get("caveats") or []) + ["unclassified instrument excluded from AI context by default"]
        safe_fields = {}
    else:
        caveats = list(obs.get("caveats") or [])
        safe_fields = {"trade_date": obs.get("trade_date"), "currentness_status": currentness_status, "price": obs.get("price"), "activity": obs.get("activity"), "field_validation": obs.get("field_validation"), "derived_fields": obs.get("derived_fields")}
    context_type = "official_market_eod_reference"
    if obs.get("instrument_type") == "equity":
        context_type = "official_equity_eod_reference"
    elif obs.get("instrument_type") == "etf":
        context_type = "official_etf_eod_reference"
    return {"source_id": obs.get("source_id"), "source_family": obs.get("source_id"), "symbol": obs.get("symbol"), "name": obs.get("name"), "market": obs.get("market"), "instrument_type": obs.get("instrument_type"), "context_type": context_type, "retrieved_at_utc": obs.get("retrieved_at_utc"), "market_date": obs.get("trade_date"), "trading_date": obs.get("trade_date"), "safe_fields": safe_fields, "omitted_fields": obs.get("omitted_source_fields", []), "caveats": caveats}


def empty_adapter_result(source_id: str, endpoint_contract_id: str, requested_symbols: list[str], requested_at_utc: str | None = None) -> dict:
    ts = requested_at_utc or utc_now()
    return {"schema_version": ADAPTER_RESULT_SCHEMA_VERSION, "source_id": source_id, "endpoint_contract_id": endpoint_contract_id, "requested_symbols": list(requested_symbols), "network_scope": "whole_market", "retained_scope": "bounded_requested_symbols", "requested_at_utc": ts, "completed_at_utc": ts, "http_status": None, "source_status": "not_started", "batch_status": "source_unavailable", "reported_trade_dates": [], "row_count_received": 0, "row_count_examined": 0, "row_count_retained": 0, "row_count_rejected": 0, "observations": [], "rejected_rows": [], "caveats": [], "provenance": {}}
