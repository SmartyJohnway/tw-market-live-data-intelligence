# TWSE OpenAPI Field Dictionary

**Endpoint:** `https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL`

This document provides a field dictionary for the official TWSE OpenAPI End-of-Day (EOD) quote response.

| Raw field name | Observed meaning | Normalized candidate name | Example value (Code: 2330) | Value type candidate | Required / optional candidate | Confidence level | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `Date` | ROC Year format trade date | `trade_date` | `1150618` | String (ROC format) | optional | observed | Recently observed in payload. 1150618 = 2026-06-18? If missing, we treat as `None`. |
| `Code` | Stock symbol code | `symbol` | `2330` | String | required | official_documented | Target symbol (stock or ETF). |
| `Name` | Stock company name | `name` | `台積電` | String | required | official_documented | Chinese name of the asset. |
| `TradeVolume` | Total trading volume (shares) | `trade_volume` | `49982610` | Numeric (parsed) | optional | official_documented | Total shares traded in the session. |
| `TradeValue` | Total trading value (TWD) | `trade_value` | `120198889493` | Numeric (parsed) | optional | official_documented | Total turnover in TWD. |
| `OpeningPrice` | Opening price | `open` | `2395.00` | Numeric (parsed) | optional | official_documented | EOD open price. Empty string `""` or `0` typically if no trade. |
| `HighestPrice` | Highest price | `high` | `2415.00` | Numeric (parsed) | optional | official_documented | EOD high price. |
| `LowestPrice` | Lowest price | `low` | `2385.00` | Numeric (parsed) | optional | official_documented | EOD low price. |
| `ClosingPrice` | Closing price | `close` | `2410.00` | Numeric (parsed) | optional | official_documented | EOD close price. |
| `Change` | Change from previous close | `change` | `25.0000` | Numeric (parsed) | optional | official_documented | Note: Positive/negative sign not always explicitly included; further analysis of up/down indicators may be needed (sometimes requires cross-referencing with reference prices). |
| `Transaction` | Number of transactions | `transaction_count` | `103190` | Numeric (parsed) | optional | official_documented | Total number of trades executed. |

## Notes
- **Empty Values**: Numeric fields can often be empty `""` or contain placeholder strings (e.g. `"-"`) when an asset has no trades on that day. These are parsed to `None`.
- **Trade Date**: The API historically did not include `Date`, but recently started returning it in an ROC format. We must implement a conservative check to map it to `trade_date` if present, but fallback to `None` with a `missing_trade_date` data quality flag if omitted, as schema drift is common.
- **Reference**: Official API semantics do not guarantee real-time data. This is strictly an End-of-Day (EOD) snapshot endpoint.
