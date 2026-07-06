# Official OpenAPI Source Semantics

## Purpose
This document clarifies the semantic boundaries, usage intents, and constraints of official OpenAPI data sources in comparison to other categories of data providers. This is crucial to avoid overclaiming capabilities or introducing architectural risks.

## Source Semantic Categories

| Source | Official Status | Freshness Category | Authentication | Session/Cookie | Coverage | Best Use | Unsuitable Use | Known Risks | AI Suitability |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TWSE OpenAPI** | Official (`official_openapi`) | EOD / Batch (`eod_batch`) | None | None | TWSE Listed Equities | End of day reference data, official daily quote context | Live intraday pricing, execution logic | Rate limits | Suitable for historical and EOD reference |
| **TPEx OpenAPI** | Official (`official_openapi`) | EOD / Batch (`eod_batch`) | None | None | TPEx OTC Equities | End of day reference data, official daily quote context | Live intraday pricing, execution logic | Rate limits | Suitable for historical and EOD reference |
| **TAIFEX OpenAPI** | Official (`official_openapi`) | Daily / Statistical / Reference / Historical candidate (`official_statistical`) | None observed in OAS | None observed in OAS | TAIFEX derivatives reports, statistics, reference data | Source-family inventory and future EOD/statistical/reference context planning | Live observation, TAIFEX_MIS replacement, trading signals | Timing/freshness validation still required; interpretation risk for derivatives statistics | Suitable for descriptive EOD/statistical/reference planning only |
| **TWSE MIS** | Unofficial (`unofficial_frontend_endpoint`) | Realtime candidate / delayed intraday (observed, not guaranteed) | None | Yes, `index.jsp` session initialization / JSESSIONID required | Selected TWSE/TPEx assets | Bounded low-frequency live watchlist context | Full-market scraping, high-frequency polling, automated trading, execution logic | Session-cookie dependency, undocumented rate limits, schema drift, blocking/CAPTCHA risk | Bounded watchlist context only, high risk |
| **Yahoo Finance** | Third-party (`unofficial_api` / `third_party_public_chart_endpoint`) | Delayed Intraday | None | None | Global/Regional assets | Low-frequency watchlist and chart context | Official pricing, accounting | Data gaps, missing symbols, non-official | Suitable for general market trend context |
| **Commercial API (e.g. FinMind)** | Third-party (`commercial_api`) | EOD / Historical | Usually Token | None | Broad Taiwan Markets | Historical analysis, backfilling | Real-time live execution | Subscription limits | Good for deep historical context |
| **Broker API (e.g. Fugle, Fubon)** | Official Broker (`broker_api`) | Real-time / Tick | Strict Token | Yes | Comprehensive | Live execution, order management | Publicly unauthenticated apps | Key rotation, platform lock-in | Suitable for live execution agents (with auth) |

## Semantic Constraints

1. **Official Does Not Mean Live:** The designation `official_openapi` implies the source is the authoritative exchange (TWSE, TPEx, or TAIFEX). However, their public OpenAPI endpoints are explicitly built for batch, End-of-Day (EOD) data distribution. They **do not** provide intraday real-time market data.
2. **Unofficial Endpoints Have Live Risks:** Endpoints like TWSE MIS provide delayed intraday data but are unofficial frontend endpoints. They are suitable for bounded watchlists but carry extremely high risk for automated ingestion due to unpredictable rate limiting and schema changes.

## Schema Contracts
For exact field mappings and data structures for the official OpenAPI endpoints, refer to:
- [TWSE OpenAPI Field Dictionary](TWSE_OPENAPI_FIELD_DICTIONARY.md) and [TWSE OpenAPI Normalized EOD Quote Contract v1](../contracts/twse_openapi_normalized_eod_quote_v1.md)
- [TPEx OpenAPI Field Dictionary](TPEX_OPENAPI_FIELD_DICTIONARY.md) and [TPEx OpenAPI Normalized EOD Quote Contract v1](../contracts/tpex_openapi_normalized_eod_quote_v1.md)
- [TAIFEX OpenAPI Protocol](TAIFEX_OPENAPI_PROTOCOL.md), [TAIFEX OpenAPI Source Family Contract v1](../contracts/taifex_openapi_source_family_v1.md), and [TAIFEX OpenAPI Endpoint Inventory](../data_capabilities/taifex_openapi_endpoint_inventory.json)
3. **No Execution-Grade Data in Free Public APIs:** Real-time, execution-grade tick data is strictly the domain of authenticated Broker APIs or paid direct-market-access (DMA) lines. Official OpenAPIs must never be framed or utilized as execution feeds.
