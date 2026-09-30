"""Pure, offline Phase I2 TAIFEX TX normalizer.

This module accepts caller-supplied source-shaped bytes/rows only. It contains
no transport client, clock access, cache, or persistence behavior.
"""
from __future__ import annotations

import json
import math
import re
from datetime import date
from typing import Any, Mapping


CAPABILITY_ID = "index_futures_context"
EVIDENCE_SCHEMA = "index_futures_context_evidence.v1"
SOURCE_ID = "I2-TAIFEX-DAILYMARKETREPORTFUT-OPENAPI"
SOURCE_FAMILY = "TAIFEX_DAILY_MARKET_REPORT_FUT"
SOURCE_CONTRACT_ID = "TAIFEX_DAILY_MARKET_REPORT_FUT_OPENAPI_V1"
SOURCE_ENDPOINT = "https://openapi.taifex.com.tw/v1/DailyMarketReportFut"
MAX_RESPONSE_BYTES = 2_097_152
MAX_ROOT_ROWS = 5_000
_DATE_RE = re.compile(r"^[0-9]{8}$")
_MONTH_RE = re.compile(r"^[0-9]{6}$")

_NUMERIC_FIELDS = {
    "Open": ("open", "index_point", False),
    "High": ("high", "index_point", False),
    "Low": ("low", "index_point", False),
    "Last": ("last", "index_point", False),
    "Change": ("change_points", "index_point", False),
    "%": ("change_percent", "percent", False),
    "Volume": ("volume", "contract_count", True),
    "SettlementPrice": ("settlement_price", "index_point", False),
    "OpenInterest": ("open_interest", "contract_count", True),
    "BestBid": ("best_bid", "index_point", False),
    "BestAsk": ("best_ask", "index_point", False),
}
_COMPLETE_FIELDS = {
    "open", "high", "low", "last", "change_points", "change_percent",
    "volume", "settlement_price", "open_interest",
}
_REQUIRED_KEYS = {
    "Date", "Contract", "ContractMonth(Week)", "Open", "High", "Low",
    "Last", "Change", "%", "Volume", "SettlementPrice", "OpenInterest",
    "BestBid", "BestAsk", "TradingHalt", "TradingSession",
}
_MISSING_MARKERS = {"", "-", "NULL"}


class I2SourceError(ValueError):
    """Stable, fail-closed source/selector error code."""


def _parse_source_date(value: Any) -> date | None:
    if not isinstance(value, str) or not _DATE_RE.fullmatch(value):
        return None
    try:
        return date(int(value[:4]), int(value[4:6]), int(value[6:8]))
    except ValueError:
        return None


def decode_taifex_payload(body: bytes) -> tuple[list[dict[str, Any]] | None, str | None]:
    """Decode only bounded UTF-8 JSON arrays; never accepts CSV or objects."""
    if not isinstance(body, bytes):
        return None, "source_failed:payload_not_bytes"
    if len(body) > MAX_RESPONSE_BYTES:
        return None, "source_failed:response_too_large"
    try:
        payload = json.loads(body.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, "source_failed:invalid_utf8_or_json"
    if not isinstance(payload, list):
        return None, "source_failed:root_not_array"
    if len(payload) > MAX_ROOT_ROWS:
        return None, "source_failed:too_many_rows"
    if any(not isinstance(row, Mapping) for row in payload):
        return None, "source_failed:row_not_object"
    return [dict(row) for row in payload], None


def decode_or_copy_rows(payload: bytes | list[Mapping[str, Any]]) -> tuple[list[dict[str, Any]] | None, str | None, int, str | None]:
    """Normalize an injected byte payload or already parsed fixture rows."""
    if isinstance(payload, bytes):
        rows, error = decode_taifex_payload(payload)
        return rows, error, len(payload), "application/octet-stream"
    if not isinstance(payload, list):
        return None, "source_failed:root_not_array", 0, None
    if len(payload) > MAX_ROOT_ROWS:
        return None, "source_failed:too_many_rows", 0, None
    if any(not isinstance(row, Mapping) for row in payload):
        return None, "source_failed:row_not_object", 0, None
    try:
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError):
        return None, "source_failed:fixture_rows_not_json_values", 0, None
    if len(encoded) > MAX_RESPONSE_BYTES:
        return None, "source_failed:response_too_large", len(encoded), "application/json"
    return [dict(row) for row in payload], None, len(encoded), "application/json"


