# M2 Normalized Schema Inventory

This document details the normalized contracts established during the M2 milestone series. These schemas define the standardized data shapes expected by the system after parsing and normalizing data from various sources.

## Inventory of Normalized Schemas

### 1. TWSE MIS Normalized Snapshot / Watchlist Sample
- **File path:** `docs/contracts/twse_mis_normalized_snapshot_v2_draft.md`
- **Scope:** Realtime/delayed snapshot data for a specific watchlist.
- **Input source:** TWSE MIS (`unofficial_frontend_endpoint`)
- **Normalized output location:** Output within the `normalized_sample` block of the TWSE MIS probe report.
- **Key fields:** `symbol`, `name`, `trade_price`, `trade_volume`, `best_bid_price`, `best_ask_price`, `time_tw_str`.
- **Required metadata:** `freshness_status` (e.g., `realtime_candidate`, `delayed`), `delay_status`, `staleness_seconds`.
- **Data quality flags:** `missing_prices`, `missing_volumes`, `malformed_fields`, `unmapped_raw_fields`.
- **Source risk flags:** Unofficial endpoint, rate-limiting risks, unauthenticated cookie dependency.
- **Known caveats:** Subject to strict IP rate-limiting. High risk of breaking.
- **Whether M3 can consume it:** M3-eligible **only** as bounded watchlist context with strict caveats about its unofficial and high-risk nature.

### 2. Yahoo Finance Normalized Chart v1
- **File path:** `docs/contracts/yahoo_finance_normalized_chart_v1.md`
- **Scope:** Intraday or historical chart time-series data.
- **Input source:** Yahoo Finance Chart API (`unofficial_api` / third-party)
- **Normalized output location:** Output within the `normalized_sample` block of the Yahoo Finance probe report.
- **Key fields:** `symbol`, `exchange`, `currency`, `timezone`, `timestamps` (array), `close_prices` (array), `volumes` (array).
- **Required metadata:** `regular_market_price`, `regular_market_time`, `gmtoffset`.
- **Data quality flags:** `missing_prices`, `inconsistent_array_lengths`, `stale_quote`.
- **Source risk flags:** Unofficial proxy for market data, undocumented limits.
- **Known caveats:** Third-party compilation. Not a source of truth for exact TWSE/TPEx EOD records.
- **Whether M3 can consume it:** M3-eligible **only** as bounded chart/watchlist context with explicit third-party and coverage caveats.

### 3. TWSE OpenAPI Normalized EOD Quote v1
- **File path:** `docs/contracts/twse_openapi_normalized_eod_quote_v1.md`
- **Scope:** Official End-of-Day (EOD) market data for TWSE targets.
- **Input source:** TWSE OpenAPI (`official_openapi`)
- **Normalized output location:** Output within the `normalized_sample` block of the TWSE OpenAPI probe report.
- **Key fields:** `symbol`, `name`, `trade_date`, `open`, `high`, `low`, `close`, `change`, `trade_volume`, `trade_value`, `transaction_count`, `currency`, `freshness_status`, `delay_status`, `coverage_status`, `source_risk_flags`, `data_quality_flags`, `raw_row`, `unmapped_raw_fields`, `retrieved_at_utc`.
- **Required metadata:** `trade_date`.
- **Data quality flags:** `missing_trade_date` (mapped to `None`), `malformed_numerics`.
- **Source risk flags:** EOD only. Cannot be used for live quotes.
- **Known caveats:** Only updates at the end of the trading day. Does not cover TPEx.
- **Whether M3 can consume it:** M3-eligible as official EOD/reference context.

### 4. TPEx OpenAPI Normalized EOD Quote v1
- **File path:** `docs/contracts/tpex_openapi_normalized_eod_quote_v1.md`
- **Scope:** Official End-of-Day (EOD) market data for TPEx targets.
- **Input source:** TPEx OpenAPI (`official_openapi`)
- **Normalized output location:** Output within the `normalized_sample` block of the TPEx OpenAPI probe report.
- **Key fields:** `symbol`, `name`, `trade_date`, `open`, `high`, `low`, `close`, `change`, `trade_volume`, `trade_value`, `transaction_count`, `currency`, `freshness_status`, `delay_status`, `coverage_status`, `source_risk_flags`, `data_quality_flags`, `raw_row`, `unmapped_raw_fields`, `retrieved_at_utc`.
- **Required metadata:** `trade_date`.
- **Data quality flags:** `missing_trade_date`, `malformed_numerics`.
- **Source risk flags:** EOD only.
- **Known caveats:** Field mappings differ slightly from TWSE raw data (e.g., `TradingShares` vs `TradingVolume`) but are resolved in normalization.
- **Whether M3 can consume it:** M3-eligible as official EOD/reference context.

### 5. Standard Probe Envelope
- **File path:** Generated natively by the data probe framework.
- **Scope:** The overarching standard JSON wrapper for any probe execution output.
- **Input source:** Applicable to all source probes.
- **Normalized output location:** The root object of the JSON probe reports.
- **Key fields:** `probe_id`, `schema_fingerprint`, `retrieved_at_taipei`, `http_ok`, `parse_status`, `normalization_status`, `is_usable_now`.
- **Required metadata:** `unsupported_targets`, `failed_targets`.
- **Data quality flags:** Rolled up from specific schema failures.
- **Source risk flags:** Varies by source type included in the payload.
- **Known caveats:** N/A. Acts as the standardized delivery mechanism.
- **Whether M3 can consume it:** Yes, the envelope metadata (especially `freshness_status` and caveats) is critical for M3.

## Summary regarding Broker APIs
Broker APIs (like Fugle MarketData and Fubon Neo) currently lack implemented normalized schemas in this repository as they hold a `doc_only` / `auth_required` status. They are **not** M3-consumable unless a future authenticated scope exists.