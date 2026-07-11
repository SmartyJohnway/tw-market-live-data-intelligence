# M8 Multi-Source Context Builder

Status: `m8_00_05_multi_source_context_builder_defined`

## 1. Purpose

M8-00-05 defines a pure, AI-safe multi-source market context builder. The builder constructs `m8_00_multi_source_market_context.v1` from caller-provided observations, caller-provided source capability registry policy, and M8-00-04 freshness evaluator output.

It is intentionally useful rather than over-restrictive: safe projected values from live-ish, EOD, manual, validation-only, stale, unavailable, credential-gated metadata, and reference contexts may remain visible when caveated. The builder labels timing class, authority level, freshness assessment, primary/supporting/metadata status, and source caveats so later conversation integration cannot confuse EOD with realtime, manual evidence with official data, validation-only evidence with primary context, or freshness labels with trading signals.

## 2. Inputs

- `observations`: caller-provided dictionaries containing already-safe projections and metadata such as `source_id`, `symbol`, `market`, `instrument_type`, `context_type`, `safe_fields`, timestamps, unavailable flags, and caveats.
- `source_registry`: caller-provided `m8_source_capability_registry.v1` dictionary. The core builder does not read registry files from disk.
- `now_utc`: optional caller-provided UTC clock string passed through to the freshness evaluator for deterministic tests and reproducible builds.

## 3. Output schema

The builder returns `m8_00_multi_source_market_context.v1` with top-level status, generated time, source summaries, freshness summary, grouped instrument contexts, cross-source caveats, AI exposure policy, and explicit `not_trading_signal` / `not_recommendation` flags.

## 4. Source handling

- `TWSE_MIS`: bounded live-ish observation. Fresh snapshots may be primary live-ish context; stale snapshots remain included but cannot be current market context.
- `TWSE_OPENAPI` / `TPEX_OPENAPI`: caller-provided official EOD/reference only in this PR. They may be official reference context, not realtime or current price.
- `TAIFEX_OPENAPI`: caller-provided official statistics EOD only in this PR. It is official statistical reference, not a live derivatives signal or leading indicator.
- `MANUAL_OPERATOR_EVIDENCE`: caveated manual snapshot. It may remain visible but cannot override official sources.
- `EXTERNAL_VALIDATION_ONLY`: supporting only, not primary context.
- `CREDENTIAL_GATED_PROVIDER`: metadata-only; not a runtime dependency and no credentials are used or stored.
- `TAIFEX_MIS`: declared metadata/live family, not executable in this PR.
- `MOPS`: fundamental/reference metadata, conservatively caveated until a future source contract classifies it more specifically.

## 5. Safety behavior

- No network access.
- No adapter.
- No runtime integration.
- No conversation integration.
- No frontend, server, or MCP change.
- No raw payload exposure.
- Forbidden raw fields are scrubbed from `safe_fields` and moved to `omitted_fields`.
- Stale observations must not be described as current.
- EOD observations must not be described as realtime.
- Manual evidence must not be described as official or allowed to override official sources.
- Validation-only evidence must not be primary context.
- A freshness label is not a trading signal.

## 6. Not over-restrictive behavior

- The builder should preserve useful `safe_fields`.
- Mixed live-ish + EOD context is allowed when caveated.
- EOD context may be included as official reference, but not current price.
- Stale or unavailable sources may remain in the context as caveated metadata.
- Manual evidence may remain in the context, but cannot override official source.
- Validation-only evidence may remain as supporting context, but cannot be primary.

## 7. Non-goals

- No M8A adapters.
- No OpenAPI fetch.
- No TAIFEX_MIS execution.
- No FastAPI endpoint.
- No conversation context integration.
- No UI.

## 8. Next task

`M8-00-06-CONTROLLED-CONVERSATION-CONTEXT-INTEGRATION`
