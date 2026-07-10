# M8 Multi-source Market Context Schema

- **Status**: `m8_00_multi_source_market_context_schema.v1_defined`
- **Schema version**: `m8_00_multi_source_market_context.v1`

This is schema only. No builder is implemented in this PR. The builder belongs to M8-00-05. Conversation context integration belongs to M8-00-06.

## Candidate structure

```json
{
  "schema_version": "m8_00_multi_source_market_context.v1",
  "context_status": "candidate_schema_only",
  "generated_at_utc": null,
  "market_scope": {},
  "sources": [],
  "freshness_summary": {},
  "instrument_contexts": [],
  "cross_source_caveats": [],
  "ai_exposure_policy": {},
  "not_trading_signal": true,
  "not_recommendation": true
}
```

## Field definitions

### `sources[]`

- `source_id`
- `source_family`
- `authority_level`
- `timing_class`
- `freshness_assessment`
- `ai_exposure_level`
- `runtime_executable`
- `caveats`

### `instrument_contexts[]`

- `symbol`
- `market`
- `instrument_type`
- `contexts[]`

Each `contexts[]` entry includes:

- `source_id`
- `context_type`
- `timing_class`
- `value_status`
- `source_timestamp`
- `retrieved_at_utc`
- `freshness_assessment`
- `safe_fields`
- `omitted_fields`
- `caveats`

### `freshness_summary`

- `has_liveish_intraday_snapshot`
- `has_official_eod_reference`
- `has_official_statistics_eod`
- `has_manual_snapshot`
- `has_validation_only`
- `has_stale_sources`
- `has_unavailable_sources`
- `most_recent_retrieved_at_utc`
- `caveated_currentness_label`

### `ai_exposure_policy`

- `safe_to_include_in_conversation_context`
- `requires_caveats`
- `blocked_fields`
- `forbidden_interpretations`
- `not_trading_signal`
- `not_recommendation`
- `not_realtime_unless_source_policy_allows`

## Governance constraints

- no TPEX_MIS is introduced by this schema.
- no rotc_ route is introduced by this schema.
- no trading advice is allowed.
- EOD must not be realtime.
- retrieved_at_utc is not exchange timestamp unless a source contract explicitly proves otherwise.
