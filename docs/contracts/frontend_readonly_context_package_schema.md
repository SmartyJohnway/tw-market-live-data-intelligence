# Frontend readonly context package schema

This contract defines a temporary, local-first readonly context package derived from a validated controlled refresh staging payload.
It is not a frontend/public artifact, not production current state, not a trading signal, and not a realtime guarantee.

## Top-level fields

- `schema_version`: `frontend_readonly_context_package.v1`.
- `generated_at_utc`: package generation time copied from the staging payload.
- `readonly_only`: must be `true`.
- `production_current_state`: must be `false`.
- `frontend_public_artifact`: must be `false`.
- `realtime_guaranteed`: must be `false`.
- `trading_signal`: false.
- `sources`: source display metadata.
- `symbols`: symbol/source display rows.
- `global_caveats`: must include `not_realtime_guaranteed`, `not_trading_signal`, `not_production_current_state`, `source_risk_present`, and `freshness_must_be_displayed`.
- `validation`: local validation summary.

## Symbol display object

Each row includes `symbol`, `source_id`, `source_authority`, `price_like_value`, `price_semantics`, `freshness_status`, `delay_status`, `staleness_seconds`, `retrieved_at`, `source_timestamp`, `normalization_status`, `data_quality_flags`, `source_risk_flags`, and `display_caveats`.

## Boundaries

The package builder may write only to an operator-supplied temporary or staging path. It must fail closed for `frontend/public/*`, production-looking paths, trading recommendation fields, and invalid staging payloads. The package must never present buy/sell/hold values.
