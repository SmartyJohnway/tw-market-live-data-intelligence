"""Offline-only normalizers for the dormant Phase I1 market-state contract.

These functions accept already supplied source-shaped rows.  They do not
perform I/O, inspect the system clock, or convert TWSE/TPEx source units.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Sequence

from scripts.twse_trading_calendar import parse_twse_roc_date


class MarketStateNormalizationError(ValueError):
    """A source-shaped row cannot be interpreted under the frozen I1 contract."""


_TWSE_FMTQIK = {
    "source_id": "I1-TWSE-FMTQIK-OPENAPI",
    "source_family": "TWSE_EXCHANGE_REPORT_FMTQIK",
    "source_contract_id": "TWSE_FMTQIK_OPENAPI_V1",
    "url": "https://openapi.twse.com.tw/v1/exchangeReport/FMTQIK",
}
_TWSE_BREADTH = {
    "source_id": "I1-TWSE-BREADTH-TWTAZU-OPENAPI",
    "source_family": "TWSE_OPENDATA_TWTAZU",
    "source_contract_id": "TWSE_TWTAZU_OD_OPENAPI_V1",
    "url": "https://openapi.twse.com.tw/v1/opendata/twtazu_od",
}
_TPEX_HIGHLIGHT = {
    "source_id": "I1-TPEX-MAINBOARD-HIGHLIGHT-OPENAPI",
    "source_family": "TPEX_MAINBOARD_MARKET_HIGHLIGHT",
    "source_contract_id": "TPEX_MAINBORAD_HIGHLIGHT_OPENAPI_V1",
    "url": "https://www.tpex.org.tw/openapi/v1/tpex_mainborad_highlight",
}


def _date(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise MarketStateNormalizationError(f"invalid_date:{field}")
    try:
        return parse_twse_roc_date(value).isoformat()
    except (TypeError, ValueError) as exc:
        raise MarketStateNormalizationError(f"invalid_date:{field}") from exc


def _number(value: Any, field: str, *, integer: bool = False) -> int | float:
    if not isinstance(value, str) or not value.strip():
        raise MarketStateNormalizationError(f"invalid_numeric:{field}")
    try:
        parsed = Decimal(value.strip())
    except InvalidOperation as exc:
        raise MarketStateNormalizationError(f"invalid_numeric:{field}") from exc
    if not parsed.is_finite() or (integer and parsed != parsed.to_integral_value()):
        raise MarketStateNormalizationError(f"invalid_numeric:{field}")
    return int(parsed) if integer else float(parsed)


def _one_row(rows: Sequence[Mapping[str, Any]], source: str) -> Mapping[str, Any]:
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        raise MarketStateNormalizationError(f"invalid_rows:{source}")
    if len(rows) != 1 or not isinstance(rows[0], Mapping):
        raise MarketStateNormalizationError(f"expected_one_selected_row:{source}")
    return rows[0]


def _component(source: Mapping[str, str], status: str, official_date: str | None,
               observed_fields: Mapping[str, Any], units: Mapping[str, str],
               retrieved_at: str) -> dict[str, Any]:
    return {
        "status": status,
        "official_date": official_date,
        "source": {**source, "authority": "official", "retrieved_at": retrieved_at},
        "observed_fields": dict(observed_fields),
        "unit_metadata": dict(units),
    }


def normalize_twse_breadth_observation(
    row: Mapping[str, Any],
) -> tuple[str, dict[str, int], dict[str, str]]:
    """Validate and normalize one exact TWSE 股票 breadth source row.

    Kept pure so production partial-evidence handling and the complete TWSE
    normalizer share one frozen field/date/value contract.
    """
    if not isinstance(row, Mapping) or row.get("類型") != "股票":
        raise MarketStateNormalizationError("invalid_selected_breadth_row:股票")
    required = ("出表日期", "類型", "上漲", "漲停", "下跌", "跌停", "持平", "未成交", "無比價")
    for key in required:
        if key not in row:
            raise MarketStateNormalizationError(f"missing_required_field:TWTAZU:{key}")
    official_date = _date(row["出表日期"], "TWTAZU.出表日期")
    mapping = {
        "上漲": "up", "漲停": "limit_up", "下跌": "down", "跌停": "limit_down",
        "持平": "flat", "未成交": "unmatched", "無比價": "no_comparison",
    }
    values = {target: _number(row[key], f"TWTAZU.{key}", integer=True) for key, target in mapping.items()}
    if any(value < 0 for value in values.values()):
        raise MarketStateNormalizationError("invalid_numeric:TWTAZU.negative_breadth")
    units = {key: "security_count" for key in values}
    return official_date, values, units


def normalize_twse_market_state(
    fmtqik_rows: Sequence[Mapping[str, Any]],
    breadth_rows: Sequence[Mapping[str, Any]],
    *, retrieved_at: str,
) -> dict[str, Any]:
    """Normalize exact TWSE FMTQIK and 股票 breadth rows without alignment guessing."""
    fmt = _one_row(fmtqik_rows, "FMTQIK")
    for key in ("Date", "TradeVolume", "TradeValue", "TAIEX", "Change"):
        if key not in fmt:
            raise MarketStateNormalizationError(f"missing_required_field:FMTQIK:{key}")
    fmt_date = _date(fmt["Date"], "FMTQIK.Date")
    fmt_values = {
        "turnover": {
            "volume": _number(fmt["TradeVolume"], "TradeVolume", integer=True),
            "value": _number(fmt["TradeValue"], "TradeValue", integer=True),
            "transactions": _number(fmt["Transaction"], "Transaction", integer=True) if fmt.get("Transaction") not in (None, "") else None,
        },
        "benchmark": {
            "identifier": "TAIEX",
            "close_index": _number(fmt["TAIEX"], "TAIEX"),
            "change_points": _number(fmt["Change"], "Change"),
            "change_unit": "index_point",
        },
    }
    selected = [row for row in breadth_rows if isinstance(row, Mapping) and row.get("類型") == "股票"]
    if len(selected) > 1:
        raise MarketStateNormalizationError("duplicate_selected_breadth_row:股票")
    breadth = selected[0] if selected else None
    breadth_date = None
    breadth_values: dict[str, int] = {}
    breadth_status = "missing"
    if breadth is not None:
        breadth_date, breadth_values, _breadth_units = normalize_twse_breadth_observation(breadth)
        breadth_status = "available"
    aligned = breadth is not None and breadth_date == fmt_date
    status = "complete" if aligned else "partial"
    caveats = []
    if breadth is None:
        caveats.append("twse_stock_breadth_row_missing; no 整體市場 fallback used")
    elif not aligned:
        caveats.append("twse_component_official_dates_mismatch; dates preserved without alignment")
    return {
        "schema_version": "market_state_context_evidence.v1",
        "status": status,
        "market": "TWSE",
        "trade_date": fmt_date,
        "currentness_status": "unknown",
        "retrieved_at": retrieved_at,
        "benchmark": fmt_values["benchmark"],
        "turnover": {**fmt_values["turnover"], "volume_unit": "share", "value_unit": "TWD", "transactions_unit": "transaction"},
        "breadth": breadth_values if breadth is not None else {},
        "breadth_unit": "security_count",
        "source_unit_metadata": {
            "I1-TWSE-FMTQIK-OPENAPI": {"turnover.volume":"share", "turnover.value":"TWD", "turnover.transactions":"transaction", "benchmark.close_index":"index_point", "benchmark.change_points":"index_point"},
            "I1-TWSE-BREADTH-TWTAZU-OPENAPI": dict(_breadth_units) if breadth is not None else {},
        },
        "components": {
            "fmtqik": _component(_TWSE_FMTQIK, "available", fmt_date, fmt_values, {"turnover.volume":"share", "turnover.value":"TWD", "turnover.transactions":"transaction", "benchmark.close_index":"index_point", "benchmark.change_points":"index_point"}, retrieved_at),
            "breadth": _component(_TWSE_BREADTH, breadth_status, breadth_date, breadth_values, dict(_breadth_units) if breadth is not None else {}, retrieved_at),
        },
        "citation_ids": [],
        "caveats": caveats,
    }


def normalize_tpex_market_state(rows: Sequence[Mapping[str, Any]], *, retrieved_at: str) -> dict[str, Any]:
    """Normalize one exact TPEx mainboard highlight row, retaining source units."""
    row = _one_row(rows, "TPEX_MAINBOARD_HIGHLIGHT")
    required = ("Date", "DailyTradingValue", "DailyTradingVolume", "CloseIndex", "IndexChange", "PriceRiseCompanyNumbers", "LimitUpCompanyNumbers", "PriceDeclineCompanyNumbers", "LimitDownCompanyNumbers", "PriceFlatCompanyNumbers", "UnmatchedCompanyNumbersSuspensionStocksIncluded")
    for key in required:
        if key not in row:
            raise MarketStateNormalizationError(f"missing_required_field:TPEX:{key}")
    trade_date = _date(row["Date"], "TPEX.Date")
    value = _number(row["DailyTradingValue"], "DailyTradingValue")
    volume = _number(row["DailyTradingVolume"], "DailyTradingVolume")
    close = _number(row["CloseIndex"], "CloseIndex")
    change = _number(row["IndexChange"], "IndexChange")
    breadth_mapping = {
        "PriceRiseCompanyNumbers":"up", "LimitUpCompanyNumbers":"limit_up",
        "PriceDeclineCompanyNumbers":"down", "LimitDownCompanyNumbers":"limit_down",
        "PriceFlatCompanyNumbers":"flat", "UnmatchedCompanyNumbersSuspensionStocksIncluded":"unmatched_including_suspended",
    }
    breadth = {target: _number(row[key], key, integer=True) for key, target in breadth_mapping.items()}
    observed = {"trade_date": trade_date, "turnover.value":value, "turnover.volume":volume, "benchmark.close_index":close, "benchmark.change_points":change, **{f"breadth.{k}":v for k,v in breadth.items()}}
    units = {"turnover.value":"TWD_million", "turnover.volume":"thousand_share", "benchmark.close_index":"index_point", "benchmark.change_points":"index_point", **{f"breadth.{key}":"company_count" for key in breadth}}
    return {
        "schema_version": "market_state_context_evidence.v1",
        "status": "complete", "market": "TPEX", "trade_date": trade_date,
        "currentness_status": "unknown", "retrieved_at": retrieved_at,
        "benchmark": {"identifier":"TPEx Mainboard Index", "close_index":close, "change_points":change, "change_unit":"index_point"},
        "turnover": {"value":value, "value_unit":"TWD_million", "volume":volume, "volume_unit":"thousand_share"},
        "breadth": breadth, "breadth_unit":"company_count",
        "source_unit_metadata": {"I1-TPEX-MAINBOARD-HIGHLIGHT-OPENAPI": units},
        "components": {"tpex_mainborad_highlight": _component(_TPEX_HIGHLIGHT, "available", trade_date, observed, units, retrieved_at)},
        "citation_ids": [], "caveats": [],
    }


def assemble_market_state_context(
    market: str,
    *,
    retrieved_at: str,
    twse_fmtqik_rows: Sequence[Mapping[str, Any]] = (),
    twse_breadth_rows: Sequence[Mapping[str, Any]] = (),
    tpex_highlight_rows: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Dispatch supplied source rows to the deterministic market normalizer.

    This is a pure selector, not a source client: rows are supplied by the
    caller and unsupported markets fail closed without producing evidence.
    """
    if market == "TWSE":
        return normalize_twse_market_state(
            twse_fmtqik_rows, twse_breadth_rows, retrieved_at=retrieved_at
        )
    if market == "TPEX":
        return normalize_tpex_market_state(
            tpex_highlight_rows, retrieved_at=retrieved_at
        )
    raise MarketStateNormalizationError(f"unsupported_market:{market}")
