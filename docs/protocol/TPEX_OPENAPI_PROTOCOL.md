# TPEx OpenAPI Protocol

## Overview
- **Source Name:** TPEx OpenAPI
- **Source Type:** `official_openapi`
- **Current Endpoint Used:** `https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes`
- **Request Method:** `GET`
- **Authentication Requirement:** None
- **Session/Cookie Requirement:** None
- **Response Format:** JSON Array
- **Role in Project Architecture:** Bounded source for EOD official quotes for OTC (TPEx) equities.

## Endpoint Semantics and Constraints

### Freshness and Delay
- **Freshness Category:** `eod_batch`
- **Delay Status:** `eod`
- This endpoint returns **End of Day (EOD)** data. It is **not** a live execution-grade data feed. Intraday polling of this endpoint will not yield live tick-by-tick market data.

### Coverage and Unsupported Targets
- **Coverage:** OTC equities (TPEx mainboard) only.
- **Unsupported Targets:** TWSE equities, Indices, Futures, Options, and most Funds.

### Explicit Limitations
- **Not for Intraday Live Trading:** The official OpenAPI feed should only be considered authoritative for daily closing reference data.
- **Rate Limits:** As a free, unauthenticated public endpoint, aggressive polling may lead to HTTP 429 errors or temporary IP blocking.

## High-Level Response Shape

The response is a top-level JSON array of objects. Each object represents the daily close summary for a single ticker symbol.

```json
[
  {
    "Date": "20231005",
    "SecuritiesCompanyCode": "5347",
    "CompanyName": "世界",
    "Close": "75.00",
    "Change": "1.00",
    "Open": "74.00",
    "High": "75.50",
    "Low": "73.80",
    "TradingVolume": "5000000",
    "TradingAmount": "375000000",
    "Transaction": "2500"
  }
]
```

## Minimal Field Notes (Observed)

| Raw Field Name | Observed Meaning | Normalized Candidate Name | Confidence Level |
| --- | --- | --- | --- |
| `SecuritiesCompanyCode` | Ticker symbol (e.g. `5347`) | `symbol` | `official_documented` |
| `CompanyName` | Company short name | `name` | `official_documented` |
| `Close` | EOD closing price | `price` | `official_documented` |
| `Change` | Daily price change | `change` | `official_documented` |
| `Date` | Trade date | (Date) | `observed` |
| `Open` | Opening price | (Open) | `observed` |
| `High` | Highest price | (High) | `observed` |
| `Low` | Lowest price | (Low) | `observed` |
| `TradingVolume` | Total trading volume | (Volume) | `observed` |

*(Note: Full standalone field dictionaries and complete schema normalization contracts are deferred to M2D-02).*

## Known Failure Modes
- **HTTP 404/5xx / Network Timeout:** Temporary unavailability of the TPEx OpenAPI servers.
- **Empty Array (`[]`):** Might occur on non-trading days, holidays, or before the batch has run for the current trading day.
- **Missing Fields:** Schema drift could result in expected fields (like `SecuritiesCompanyCode` or `Close`) missing from the response objects.
