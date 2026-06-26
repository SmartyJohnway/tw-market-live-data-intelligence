# Frontend Readonly Caveat and Staleness Display Contract

## Purpose

This design defines how a frontend should display readonly market context with caveats and staleness information. It is design-only and does not authorize frontend writes, frontend artifact refresh, production refresh, trading signals, or realtime claims.

## Required Readonly Display Fields

For each displayed symbol/source candidate, the UI must expose or make immediately available:

- source authority
- source id
- freshness status
- delay status
- staleness seconds
- `retrieved_at`
- `source_timestamp`
- data quality flags
- source risk flags
- normalization status
- price semantics

## Required Caveats

The UI must communicate:

- not realtime-guaranteed
- not a trading signal
- not buy/sell/hold advice
- not production current state unless explicitly refreshed under a separate authorization
- official OpenAPI sources are EOD reference only
- TWSE MIS is an unofficial frontend source and may be delayed, stale, blocked, or fragile
- third-party sources may have delay, coverage, and maintenance risk

## UI Wording Examples

- `Live candidate; not guaranteed realtime.`
- `Delayed candidate; verify source timestamp before use.`
- `Stale data; do not treat as current market state.`
- `EOD reference only; not intraday data.`
- `Unavailable or malformed source data; no fallback current price inferred.`
- `Descriptive market context only; not a trading signal.`

## Warning / Caveat Display Logic

- If `freshness_status` is `stale` or `delay_status` is `stale`, show a high-visibility stale warning.
- If `freshness_status` is `delayed` or `delay_status` is `delayed_candidate`, show a delayed warning.
- If `freshness_status` is `eod_batch`, show EOD-reference-only wording.
- If `staleness_seconds` is null or missing, show freshness unknown.
- If `data_quality_flags` is non-empty, show a data-quality warning or expandable details.
- If `source_risk_flags` is non-empty, show source-risk details near the affected value.
- Never relabel `live_candidate` as realtime.

## Prohibited Frontend Behavior

- No `frontend/public/*` writes.
- No frontend artifact refresh.
- No production refresh.
- No trading signals.
- No realtime claim.
- No hidden caveats for price-like values.
- No substitution of yesterday's close as current market data.

## Non-goals

- Implementing UI code.
- Generating frontend artifacts.
- Running live probes.
- Promoting evidence into production current market state.
- Adding trading recommendations, rankings, target prices, or automated actions.
