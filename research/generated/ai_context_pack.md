# TW-Market AI Context Pack

**Generated at:** 2026-06-17T10:26:55.245593+00:00

This document provides an evidence-based summary of Taiwan equity market data sources for AI agents.

## Source Capabilities

### TWSE_OpenAPI
- **Type:** official_openapi
- **Usable Now:** ✅ Yes (Contract Status: `normalized_pass`)
- **Freshness:** eod_batch
- **Risk Level:** low
- **AI Suitability:** historical_and_eod
- **Unsupported Targets:** tpex_stocks, futures_candidates, fund_candidates

### TPEx_OpenAPI
- **Type:** official_openapi
- **Usable Now:** ✅ Yes (Contract Status: `normalized_pass`)
- **Freshness:** eod_batch
- **Risk Level:** low
- **AI Suitability:** historical_and_eod
- **Unsupported Targets:** twse_large_caps, futures_candidates, fund_candidates

### Yahoo_Finance
- **Type:** public_api
- **Usable Now:** ✅ Yes (Contract Status: `normalized_pass`)
- **Freshness:** realtime_candidate
- **Risk Level:** medium
- **AI Suitability:** live_watchlist
- **Unsupported Targets:** funds
- **Notes:** Rate limits apply, Not an official data source

### TWSE_MIS
- **Type:** unofficial_frontend_endpoint
- **Usable Now:** ✅ Yes (Contract Status: `normalized_pass`)
- **Freshness:** realtime_candidate
- **Risk Level:** high
- **AI Suitability:** live_watchlist
- **Unsupported Targets:** futures, foreign_funds
- **Failed Targets:** 1435
- **Notes:** Strict rate limiting, Requires index.jsp visit for cookies, Not designed for API use

### FinMind
- **Type:** commercial_api
- **Usable Now:** ✅ Yes (Contract Status: `normalized_pass`)
- **Freshness:** eod_batch
- **Risk Level:** low
- **AI Suitability:** historical_and_eod
- **Unsupported Targets:** funds
- **Failed Targets:** TX
- **Notes:** Free tier rate limits apply

### Fugle_MarketData
- **Type:** commercial_api
- **Usable Now:** ✅ Yes (Contract Status: `auth_required`)
- **Freshness:** unknown
- **Risk Level:** low
- **AI Suitability:** live_streaming_capable
- **Notes:** Requires personal free tier or paid API key, Good WebSocket streaming

### Fubon_Neo_API
- **Type:** broker_api
- **Usable Now:** ✅ Yes (Contract Status: `doc_only`)
- **Freshness:** unknown
- **Risk Level:** high
- **AI Suitability:** execution_capable_but_complex
- **Notes:** Requires valid brokerage account, Requires certificate setup
