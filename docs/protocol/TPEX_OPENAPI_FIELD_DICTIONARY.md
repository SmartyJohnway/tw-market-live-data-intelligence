# TPEx OpenAPI Field Dictionary

**Endpoint:** `https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes`

This document provides a field dictionary for the official TPEx OpenAPI End-of-Day (EOD) quote response.

| Raw field name | Observed meaning | Normalized candidate name | Example value (Code: 3105) | Value type candidate | Required / optional candidate | Confidence level | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `Date` | ROC Year format trade date | `trade_date` | `1150618` | String (ROC format) | optional | observed | Usually formatted as ROC year + MMDD. |
| `SecuritiesCompanyCode` | Stock symbol code | `symbol` | `3105` | String | required | official_documented | Target symbol (stock or ETF). |
| `CompanyName` | Stock company name | `name` | `穩懋` | String | required | official_documented | Chinese name of the asset. |
| `Close` | Closing price | `close` | `528.00` | Numeric (parsed) | optional | official_documented | EOD close price. |
| `Change` | Change from previous close | `change` | `+9.00` | Numeric (parsed) | optional | official_documented | Explicitly includes signs (e.g., `+`, `-`). |
| `Open` | Opening price | `open` | `522.00` | Numeric (parsed) | optional | official_documented | EOD open price. |
| `High` | Highest price | `high` | `557.00` | Numeric (parsed) | optional | official_documented | EOD high price. |
| `Low` | Lowest price | `low` | `521.00` | Numeric (parsed) | optional | official_documented | EOD low price. |
| `Average` | Average trade price | `average_price` | `538.47` | Numeric (parsed) | optional | observed | Average price. Will be in `unmapped_raw_fields` in draft v1. |
| `TradingShares` | Total trading volume (shares) | `trade_volume` | `40139349` | Numeric (parsed) | optional | official_documented | Total shares traded in the session. (Alias: `TradingVolume`) |
| `TransactionAmount` | Total trading value (TWD) | `trade_value` | `21613642453` | Numeric (parsed) | optional | official_documented | Total turnover in TWD. (Alias: `TradingAmount`) |
| `TransactionNumber` | Number of transactions | `transaction_count` | `47240` | Numeric (parsed) | optional | official_documented | Total number of trades executed. (Alias: `Transaction`) |
| `LatestBidPrice` | Latest bid price | (unmapped) | `528.00` | Numeric | optional | observed | Preserved in `unmapped_raw_fields`. |
| `LatesAskPrice` | Latest ask price | (unmapped) | `529.00` | Numeric | optional | observed | Preserved in `unmapped_raw_fields`. |
| `Capitals` | Outstanding shares / Capital | (unmapped) | `423940384` | Numeric | optional | observed | Preserved in `unmapped_raw_fields`. |
| `NextReferencePrice` | Next day reference price | (unmapped) | `528.00` | Numeric | optional | observed | Preserved in `unmapped_raw_fields`. |
| `NextLimitUp` | Next day limit up price | (unmapped) | `580.00` | Numeric | optional | observed | Preserved in `unmapped_raw_fields`. |
| `NextLimitDown` | Next day limit down price | (unmapped) | `475.50` | Numeric | optional | observed | Preserved in `unmapped_raw_fields`. |

## Notes
- **Empty Values**: Numeric fields can often be empty `""` or contain placeholder strings (e.g. `"-"`) when an asset has no trades on that day. These are parsed to `None`.
- **Reference**: Official API semantics do not guarantee real-time data. This is strictly an End-of-Day (EOD) snapshot endpoint.