def select_tx_regular_series(rows: list[Mapping[str, Any]]) -> tuple[str, str | None, date | None, dict[str, Any] | None]:
    """Select max valid Gregorian Date, then minimum unique eligible TX YYYYMM."""
    dated: list[tuple[date, Mapping[str, Any]]] = []
    for row in rows:
        parsed = _parse_source_date(row.get("Date"))
        if parsed is not None:
            dated.append((parsed, row))
    if not dated:
        return "source_failed", None, None, None
    selected_date = max(parsed for parsed, _ in dated)
    eligible: list[tuple[str, Mapping[str, Any]]] = []
    for parsed, row in dated:
        if parsed != selected_date or row.get("Contract") != "TX" or row.get("TradingSession") != "一般":
            continue
        period = row.get("ContractMonth(Week)")
        if not isinstance(period, str) or not _MONTH_RE.fullmatch(period):
            continue
        month = int(period[4:6])
        if not 1 <= month <= 12:
            continue
        eligible.append((period, row))
    if not eligible:
        return "unavailable", None, selected_date, None
    nearest = min(period for period, _ in eligible)
    bound = [row for period, row in eligible if period == nearest]
    if len(bound) != 1:
        return "binding_failed", nearest, selected_date, None
    return "selected", nearest, selected_date, dict(bound[0])


def _parse_numeric(raw: Any, *, integer: bool) -> float | int | None:
    if not isinstance(raw, str):
        raise I2SourceError("source_failed:selected_value_not_string")
    value = raw.strip()
    if value in _MISSING_MARKERS:
        return None
    if value.endswith("%"):
        value = value[:-1].strip()
    try:
        if integer:
            parsed_int = int(value)
            if str(parsed_int) != value or parsed_int < 0:
                raise ValueError
            return parsed_int
        parsed_float = float(value)
        if not math.isfinite(parsed_float):
            raise ValueError
        return parsed_float
    except (TypeError, ValueError, OverflowError):
        raise I2SourceError("source_failed:selected_numeric_malformed") from None


def _transport_fixture_metadata(
    *, http_status: int | None, content_type: str | None, response_byte_count: int,
    response_sha256: str | None, retrieved_at: str, get_count: int,
    error_code: str | None = None,
) -> dict[str, Any]:
    return {
        "http_status": http_status,
        "content_type": content_type,
        "response_byte_count": response_byte_count,
        "response_sha256": response_sha256,
        "retrieved_at": retrieved_at,
        "get_count": get_count,
        "retry_count": 0,
        "raw_payload_persisted": False,
        **({"error_code": error_code} if error_code else {}),
    }


def alignment_status(i2_status: str, trade_date: str | None, fmtqik_benchmark_date: str | None) -> str:
    """Compare only with the governed TWSE FMTQIK benchmark trade date."""
    if i2_status not in {"complete", "partial"} or not trade_date:
        return "unavailable"
    if not fmtqik_benchmark_date or not _is_iso_date(trade_date) or not _is_iso_date(fmtqik_benchmark_date):
        return "not_comparable"
    return "same_trade_date_non_simultaneous_close" if trade_date == fmtqik_benchmark_date else "different_trade_date"


def _is_iso_date(value: str) -> bool:
    try:
        return date.fromisoformat(value).isoformat() == value
    except (TypeError, ValueError):
        return False


