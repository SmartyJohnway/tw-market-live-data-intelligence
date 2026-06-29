# AI Safety Policy

## Required framing
AI responses must state that M5F data is historical/stale reviewed evidence for a bounded watchlist. Always include source, source date, freshness/staleness, and caveats.

## Prohibited outputs
Do not provide investment advice, buy/sell/hold instructions, target prices, rankings, portfolio actions, full-market claims, realtime guarantees, production-current-state claims, or broker/execution guidance.

## Source authority rules
TWSE_OpenAPI is official reference evidence in this package, not an intraday realtime feed. Source authority must be quoted from the package; do not upgrade source status based on assumptions.

## Freshness requirements
Display `historical/stale`, source date, retrieval timestamp where available, delay status, and `not_realtime_guaranteed`. If a symbol or source fails in future packages, disclose it instead of fabricating values.

## Bounded watchlist requirement
Only discuss the symbols present in the canonical payload. Do not infer market-wide conclusions from 0050, 00929, and 2330.

## Failure behavior
If package validation fails or a consumer reports malformed/missing artifacts, refuse market summarization and ask the operator to restore or rebuild the canonical package through the validator and builder.
