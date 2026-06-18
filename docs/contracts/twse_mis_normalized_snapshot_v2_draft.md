# TWSE MIS Normalized Snapshot v2 Contract (Draft)

**STATUS:** Draft for M2B-02. **Not fully implemented in M2B-01.**

## 1. Overview
This document defines the target normalized data contract for the TWSE MIS data source. The goal is to provide a standardized, strongly-typed Python dictionary/JSON structure that downstream AI agents can reliably interpret, abstracting away the esoteric, single-letter field names of the raw TWSE MIS response.

## 2. Scope and Non-Scope
**In Scope:**
- Mapping core identity, price, volume, and bid/ask fields.
- Defining standard timestamp fields and derived freshness metrics.
- Handling `-` (missing) values safely (converting to `None` or appropriate types).
- Handling the string-based, underscore-separated bid/ask arrays.

**Non-Scope:**
- This contract does not guarantee the data is officially real-time.
- This contract does not support high-frequency polling.
- This contract does not parse obscure or unconfirmed post-market fields (`oa`, `ob`, etc.) unless fully understood.

## 3. Normalized Field Table
| Normalized Field | Type | Description |
| :--- | :--- | :--- |
| `symbol` | `str` | The core ticker symbol (e.g., "2330"). |
| `exchange` | `str` | The exchange identifier ("tse" or "otc"). |
| `name` | `str` | The short name of the asset. |
| `channel` | `str` | The source channel identifier (e.g., "tse_2330.tw"). |
| `last_price` | `float \| None` | The last traded price. |
| `previous_close` | `float \| None` | The previous trading day's closing price. |
| `open` | `float \| None` | The opening price. |
| `high` | `float \| None` | The highest price of the session. |
| `low` | `float \| None` | The lowest price of the session. |
| `change` | `float \| None` | The absolute price change from `previous_close`. |
| `change_pct` | `float \| None` | The percentage price change. |
| `cumulative_volume` | `int \| None` | Total volume traded in the session. |
| `current_volume` | `int \| None` | Volume of the last trade. |
| `bid_prices` | `list[float]` | Top 5 bid prices. |
| `bid_volumes` | `list[int]` | Volumes for the top 5 bid prices. |
| `ask_prices` | `list[float]` | Top 5 ask prices. |
| `ask_volumes` | `list[int]` | Volumes for the top 5 ask prices. |
| `limit_up` | `float \| None` | The limit up price. |
| `limit_down` | `float \| None` | The limit down price. |
| `source_date` | `str` | The trading date (YYYYMMDD). |
| `source_time` | `str` | The source-reported time (HH:MM:SS). |
| `source_time_ms` | `int` | Epoch timestamp from the source. |
| `source_datetime_taipei` | `str` | Combined date/time localized to Taipei. |
| `retrieved_at_utc` | `str` | ISO8601 timestamp of when the probe executed. |
| `retrieved_at_taipei` | `str` | ISO8601 timestamp localized to Taipei. |
| `staleness_seconds` | `int \| None` | Derived age of the data. |
| `freshness_status` | `str` | e.g., "realtime_candidate", "delayed", "stale". |
| `delay_status` | `str` | Derived delay categorization. |
| `data_quality_flags` | `list[str]` | Flags for missing data (e.g., `["missing_last_price", "missing_bid_ask"]`). |
| `source_risk_flags` | `list[str]` | Caveats (e.g., `["unofficial_endpoint", "observed_contract"]`). |

## 4. Raw-to-Normalized Mapping Table
- `c` -> `symbol`
- `ex` -> `exchange`
- `n` -> `name`
- `ch` -> `channel`
- `z` -> `last_price` (requires `-` check)
- `y` -> `previous_close`
- `o` -> `open` (requires `-` check)
- `h` -> `high` (requires `-` check)
- `l` -> `low` (requires `-` check)
- `v` -> `cumulative_volume`
- `tv` -> `current_volume` (requires `-` check)
- `b` -> `bid_prices` (requires string split)
- `g` -> `bid_volumes` (requires string split)
- `a` -> `ask_prices` (requires string split)
- `f` -> `ask_volumes` (requires string split)
- `u` -> `limit_up`
- `w` -> `limit_down`
- `d` -> `source_date`
- `t` -> `source_time`
- `tlong` -> `source_time_ms`

## 5. Example JSON Object (Illustrative Only)

*Note: This is a target contract for M2B-02 and is not fully implemented in M2B-01.*

```json
{
  "symbol": "2330",
  "exchange": "tse",
  "name": "台積電",
  "channel": "tse_2330.tw",
  "last_price": 1050.0,
  "previous_close": 1040.0,
  "open": 1045.0,
  "high": 1055.0,
  "low": 1040.0,
  "change": 10.0,
  "change_pct": 0.96,
  "cumulative_volume": 15000,
  "current_volume": 5,
  "bid_prices": [1050.0, 1045.0, 1040.0, 1035.0, 1030.0],
  "bid_volumes": [150, 250, 350, 450, 550],
  "ask_prices": [1055.0, 1060.0, 1065.0, 1070.0, 1075.0],
  "ask_volumes": [100, 200, 300, 400, 500],
  "limit_up": 1140.0,
  "limit_down": 936.0,
  "source_date": "20241025",
  "source_time": "13:30:00",
  "source_time_ms": 1729834200000,
  "source_datetime_taipei": "2024-10-25 13:30:00",
  "retrieved_at_utc": "2024-10-25T05:30:05Z",
  "retrieved_at_taipei": "2024-10-25T13:30:05+08:00",
  "staleness_seconds": 5,
  "freshness_status": "realtime_candidate",
  "delay_status": "realtime",
  "data_quality_flags": [],
  "source_risk_flags": [
    "unofficial_endpoint",
    "observed_contract",
    "not_official_realtime_api"
  ]
}
```

## 6. Data Quality Flags
If parsing encounters `"-"` for critical fields (like `z` or `tv`), or if bid/ask arrays are missing (such as in index rows like `t00.tw`), the normalizer should inject flags into `data_quality_flags` (e.g., `"missing_last_price"`, `"missing_bid_ask"`). This allows AI agents to cleanly understand why data is null without crashing.

## 7. Session-Dependent Caveats
The normalizer must gracefully handle the difference between intraday and post-market data.
- Intraday `"-"` values should result in `None` types for floats/ints.
- The normalizer should not crash if post-market fields (`oa`, `ob`) are present but unhandled; it should simply ignore them or place them in an `unmapped_raw_fields` dictionary if strict retention is desired.

## 8. Deferred Implementation Notes for M2B-02
- Implement the actual Python logic in `probe_twse_mis.py` to output this `normalized_sample`.
- Add unit tests validating the parsing of `"-"` values.
- Add unit tests validating the string-splitting logic for bid/ask arrays.
- Add unit tests demonstrating safe handling of index rows (`t00.tw`) lacking bid/ask data.