def normalize_taifex_tx_payload(
    payload: bytes | list[Mapping[str, Any]],
    *,
    governed_retrieved_at: str,
    fmtqik_benchmark_date: str | None,
    citation_ids: list[str],
    transport: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return schema-valid normalized evidence from injected source-shaped data.

    The caller supplies timestamps, citations, and transport observations. This
    function never reads a clock, reaches a source, or writes an artifact.
    """
    rows, decode_error, byte_count, content_type = decode_or_copy_rows(payload)
    if rows is None:
        raise I2SourceError(decode_error or "source_failed:payload_invalid")
    selected_status, period, selected_date, selected_row = select_tx_regular_series(rows)
    if selected_status == "selected":
        if not _REQUIRED_KEYS.issubset(selected_row):
            selected_status = "source_failed"
            selected_row = None
        elif _parse_source_date(selected_row.get("Date")) is None:
            selected_status = "source_failed"
            selected_row = None

    market_data: dict[str, Any] = {}
    units: dict[str, str] = {}
    missing: list[str] = []
    status = selected_status
    if selected_row is not None:
        try:
            for source_key, (field, unit, integer) in _NUMERIC_FIELDS.items():
                value = _parse_numeric(selected_row[source_key], integer=integer)
                if value is None:
                    if field in {"best_bid", "best_ask"}:
                        market_data[field] = None
                        units[field] = unit
                    elif field in _COMPLETE_FIELDS:
                        missing.append(field)
                    continue
                market_data[field] = value
                units[field] = unit
        except I2SourceError:
            status = "source_failed"
            market_data, units, missing = {}, {}, []
        else:
            status = "partial" if missing else "complete"
            if status == "partial" and not any(value is not None for value in market_data.values()):
                status = "source_failed"
                market_data, units, missing = {}, {}, []

    if transport is None:
        # Fixture-only default metadata; callers exercising an end-to-end test
        # may supply explicit simulated transport fields.
        import hashlib
        digest = hashlib.sha256(payload).hexdigest() if isinstance(payload, bytes) else hashlib.sha256(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
        ).hexdigest()
        transport_obj = _transport_fixture_metadata(
            http_status=200, content_type=content_type or "application/json",
            response_byte_count=byte_count, response_sha256=digest,
            retrieved_at=governed_retrieved_at, get_count=1,
        )
    else:
        transport_obj = dict(transport)

    date_text = selected_date.isoformat() if selected_date else None
    evidence: dict[str, Any] = {
        "schema_version": EVIDENCE_SCHEMA,
        "status": status,
        "target_market": "TWSE",
        "venue": "TAIFEX",
        "product_code": "TX",
        "trading_session": "regular",
        "currentness_status": "unknown",
        "retrieved_at": governed_retrieved_at,
        "alignment_status": alignment_status(status, date_text, fmtqik_benchmark_date),
        "source": {
            "source_id": SOURCE_ID,
            "source_family": SOURCE_FAMILY,
            "source_contract_id": SOURCE_CONTRACT_ID,
            "endpoint": SOURCE_ENDPOINT,
            "authority": "official_taifex_oas_open_data",
            "dataset_id": "11319",
            "attribution_required": True,
        },
        "transport": transport_obj,
        "citation_ids": list(citation_ids),
        "caveats": ["Descriptive TAIFEX TX regular-session context only; no signal, basis, or causation interpretation."],
    }
    if transport is None:
        evidence["caveats"].append("offline fixture metadata only; no source request occurred")
    if status in {"complete", "partial"}:
        evidence.update({"contract_period": period, "trade_date": date_text, "market_data": market_data, "unit_metadata": units})
        if status == "partial":
            evidence["missing_fields"] = sorted(missing)
    elif status == "unavailable" and date_text is not None:
        evidence["trade_date"] = date_text
    elif status == "binding_failed":
        evidence.update({"contract_period": period, "trade_date": date_text})
    if status == "source_failed":
        evidence["caveats"].append("selected_source_row_failed_frozen_structural_or_numeric_validation")
    from jsonschema import Draft202012Validator, FormatChecker
    from pathlib import Path
    schema_path = Path(__file__).resolve().parents[2] / "schemas" / "index_futures_context_evidence.v1.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(evidence))
    if errors:
        raise I2SourceError("source_failed:evidence_schema_invalid")
    return evidence
