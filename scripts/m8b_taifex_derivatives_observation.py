"""M8B TAIFEX OpenAPI derivatives normalized observation helpers.

Pure helpers: no network, no filesystem writes, no raw source payload retention.
Market numeric values are normalized as Decimal-compatible strings or integers;
Python float is intentionally not used.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

SCHEMA_VERSION = "m8b_taifex_derivatives_context_observation.v1"
ADAPTER_RESULT_SCHEMA_VERSION = "m8b_taifex_openapi_adapter_result.v1"
SOURCE_ID = "TAIFEX_OPENAPI"
AUTHORITY_LEVEL = "official_documented"
TIMING_CLASS = "official_derivatives_eod"
MISSING_MARKERS = {None, "", "-", "--", "---"}

CONTEXT_TYPES = {
    "futures": "official_derivatives_futures_eod_reference",
    "options": "official_derivatives_options_eod_reference",
    "final_settlement": "official_derivatives_final_settlement_reference",
    "large_trader_oi": "official_derivatives_large_trader_open_interest_reference",
    "put_call_ratio": "official_derivatives_put_call_ratio_reference",
    "block_trade": "official_derivatives_block_trade_reference",
}

FAILURE_STATUSES = {
    "successful_derivatives_eod_batch", "empty_non_trading_day", "source_unavailable",
    "source_error", "schema_drift", "identity_parse_failure", "date_mismatch",
    "partial_source_success", "valid_zero_trade_contract", "unresolved_session_semantics",
    "rejected_invalid_scope", "operator_confirmation_required",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_yyyymmdd(value: Any) -> tuple[str | None, dict]:
    text = str(value).strip() if value is not None else ""
    if len(text) != 8 or not text.isdigit():
        return None, {"valid": False, "reason": "date_must_be_yyyymmdd"}
    try:
        return date(int(text[:4]), int(text[4:6]), int(text[6:8])).isoformat(), {"valid": True, "source_format": "YYYYMMDD"}
    except ValueError as exc:
        return None, {"valid": False, "reason": f"invalid_date:{exc}"}


def is_missing(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value.strip() in MISSING_MARKERS)


def parse_decimal_text(value: Any, *, allow_negative: bool = False, allow_missing: bool = True) -> tuple[str | None, dict]:
    if is_missing(value):
        return None, {"valid": bool(allow_missing), "reason": "missing"}
    text = str(value).strip().replace(",", "").replace("%", "")
    if text.startswith("+"):
        text = text[1:]
    try:
        dec = Decimal(text)
    except (InvalidOperation, ValueError):
        return None, {"valid": False, "reason": "invalid_decimal"}
    if dec < 0 and not allow_negative:
        return None, {"valid": False, "reason": "negative_not_allowed"}
    return format(dec, "f"), {"valid": True, "numeric_type": "decimal_string"}


def parse_signed_decimal_text(value: Any, *, allow_missing: bool = True) -> tuple[str | None, dict]:
    return parse_decimal_text(value, allow_negative=True, allow_missing=allow_missing)


def parse_non_negative_int(value: Any, *, allow_missing: bool = True) -> tuple[int | None, dict]:
    if is_missing(value):
        return None, {"valid": bool(allow_missing), "reason": "missing"}
    text = str(value).strip().replace(",", "")
    if not text.isdigit():
        return None, {"valid": False, "reason": "invalid_integer"}
    return int(text), {"valid": True, "numeric_type": "integer"}


def map_call_put(value: Any, *, allow_not_applicable: bool = False) -> tuple[str | None, dict]:
    if is_missing(value):
        if allow_not_applicable and str(value).strip() == "-":
            return "not_applicable", {"valid": True, "source_value": value}
        return None, {"valid": False, "reason": "missing_call_put", "source_value": value}
    mapping = {"買權": "call", "賣權": "put", "call": "call", "put": "put", "C": "call", "P": "put"}
    text = str(value).strip()
    if text in mapping:
        return mapping[text], {"valid": True, "source_value": value}
    return None, {"valid": False, "reason": "unknown_call_put", "source_value": value}


def map_session(value: Any) -> tuple[str, dict, list[str]]:
    if is_missing(value):
        return "unknown", {"valid": False, "reason": "missing_session", "source_value": value}, ["session_semantics_unresolved"]
    text = str(value).strip()
    mapping = {"一般": "regular", "regular": "regular", "盤後": "after_hours", "夜盤": "after_hours"}
    if text in mapping:
        return mapping[text], {"valid": True, "source_value": value}, []
    return "unknown", {"valid": False, "reason": "unknown_session_label", "source_value": value}, ["session_semantics_unresolved"]


def validate_contract_month(value: Any, *, allow_missing: bool = False) -> tuple[str | None, dict]:
    if is_missing(value):
        return None, {"valid": bool(allow_missing), "reason": "missing_contract_month"}
    text = str(value).strip()
    ok = text.isalnum() and 4 <= len(text) <= 12
    return (text if ok else None), {"valid": ok, "reason": None if ok else "invalid_contract_month"}


def source_field_presence(row: dict, expected_fields: list[str]) -> tuple[list[str], list[str]]:
    present = [f for f in expected_fields if f in row]
    omitted = [f for f in expected_fields if f not in row]
    return present, omitted


def currentness(status: str | None = None, *, trade_date: str | None = None, caveats: list[str] | None = None) -> dict:
    return {"status": status or "currentness_not_evaluated", "trade_date": trade_date, "caveats": list(caveats or [])}


def create_observation(*, endpoint_contract_id: str, context_type: str, instrument_type: str, product_id: str | None = None, product_name: str | None = None, contract_identity: dict | None = None, aggregate_identity: dict | None = None, trade_date: str | None = None, retrieved_at_utc: str | None = None, session: str = "not_applicable", source_session_label: str | None = None, source_status: str = "ok", observation_status: str | None = None, currentness_value: dict | None = None, field_validation: dict | None = None, source_fields_present: list[str] | None = None, omitted_source_fields: list[str] | None = None, derived_fields: list[str] | None = None, caveats: list[str] | None = None, provenance: dict | None = None, payload: dict | None = None) -> dict:
    caveats = list(dict.fromkeys(list(caveats or []) + ["quotation_unit_unresolved"]))
    payload = dict(payload or {})
    valid_identity = bool(product_id or aggregate_identity or contract_identity)
    valid_date = True
    if trade_date:
        try: date.fromisoformat(trade_date)
        except ValueError: valid_date = False
    status = observation_status or ("complete" if valid_identity and valid_date else "invalid")
    return {
        "schema_version": SCHEMA_VERSION, "source_id": SOURCE_ID, "source_family": SOURCE_ID,
        "endpoint_contract_id": endpoint_contract_id, "context_type": context_type,
        "authority_level": AUTHORITY_LEVEL, "timing_class": TIMING_CLASS, "market": "taifex",
        "instrument_type": instrument_type, "product_id": product_id, "symbol": product_id,
        "product_name": product_name, "name": product_name, "contract_identity": contract_identity,
        "aggregate_identity": aggregate_identity, "trade_date": trade_date, "market_date": trade_date,
        "trading_date": trade_date, "retrieved_at_utc": retrieved_at_utc or utc_now(),
        "session": session, "source_session_label": source_session_label, "settlement_currency": None,
        "quotation_unit": "product_specific_quote_unit", "contract_multiplier": None,
        "source_status": source_status, "observation_status": status,
        "currentness": currentness_value or currentness(trade_date=trade_date),
        "field_validation": dict(field_validation or {}), "source_fields_present": list(source_fields_present or []),
        "omitted_source_fields": list(omitted_source_fields or []), "derived_fields": list(derived_fields or []),
        "caveats": caveats, "provenance": dict(provenance or {}), "payload": payload,
        "safe_fields": {"endpoint_contract_id": endpoint_contract_id, "context_type": context_type,
            "trade_date": trade_date, "currentness": currentness_value or currentness(trade_date=trade_date),
            "session": session, "source_session_label": source_session_label, "quotation_unit": "product_specific_quote_unit",
            "settlement_currency": None, "contract_multiplier": None, "contract_identity": contract_identity,
            "aggregate_identity": aggregate_identity, "payload": payload},
        "omitted_fields": list(omitted_source_fields or []),
    }


def empty_adapter_result(endpoint_contract_id: str, requested_products: list[str] | None = None) -> dict:
    ts = utc_now()
    return {"schema_version": ADAPTER_RESULT_SCHEMA_VERSION, "source_id": SOURCE_ID, "endpoint_contract_id": endpoint_contract_id,
            "requested_products": list(requested_products or []), "network_scope": "whole_endpoint", "retained_scope": "bounded_requested_scope",
            "requested_at_utc": ts, "completed_at_utc": ts, "http_status": None, "source_status": "not_started",
            "batch_status": "source_unavailable", "reported_trade_dates": [], "row_count_received": 0,
            "row_count_examined": 0, "row_count_retained": 0, "row_count_rejected": 0, "observations": [],
            "rejected_rows": [], "caveats": [], "provenance": {"raw_payload_retained": False}}
