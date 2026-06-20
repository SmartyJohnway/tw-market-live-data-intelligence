# TWSE OpenAPI Normalized EOD Quote Contract (Draft v1)

## Overview
This document specifies the standard schema mapping for normalizing an End-of-Day (EOD) quote from the TWSE OpenAPI (`STOCK_DAY_ALL` endpoint).

## Contract Definition

The normalized object is embedded within the `normalized_sample` block of the standard probe data envelope.

### Status and Metadata Constants
- `source`: `"TWSE_OpenAPI"`
- `source_type`: `"official_openapi"`
- `official_status`: `"official_public_openapi"`
- `market`: `"TWSE"`
- `exchange`: `"TWSE"`
- `freshness_status`: `"eod_batch"`
- `delay_status`: `"eod"`
- `coverage_status`: `"observed_supported"`
- `currency`: `"TWD"`

### Standard Normalized Fields

| Normalized Field | TWSE Raw Field | Type | Parsing Rule |
| :--- | :--- | :--- | :--- |
| `symbol` | `Code` | String | Trimmed. Add `missing_symbol` flag if empty. |
| `name` | `Name` | String | Trimmed. Add `missing_name` flag if empty. |
| `trade_date` | `Date` | String / `None` | If missing/empty, evaluate to `None` and add `missing_trade_date` to flags. |
| `open` | `OpeningPrice` | Float / `None` | Parse via safe numeric helper. |
| `high` | `HighestPrice` | Float / `None` | Parse via safe numeric helper. |
| `low` | `LowestPrice` | Float / `None` | Parse via safe numeric helper. |
| `close` | `ClosingPrice` | Float / `None` | Parse via safe numeric helper. Add `missing_close` or `malformed_close` flags if parsing yields `None`. |
| `change` | `Change` | Float / `None` | Parse via safe numeric helper. |
| `trade_volume` | `TradeVolume` | Integer / `None` | Parse via safe numeric helper. |
| `trade_value` | `TradeValue` | Float / `None` | Parse via safe numeric helper. |
| `transaction_count` | `Transaction` | Integer / `None` | Parse via safe numeric helper. |

### Data Quality & Risk Flags

**Required Source Risk Flags:**
```json
[
  "official_eod_reference_source",
  "not_intraday_live_feed",
  "not_execution_grade",
  "public_endpoint_rate_limits_apply",
  "schema_drift_possible"
]
```

**Data Quality Flags (Conditionally added based on row parsing):**
- `missing_trade_date`: The endpoint did not provide a `Date` field for this row.
- `missing_symbol`: The `Code` field was missing or empty.
- `missing_name`: The `Name` field was missing or empty.
- `missing_close`: `ClosingPrice` was explicitly empty or missing.
- `malformed_close`: `ClosingPrice` existed but failed safe numeric parsing.
- (Additional flags e.g., `missing_open`, `malformed_open` can be implemented similarly per M2D-02 requirements).

### Mandatory Preservation Keys

- `raw_row`: Must contain the exact, unmodified JSON dictionary object received from the endpoint for the current asset.
- `unmapped_raw_fields`: Must contain a dictionary of any fields present in `raw_row` that are not explicitly mapped to the standard normalized schema above.
- `retrieved_at_utc`: Standard ISO-8601 string populated by the probe execution wrapper.

### Safe Parsing Rules
- Do not impute prices or volumes.
- Empty string, `"-"`, `"--"`, `"---"` and `None` should evaluate to Python `None`.
- Commas (e.g., `"1,000"`) should be stripped before float conversion.
- Do not throw exceptions from malformed rows. Catch standard parsing exceptions and assign `None` with a matching `malformed_<field>` flag.
