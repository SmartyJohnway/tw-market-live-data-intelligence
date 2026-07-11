# M8 Source Freshness Evaluator

Status: `m8_00_04_source_freshness_evaluator_defined`

## 1. Purpose

`M8-00-04-SOURCE-FRESHNESS-EVALUATOR-PURE-HELPER` defines a pure, deterministic helper for classifying one observation/source-policy pair into a safe M8 freshness assessment. The helper is implemented in `scripts/m8_source_freshness_evaluator.py` and exists to prevent timing and authority mistakes before the M8-00-05 multi-source context builder is implemented.

This is not runtime integration. It does not build multi-source context, does not expose conversation context, does not add adapters, and does not fetch data.

## 2. Inputs

### `observation`

A caller-provided dictionary representing one already-obtained observation. Supported fields include:

- `source_id`
- `source_family`
- `source_timestamp`
- `retrieved_at_utc`
- `market_date`
- `trading_date`
- `session_state`
- `source_unavailable`
- `source_unavailable_reason`
- `value_status`
- `validation_status`

### `source_policy`

A single source record from `docs/data_capabilities/m8_source_capability_registry.json`. Supported fields include:

- `source_id`
- `source_family`
- `authority_level`
- `timing_class`
- `latency_class`
- `freshness_policy`
- `runtime_executable`
- `ai_exposure_level`
- `ai_context_allowed`
- `allowed_interpretation`
- `blocked_interpretation`
- `caveats`
- `freshness_evaluator_policy`

Optional `freshness_evaluator_policy` keys include:

- `max_intraday_age_seconds`
- `allow_retrieved_at_only_intraday_freshness`
- `requires_exchange_timestamp_for_fresh`
- `eod_reference_requires_market_date`
- `unavailable_if_value_status_in`

### `now_utc`

Optional ISO-8601 UTC timestamp used as the deterministic comparison clock. Tests should pass `now_utc`. If omitted, the helper uses current UTC internally; no local timezone is used.

## 3. Output schema

The helper returns `m8_source_freshness_assessment.v1` with these fields:

- `schema_version`
- `source_id`
- `source_family`
- `authority_level`
- `timing_class`
- `latency_class`
- `freshness_assessment`
- `freshness_reason`
- `stale_reason`
- `source_unavailable_reason`
- `source_timestamp`
- `retrieved_at_utc`
- `market_date`
- `trading_date`
- `session_state`
- `delay_seconds`
- `age_seconds`
- `not_realtime_guaranteed`
- `eod_only`
- `intraday_snapshot`
- `manual_snapshot`
- `validation_only`
- `credential_gated`
- `exchange_timestamp_absent`
- `retrieved_time_only`
- `requires_caveats`
- `safe_for_ai_context`
- `ai_exposure_level`
- `allowed_interpretation`
- `blocked_interpretation`
- `caveats`
- `not_trading_signal`
- `not_recommendation`
- `trading_advice_allowed`
- `trading_signal_allowed`
- `recommendation_allowed`

## 4. Timing-class mapping

- `liveish_intraday_snapshot` maps to `fresh_intraday_snapshot`, `stale_intraday_snapshot`, `source_unavailable`, or `unknown`.
- `official_eod` maps to `official_eod_reference`.
- `official_statistics_eod` maps to `official_statistics_eod`.
- `regulatory_reference` maps to `regulatory_reference`.
- `manual_snapshot` maps to `manual_snapshot`.
- `validation_only` maps to `validation_only`.
- `credential_gated_research` maps to `credential_gated_metadata_only`.
- `fundamental_reference` maps conservatively to `unknown` for M8-00-04 because no dedicated freshness assessment enum exists yet.
- Unknown or malformed timing inputs map to `unknown` with caveats.

## 5. Hard interpretation rules

- `retrieved_at_utc` is not exchange timestamp.
- EOD is not realtime.
- Stale is not current.
- Manual snapshot is not official source.
- Validation-only is not primary source.
- Credential-gated source is not runtime dependency.
- Freshness labels are not trading signals.
- The helper must not output trading advice, recommendations, bullish/bearish labels, target prices, support/resistance, or market direction.

## 6. Non-goals

- No context builder.
- No conversation integration.
- No adapter.
- No network.
- No frontend change.
- No server change.
- No MCP change.
- No scheduler, polling, hidden fetch, or startup fetch.

## 7. Next task

`M8-00-05-MULTI-SOURCE-CONTEXT-BUILDER`
