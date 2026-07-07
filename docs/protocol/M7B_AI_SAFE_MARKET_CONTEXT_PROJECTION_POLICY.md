# M7B AI-safe market context projection policy

## 1. Purpose

M7B designs an AI-safe projection layer on top of M7A runtime-populated `twse_mis_rich_facts`. The projection is a policy-gated, caveated market snapshot context for AI readers, not a raw facts dump and not an exposure enablement in M7B-00/M7B-01.

The projection must preserve M7A caveats and must not treat candidate TWSE MIS field semantics as official field definitions, realtime guarantees, verified quantity units, trading guidance, or complete market depth.

## 2. M7A dependency

M7B depends on M7A final acceptance: **M7A completed as pass_with_caveats.** The starting evidence and constraints are documented in:

- `docs/protocol/M7A_TWSE_MIS_RICH_FACTS_FINAL_ACCEPTANCE.md`
- `docs/protocol/TWSE_MIS_RICH_OBSERVATION_CONTRACT.md`
- `docs/data_capabilities/twse_mis_rich_field_inventory.json`

M7A produced runtime-populated `twse_mis_rich_facts`, but M7A explicitly kept AI exposure unsafe by default. M7B-00/M7B-01 therefore define policy and schema only.

## 3. M7B scope

Allowed in M7B:

- define AI-safe projection policy
- define projection schema
- define allowed field families
- define blocked field families
- define evidence language
- define safety levels
- define future builder requirements

Not allowed in M7B-00/M7B-01:

- runtime projection builder
- FastAPI/MCP/frontend integration
- conversation context exposure
- AI-safe exposure enablement

## 4. Allowed projection categories

Allowed projection categories include only caveated, non-signal facts:

- `instrument_context`
- `source_context`
- `price_snapshot_context`
- `reference_price_context`
- `session_state_context`
- `index_market_context`
- `displayed_depth_availability_context`
- `data_quality_context`
- `freshness_context`
- `caveat_context`

## 5. Blocked projection categories

The projection must block these categories:

- `trading_signal`
- `recommendation`
- `buy_sell_hold`
- `target_price`
- `support_resistance`
- `main_force`
- `true_liquidity`
- `order_book_truth`
- `execution_feed`
- `realtime_guarantee`
- `official_api_definition`
- `unit_verified_quantity`
- `odd_lot_semantics_without_mode_evidence`

## 6. Field admission policy

Allowed with caveats for future projection:

- `instrument_facts.instrument_kind_candidate`
- `instrument_facts.price_domain`
- `market_mode_facts.market_mode_candidate`
- `price_facts.last_value`
- `price_facts.previous_close`
- `price_facts.open`
- `price_facts.high`
- `price_facts.low`
- `price_facts.last_value_placeholder`
- `price_facts.fallback_reference_field`
- `timestamp_facts` raw source time values
- `session_state_candidate_facts.session_state_candidate`
- `auction_or_reference_facts` `raw_ps`/`raw_pz`/`raw_ts` as candidate/reference context only
- `index_market_facts` `raw_m`/`raw_r` and candidate semantics for index rows only
- `displayed_depth_facts.applicable`
- `displayed_depth_facts.best_bid`/`best_ask` only as displayed quote snapshot, not support/resistance
- `quality_facts.placeholder_fields`
- `quality_facts.malformed_fields`
- `quality_facts.ladder_mismatch_flags`
- `semantic_confidence` `evidence_level`
- `ai_exposure_policy` `safe_for_ai_context=false` inherited from M7A

Blocked from direct projection:

- full displayed ladder arrays unless explicitly summarized as availability only
- `raw_unknown_facts` except quality/caveat mention
- `raw_pid`, `raw_hash`, `raw_m_percent`, `raw_mt`
- broker/app supporting-only evidence as authoritative source
- any field with `unit_verified=false` as verified quantity
- any inferred direction that becomes a recommendation

Future projection may compute a descriptive relation such as `direction_vs_previous_close = up/down/flat/unknown`. This relation must remain strictly descriptive and must not become trend, signal, momentum, buy/sell, target, support/resistance, or any recommendation.

## 7. Evidence language policy

Allowed evidence language:

- `runtime_parsed_candidate`
- `operator_evidence_supported_not_official_dictionary`
- `official_mis_ui_cross_checked_not_field_dictionary`
- `probe_observed`
- `market_context_required`
- `not_realtime_guaranteed`
- `source_may_be_delayed_or_unavailable`

Forbidden evidence language unless explicitly framed as blocked/negated:

- official API definition
- official field dictionary validated
- realtime guaranteed
- SLA-backed
- verified lot/share unit
- full order book
- true liquidity
- support/resistance
- trading signal

## 8. AI exposure safety levels

Status levels:

- `not_safe_raw_facts`
- `schema_only`
- `projection_candidate_not_exposed`
- `ai_safe_projection_candidate`
- `ai_safe_context_enabled`
- `blocked`

For M7B-00/M7B-01, the expected status is `projection_candidate_not_exposed`.

M7B-00/M7B-01 must not set `ai_safe_context_enabled`.

## 9. M7B planned tasks

Planned sequence:

- M7B-00: readiness / scope / policy
- M7B-01: AI-safe projection schema
- M7B-02: pure projection builder
- M7B-03: fixtures and safety tests
- M7B-04: controlled exposure integration
- M7B-05: compatibility hardening
- M7B-06: final acceptance / closure
