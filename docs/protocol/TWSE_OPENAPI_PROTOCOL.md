# TWSE OpenAPI Protocol

## Overview
- **Source Name:** TWSE OpenAPI
- **Source Type:** `official_openapi`
- **Current Endpoint Used:** `https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL`
- **Request Method:** `GET`
- **Authentication Requirement:** None
- **Session/Cookie Requirement:** None
- **Response Format:** JSON Array
- **Role in Project Architecture:** Bounded source for EOD official quotes for listed (TWSE) equities.

## Endpoint Semantics and Constraints

### Freshness and Delay
- **Freshness Category:** `eod_batch`
- **Delay Status:** `eod`
- This endpoint returns **End of Day (EOD)** data. It is **not** a live execution-grade data feed. Intraday polling of this endpoint will not yield live tick-by-tick market data.

### Coverage and Unsupported Targets
- **Coverage:** Listed equities (TWSE) only.
- **Unsupported Targets:** Indices, Futures, Options, and most Funds.

### Explicit Limitations
- **Not for Intraday Live Trading:** The official OpenAPI feed should only be considered authoritative for daily closing reference data.
- **Rate Limits:** As a free, unauthenticated public endpoint, aggressive polling may lead to HTTP 429 errors or temporary IP blocking.

## High-Level Response Shape

The response is a top-level JSON array of objects. Each object represents the daily close summary for a single ticker symbol.

```json
[
  {
    "Code": "1101",
    "Name": "台泥",
    "TradeVolume": "45678901",
    "TradeValue": "1500000000",
    "OpeningPrice": "33.50",
    "HighestPrice": "34.00",
    "LowestPrice": "33.10",
    "ClosingPrice": "33.80",
    "Change": "0.30",
    "Transaction": "15000"
  }
]
```

## Minimal Field Notes (Observed)

| Raw Field Name | Observed Meaning | Normalized Candidate Name | Confidence Level |
| --- | --- | --- | --- |
| `Code` | Ticker symbol (e.g. `2330`) | `symbol` | `official_documented` |
| `Name` | Company short name | `name` | `official_documented` |
| `ClosingPrice` | EOD closing price | `price` | `official_documented` |
| `Change` | Daily price change | `change` | `official_documented` |
| `TradeVolume` | Total trading volume | (Volume) | `observed` |
| `OpeningPrice` | Opening price | (Open) | `observed` |
| `HighestPrice` | Highest price | (High) | `observed` |
| `LowestPrice` | Lowest price | (Low) | `observed` |

*(Note: For full field dictionaries, see [TWSE OpenAPI Field Dictionary](TWSE_OPENAPI_FIELD_DICTIONARY.md). For schema normalization, see [TWSE OpenAPI Normalized EOD Quote Contract v1](../contracts/twse_openapi_normalized_eod_quote_v1.md)).*

## Known Failure Modes
- **HTTP 404/5xx / Network Timeout:** Temporary unavailability of the TWSE OpenAPI servers.
- **Empty Array (`[]`):** Might occur on non-trading days, holidays, or before the batch has run for the current trading day.
- **Missing Fields:** Schema drift could result in expected fields (like `Code` or `ClosingPrice`) missing from the response objects.
