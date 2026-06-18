# Yahoo Finance Normalized Chart Contract v1

## 1. Overview
This document defines the normalized shape for a successfully parsed Yahoo Finance chart response. Due to the unofficial nature of the Yahoo Finance endpoint, responses are subject to missing arrays, missing fields, or empty results. This contract enforces a strict, predictable JSON shape to ensure downstream consumers (such as AI contexts or offline reports) do not fail when Yahoo data is structurally degraded.

## 2. General Principles
1. **No Imputation:** Missing values (`None` or `null`) inside an array remain `None`. The system does not impute missing prices, nor does it forward-fill them.
2. **Predictable Types:** The `series` object will always contain keys for required arrays, even if the payload lacks them. Missing arrays are stored as empty lists (`[]`), and a corresponding flag is added to `data_quality_flags`.
3. **No Synthesizing Data:** Array mismatch lengths are flagged but not silently padded or truncated.
4. **Time Conversions:** The original epoch time is captured as the source-of-truth. Derived string representations for UTC and Local time are provided for convenience.

## 3. Normalized Data Model

A successfully normalized response should align with the structure below. It is produced by the `normalize_yahoo_chart_result` helper inside `scripts/probe_yahoo.py`.

```json
{
  "symbol": "2330.TW",
  "requested_symbol": "2330.TW",
  "source": "Yahoo_Finance",
  "source_type": "unofficial_api",
  "currency": "TWD",
  "exchange_name": "TAI",
  "exchange_timezone_name": "Asia/Taipei",
  "gmtoffset": 28800,
  "regular_market_price": 950.0,
  "regular_market_time": 1781760608,
  "regular_market_time_utc": "2026-06-18T13:13:28+00:00",
  "regular_market_time_local": "2026-06-18T21:13:28+08:00",
  "chart_range": "1d",
  "data_granularity": "1m",
  "valid_ranges": ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"],
  "first_trade_date": 946944000,
  "retrieved_at_utc": "2026-06-18T13:14:00+00:00",
  "staleness_seconds": 32,
  "freshness_status": "realtime_candidate",
  "delay_status": "realtime",
  "source_risk_flags": [
    "unofficial_source",
    "rate_limits_apply",
    "no_execution_guarantees"
  ],
  "data_quality_flags": [
    "missing_adjclose_array"
  ],
  "coverage_status": "observed_supported",
  "series": {
    "timestamps": [1781744400, 1781744460],
    "timestamps_utc": ["2026-06-18T09:00:00+00:00", "2026-06-18T09:01:00+00:00"],
    "timestamps_local": ["2026-06-18T17:00:00+08:00", "2026-06-18T17:01:00+08:00"],
    "open": [945.0, 946.0],
    "high": [948.0, 946.0],
    "low": [945.0, 945.0],
    "close": [948.0, 945.0],
    "volume": [123000, 50000],
    "adjclose": []
  },
  "raw_meta": {
    "symbol": "2330.TW",
    "regularMarketPrice": 950.0,
    "regularMarketTime": 1781760608
    ...
  },
  "unmapped_meta_fields": {
    "currentTradingPeriod": { ... },
    "instrumentType": "EQUITY"
  }
}
```

## 4. Field Descriptions

### Top-Level Fields
*   **symbol**: The ticker symbol reported by Yahoo's meta block.
*   **requested_symbol**: The requested symbol argument.
*   **source**: `Yahoo_Finance`
*   **source_type**: `unofficial_api`
*   **currency**: The traded currency (e.g., `TWD`).
*   **exchange_name**: The name of the exchange (e.g., `TAI`, `TWO`).
*   **exchange_timezone_name**: The standard timezone name reported by Yahoo (e.g., `Asia/Taipei`).
*   **gmtoffset**: GMT offset in seconds. Used for string conversion.
*   **regular_market_price**: Most recent regular market price float.
*   **regular_market_time**: Most recent regular market time (epoch).
*   **regular_market_time_utc**: Derived UTC ISO-8601 string of the market time.
*   **regular_market_time_local**: Derived local timezone ISO-8601 string of the market time.
*   **chart_range**: The range constraint of the request (e.g., `1d`).
*   **data_granularity**: The interval constraint of the returned series (e.g., `1m`).
*   **valid_ranges**: Array of ranges supported by the endpoint.
*   **first_trade_date**: The earliest known trading date (epoch).
*   **retrieved_at_utc**: ISO-8601 string reflecting when the parser was invoked.
*   **staleness_seconds**: Calculated difference between `retrieved_at_utc` and `regular_market_time`.
*   **freshness_status**: The assessed freshness of the data (`realtime_candidate`, `delayed_candidate`, `stale`).
*   **delay_status**: Contextual descriptor (`realtime`, `delayed`, `stale`, `unknown`).
*   **source_risk_flags**: Warnings associated with the unofficial source.
*   **data_quality_flags**: An array listing structural or data anomalies.
*   **coverage_status**: Target coverage categorization (e.g., `observed_supported`).

### Series Data (`series`)
The `series` object contains parallel arrays representing a time series.
*   **timestamps**: Raw epoch times.
*   **timestamps_utc**: Derived UTC ISO-8601 strings.
*   **timestamps_local**: Derived Local ISO-8601 strings using `gmtoffset`.
*   **open**, **high**, **low**, **close**, **volume**: OHLCV float values.
*   **adjclose**: Adjusted close prices. Will be an empty list `[]` if the response does not include it.

### Meta Data
*   **raw_meta**: The original dictionary of the Yahoo chart `meta` payload.
*   **unmapped_meta_fields**: Any keys within `meta` that are not explicitly documented as part of the core parsed top-level fields in this document.

## 5. Standard Data Quality Flags
If an anomaly is detected, the `data_quality_flags` list should contain one or more of the following standard string flags:

*   `missing_meta`
*   `missing_regular_market_time`
*   `missing_timestamp_array`
*   `missing_quote_block`
*   `missing_open_array`
*   `missing_high_array`
*   `missing_low_array`
*   `missing_close_array`
*   `missing_volume_array`
*   `missing_adjclose_array`
*   `timestamp_quote_length_mismatch`
*   `timestamp_adjclose_length_mismatch`
*   `malformed_timestamp`
*   `malformed_regular_market_time`
*   `missing_gmtoffset_for_local_time`
*   `empty_chart_result`
*   `chart_error_present`
