# Glossary

- staging_only: local candidate payload not promoted to production.
- readonly_only: display-only package.
- production_current_state: durable current market state; not produced here.
- frontend_public_artifact: published frontend artifact; forbidden here.
- realtime_guaranteed: verified realtime guarantee; not claimed.
- trading_signal: buy/sell/hold, ranking, target price, or recommendation output; forbidden.
- live_candidate: possible low-latency candidate, still not realtime guaranteed.
- delayed: delayed candidate.
- stale: stale data requiring caveat.
- eod_batch: end-of-day batch.
- unknown: unknown freshness or delay.
- unofficial_source_risk: unofficial endpoint risk flag.
- fragile_frontend_contract: browser/frontend contract fragility.
- not_official_realtime_api: source is not official realtime API.
- not_production_current_market_state_by_itself: cannot be treated as current state alone.
- validation-only: used for validation, not promotion.
- fixture-backed: backed by local fixture data.
