# TPEx OpenAPI Normalized EOD Quote Contract (Draft v1)

## Overview
This document specifies the standard schema mapping for normalizing an End-of-Day (EOD) quote from the TPEx OpenAPI (`tpex_mainboard_daily_close_quotes` endpoint).

## Contract Definition

The normalized object is embedded within the `normalized_sample` block of the standard probe data envelope.

### Status and Metadata Constants
- `source`: `"TPEx_OpenAPI"`
- `source_type`: `"official_openapi"`
- `official_status`: `"official_public_openapi"`
- `market`: `"TPEx"`
- `exchange`: `"TPEx"`
- `freshness_status`: `"eod_batch"`
- `delay_status`: `"eod"`
- `coverage_status`: `"observed_supported"`
- `currency`: `"TWD"`

### Standard Normalized Fields

| Normalized Field | TPEx Raw Field | Type | Parsing Rule |
| :--- | :--- | :--- | :--- |
| `symbol` | `SecuritiesCompanyCode` | String | Trimmed. Add `missing_symbol` flag if empty. |
| `name` | `CompanyName` | String | Trimmed. Add `missing_name` flag if empty. |
| `trade_date` | `Date` | String / `None` | Direct string assignment. If missing, `None` + `missing_trade_date` flag. |
| `open` | `Open` | Float / `None` | Parse via safe numeric helper. |
| `high` | `High` | Float / `None` | Parse via safe numeric helper. |
| `low` | `Low` | Float / `None` | Parse via safe numeric helper. |
| `close` | `Close` | Float / `None` | Parse via safe numeric helper. Add `missing_close` / `malformed_close` flags if parsing yields `None`. |
| `change` | `Change` | Float / `None` | Parse via safe numeric helper. TPEx explicit signs (e.g., `+9.00`) should parse correctly to floats. |
| `trade_volume` | `TradingShares` | Integer / `None` | Parse via safe numeric helper. |
| `trade_value` | `TransactionAmount` | Float / `None` | Parse via safe numeric helper. |
| `transaction_count` | `TransactionNumber` | Integer / `None` | Parse via safe numeric helper. |

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
- `missing_trade_date`: `Date` was not provided.
- `missing_symbol`: `SecuritiesCompanyCode` was missing or empty.
- `missing_name`: `CompanyName` was missing or empty.
- `missing_close`: `Close` was explicitly empty or missing.
- `malformed_close`: `Close` existed but failed safe numeric parsing.
- (Additional flags e.g., `missing_open`, `malformed_open` can be implemented similarly).

### Mandatory Preservation Keys

- `raw_row`: Must contain the exact, unmodified JSON dictionary object received from the endpoint.
- `unmapped_raw_fields`: A dictionary of unmapped keys. For TPEx, this will usually include: `Average`, `LatestBidPrice`, `LatesAskPrice`, `Capitals`, `NextReferencePrice`, `NextLimitUp`, `NextLimitDown`.
- `retrieved_at_utc`: Standard ISO-8601 string populated by the probe execution wrapper.

### Safe Parsing Rules
- Do not impute prices or volumes.
- Empty string, `"-"`, `"--"`, `"---"` and `None` should evaluate to Python `None`.
- Commas (e.g., `"1,000"`) should be stripped before float conversion.
- Do not throw exceptions from malformed rows. Catch standard parsing exceptions and assign `None` with a matching `malformed_<field>` flag.
