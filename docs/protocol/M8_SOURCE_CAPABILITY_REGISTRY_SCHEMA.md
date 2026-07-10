# M8 Source Capability Registry Schema

- **Status**: `m8_source_capability_registry_schema.v1_defined`
- **Schema version**: `m8_source_capability_registry.v1`

## Purpose

The M8 source capability registry defines source-family authority, timing, runtime availability, freshness policy, and AI exposure metadata before any future M8 adapter work. It is a policy and metadata schema only.

## Required source family record fields

Each source family record must include at least:

- `source_id`
- `source_family`
- `display_name`
- `authority_level`
- `official_documented`
- `endpoint_type`
- `timing_class`
- `latency_class`
- `freshness_policy`
- `market_scope`
- `instrument_scope`
- `field_groups`
- `runtime_available`
- `runtime_executable`
- `ai_context_allowed`
- `ai_exposure_level`
- `primary_use`
- `allowed_interpretation`
- `blocked_interpretation`
- `caveats`
- `credential_required`
- `local_first_safe`
- `raw_payload_exposure_allowed`
- `trading_signal_allowed`
- `recommendation_allowed`
- `source_notes`

## Enum suggestions

### authority_level

- `official_documented`
- `official_undocumented`
- `unofficial_observed`
- `manual_operator_evidence`
- `external_validation_only`
- `credential_gated_provider`

### endpoint_type

- `hidden_browser_json`
- `official_openapi`
- `official_web_page`
- `manual_upload`
- `provider_api`
- `derived_context`

### timing_class

- `liveish_intraday_snapshot`
- `official_eod`
- `official_statistics_eod`
- `regulatory_reference`
- `fundamental_reference`
- `manual_snapshot`
- `validation_only`
- `credential_gated_research`

### latency_class

- `intraday_snapshot`
- `eod_after_close`
- `delayed_reference`
- `manual`
- `unknown`

### ai_exposure_level

- `safe_context_allowed`
- `caveated_context_allowed`
- `metadata_only`
- `validation_only`
- `blocked`

## M8-00 defaults and prohibitions

- `runtime_executable` is boolean: `true` or `false`.
- `raw_payload_exposure_allowed` is `false` by default.
- `trading_signal_allowed` is `false` always for M8-00.
- `recommendation_allowed` is `false` always for M8-00.
- no TPEX_MIS is introduced by this schema.
- no rotc_ route is introduced by this schema.
- no trading advice is allowed from this schema.
