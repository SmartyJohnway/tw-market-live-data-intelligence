# M2 Source-Contract Baseline

This document defines the consolidated source-contract baseline at the closure of the M2 milestone. It provides the definitive inventory of market data sources evaluated, normalized, and approved for use within the repository, along with explicit definitions of authority, freshness, capability scope, and readiness for downstream consumption (e.g., M3 context pack generation).

## Baseline Scope

This baseline includes the seven canonical data sources explored during the M2 milestone series.

**Note:** No additional sources beyond the M2 canonical seven were promoted into the M2 source-contract baseline. Any future sources require separate source-contract intake and review.

## Source-Contract Inventory Table

| Source | Source type | Authority level | Freshness / delay class | Current normalized contract | Supported target classes | Unsupported target classes | AI-safe usage | Explicit prohibitions | Remaining caveats | M3 eligibility |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TWSE MIS** | unofficial_frontend_endpoint | unofficial / frontend endpoint | realtime_candidate / delayed / stale possible | twse_mis_normalized_snapshot_v2_draft.md | TWSE stocks, TPEx stocks, TWSE ETFs, TPEx ETFs, TWSE Indices (limited) | Futures, options, complex derivatives, unlisted funds | bounded low-frequency watchlist context only | full-market scan, high-frequency polling, execution logic, trading signals | High-risk unofficial source; strict rate limiting; cookies required; may break without notice | allowed only with high-risk caveats and freshness/staleness metadata |
| **Yahoo Finance** | unofficial_api / third-party chart endpoint | third-party, not official | realtime_candidate / delayed / stale possible | yahoo_finance_normalized_chart_v1.md | TWSE stocks, TPEx stocks, TWSE ETFs, Major Indices | Unlisted funds, obscure indices, minor TPEx | low-frequency chart/watchlist context | official quote authority, execution-grade use, guaranteed coverage | Unofficial endpoint; rate limits; relies on third-party data compilation | allowed only with third-party and coverage caveats |
| **TWSE OpenAPI** | official_openapi | official public exchange OpenAPI | EOD/reference | twse_openapi_normalized_eod_quote_v1.md | TWSE stocks, TWSE ETFs | TPEx assets, intraday data, futures, indices (via this endpoint) | official EOD/reference context for TWSE targets | live intraday, execution-grade, full historical ingestion unless future scope | EOD data only; no intraday quotes | allowed as official EOD/reference source |
| **TPEx OpenAPI** | official_openapi | official public exchange OpenAPI | EOD/reference | tpex_openapi_normalized_eod_quote_v1.md | TPEx stocks, TPEx ETFs | TWSE assets, intraday data, futures | official EOD/reference context for TPEx targets | live intraday, execution-grade, full historical ingestion unless future scope | EOD data only; no intraday quotes | allowed as official EOD/reference source |
| **FinMind** | commercial_api / third-party historical/EOD | third-party/commercial dataset | EOD/reference (for free tier) | standard probe envelope | TWSE stocks, TPEx stocks | Live intraday (free tier) | historical/EOD candidate with auth/free-tier caveats | full-market high-frequency scan, acting as official exchange authority | Requires API token (`FINMIND_TOKEN`); rate limits apply on free tier | allowed only with dataset/auth caveats and never as official exchange authority |
| **Fugle MarketData** | commercial/broker API | authenticated provider / broker | unknown / dependent on tier | doc_only / auth_required | TWSE stocks, TPEx stocks | N/A | documentation only unless credentials and explicit future scope exist | usage without explicit credentials and proper pipeline authorization | Requires personal API key | not eligible for live use in current repo |
| **Fubon Neo API** | commercial/broker API | authenticated provider / broker | unknown / dependent on tier | doc_only / auth_required | TWSE stocks, TPEx stocks | N/A | documentation only unless credentials and explicit future scope exist | execution of trades, querying real accounts without explicit authorization | Requires valid brokerage account and certificate setup | not eligible for live use in current repo |

## Contract Guarantees

The contracts detailed above must be respected. Specifically:
- **Execution:** No source in this repository is currently authorized or capable of execution-grade operations.
- **Authority:** Unofficial and third-party sources cannot be presented as official records of trade. Only TWSE OpenAPI and TPEx OpenAPI provide authoritative End-of-Day data.
- **Polling:** Probes against unofficial sources must be low-frequency and bounded (e.g., watchlist scope). Full-market scans and high-frequency loops are prohibited to avoid IP blocks and bandwidth abuse.
