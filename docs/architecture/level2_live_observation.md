# Level 2 Live Observation

Level 2 provides explicit, bounded, non-canonical market observations for a watchlist.

## Unified observation model

Adapters emit `m5_live_observation.normalized.v1` records with common fields for symbol, source, adapter, status, price-like value, source timestamp, retrieval timestamp, freshness, delay, reference-only status, contract details, data-quality flags, source-risk flags, and caveats.

## Unified failure model

Adapters emit `m5_live_observation.failure.v1` records with common fields for symbol, source, adapter, status, reason, stage, source status, investigation summary, retryability, and governance caveats.

## Safety rules

- Explicit execution only.
- Bounded watchlists only.
- No writes to M5F, `frontend/public`, `research/generated`, or production paths.
- No trading recommendation fields.
- No realtime claim unless source timestamps and delay semantics support it.
