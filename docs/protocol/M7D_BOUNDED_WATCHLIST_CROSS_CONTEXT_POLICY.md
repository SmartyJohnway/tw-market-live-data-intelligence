# M7D Bounded Watchlist Cross-Context Policy

Status:
- schema_only
- policy_defined_not_runtime_populated

## 1. Purpose

M7D defines bounded cross-context for the currently configured watchlist and latest observation package. It allows future AI-facing layers to discuss relationships among observed watchlist items without pretending that the observation set represents the whole Taiwan market.

M7D is not full-market breadth, not sector rotation, not capital flow, not prediction, not signal, and not recommendation.

## 2. Dependency

M7D depends on:
- M7A pass_with_caveats
- M7B pass_with_caveats
- M7C pass_with_caveats

References:
- `docs/protocol/M7C_DETERMINISTIC_METRICS_FINAL_ACCEPTANCE.md`
- `docs/protocol/M7B_AI_SAFE_MARKET_CONTEXT_FINAL_ACCEPTANCE.md`
- `docs/data_capabilities/twse_mis_rich_field_inventory.json`

## 3. Scope

Allowed in M7D-00/M7D-01:
- define bounded watchlist cross-context policy
- define 19-item coverage catalog
- define schema
- define required inputs
- define grouping dimensions
- define availability summaries
- define comparison semantics
- define quality gates
- define forbidden interpretations
- define future builder requirements

Not allowed in M7D-00/M7D-01:
- builder
- calculations
- runtime integration
- conversation context integration
- FastAPI/MCP/frontend integration
- source-health integration
- source discovery
- live probe

## 4. Boundedness policy

All M7D outputs are bounded to the currently configured watchlist and latest observation payload.
M7D must never generalize bounded watchlist observations to the whole Taiwan market.
M7D must label all breadth-like counts as bounded_watchlist_only.

## 5. Required 19-item coverage catalog

| id | name | scope_status | description | allowed_interpretation | forbidden_interpretation | depends_on | m7d_schema_group |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bounded_observed_market_snapshot | Bounded observed market snapshot | in_scope_m7d | Summary of the currently observed watchlist payload only. | Describes only items in the configured watchlist/latest observation payload. | Must not imply full market coverage or market-wide direction. | latest_observation_payload | watchlist_observation_coverage |
| current_price_state | Current price state | referenced_dependency | Latest observed price state per watchlist item. | M7D may aggregate availability but must not redefine price semantics. | Must not reinterpret reference values as current market data. | M7A/M7B/M7C | watchlist_observation_coverage |
| session_position | Session position | deferred_m7e | Whether current observation is preopen/intraday/closed/stale/session-relative. | Deferred until a market clock/session-state policy exists. | Must not implement session clock now. | M7E_market_clock | quality_gate_policy |
| market_index_context | Market index context | in_scope_m7d | Bounded relationship to index-like watchlist items such as TAIEX if present. | Only if an index item is in the current watchlist and has observation/metrics. | Must not infer market prediction or full Taiwan market direction. | watchlist_config/M7C | index_relative_context |
| futures_context | Futures context | in_scope_m7d | Bounded relationship to TAIFEX/TX-like watchlist items if present. | Compare only against futures-like items present in the same watchlist. | Must not infer basis, fair value, or futures-led direction unless explicitly supported. | watchlist_config/M7C | futures_relative_context |
| watchlist_breadth | Watchlist breadth | in_scope_m7d | Positive/negative/flat/degraded/failed/reference-only counts within current watchlist. | Must be called bounded watchlist breadth. | Must not be called market breadth or generalized to full market breadth. | M7C | bounded_breadth_summary |
| cross_instrument_differences | Cross-instrument differences | in_scope_m7d | Factual comparison of watchlist items by deterministic metrics such as change_percent. | Descriptive comparison among observed watchlist items. | No ranking as recommendation. | M7C | bounded_relative_change_summary |
| current_volume_observations | Current volume observations | referenced_dependency | Bounded observation of current volume fields if available. | M7D may summarize availability while preserving upstream caveats. | Must not treat volume as capital flow. | M7A/M7B/M7C | watchlist_observation_coverage |
| displayed_order_book_depth_snapshot | Displayed order book depth snapshot | referenced_dependency | Displayed top-5 quote/depth context from M7C metrics. | Displayed snapshot only. | Must not infer true liquidity, full order book, support/resistance, or main force. | M7C | bounded_relative_change_summary |
| source_freshness_delay_failure | Source freshness delay failure | in_scope_m7d | Count/summarize fresh/degraded/stale/failed observations. | Use existing freshness/source-health semantics only. | Must not invent market timing. | latest_observation_payload | source_freshness_summary |
| missing_fields_context | Missing fields context | in_scope_m7d | Summarize missing required context fields across watchlist items. | Descriptive only. | Must not convert missingness into direction or recommendation. | M7B/M7C | missing_context_summary |
| stale_observations_context | Stale observations context | in_scope_m7d | Identify stale/reference-only/degraded observations inside bounded watchlist. | Describes quality/freshness limitations. | Do not call stale market direction. | latest_observation_payload | degraded_context_summary |
| official_eod_context | Official EOD context | deferred_m8 | Official TWSE/TPEx/TAIFEX EOD reference baseline. | Deferred official EOD/reference context. | Do not implement official EOD in M7D. | M8_official_eod_context | quality_gate_policy |
| recent_historical_context | Recent historical context | deferred_m8 | 5D/20D or recent historical baseline. | Deferred historical context. | Do not implement history in M7D. | M8_recent_history | quality_gate_policy |
| source_health_caveats | Source health caveats | referenced_dependency | Existing source-health caveats reflected in bounded context. | Reference existing caveats without changing behavior. | M7D should not change source-health behavior in M7D-00/01. | source_health_summary | source_freshness_summary |
| data_provenance | Data provenance | referenced_dependency | Source, adapter, retrieved_at, evidence lineage. | Schema includes provenance_summary placeholders. | Must not fabricate lineage. | latest_observation_payload | provenance_summary |
| semantic_limitations | Semantic limitations | in_scope_m7d | Explicit limitations and forbidden interpretations. | Required caveats for future output. | Must not omit no-go caveats. | none | semantic_limitations |
| frontend_operator_presentation | Frontend operator presentation | deferred_m7f | Frontend/operator card, workbench layout, copy-to-AI rendering. | Deferred product surface work. | Do not build frontend in M7D. | M7F_frontend_operator_presentation | quality_gate_policy |
| ai_discussion_handoff | AI discussion handoff | in_scope_m7d | AI-readable bounded cross-context package. | Schema only in M7D-00/01; actual controlled exposure deferred to M7D-04. | Must not expose M7D to conversation context before controlled integration. | M7D-04 | semantic_limitations |

## 6. Allowed grouping dimensions

Allowed grouping dimensions:
- market
- source
- adapter_id
- instrument_type
- category
- watchlist_group
- observation_status
- freshness_status
- reference_only_status
- has_m7b_projection
- has_m7c_metrics

Industry and sector grouping are deferred unless currently present in watchlist metadata. Capital flow and market-wide breadth are not M7D grouping dimensions.

## 7. Allowed summaries

Allowed summary families:
- watchlist_observation_coverage
- bounded_breadth_summary
- bounded_relative_change_summary
- index_relative_context
- futures_relative_context
- etf_group_context
- source_freshness_summary
- missing_context_summary
- degraded_context_summary
- provenance_summary
- semantic_limitations

## 8. Quality gates

M7D quality status values:
- schema_only
- not_computed
- computed
- blocked_missing_watchlist
- blocked_missing_latest_observation
- blocked_missing_m7c_metrics
- blocked_insufficient_observed_items
- blocked_quality_flags
- blocked_deferred_dependency

## 9. Allowed descriptive language

Allowed examples:
- 在目前 watchlist 中
- 在目前已觀測標的中
- bounded watchlist only
- 目前觀察清單中 N 檔有有效觀測
- 目前觀察清單中 N 檔缺少可比較 metrics
- 目前觀察清單中 change_percent 較高者為...
- 目前觀察清單中 TAIEX 與 2330 的方向一致 / 不一致

## 10. Forbidden interpretations

Forbidden:
- full market breadth
- market-wide trend
- sector rotation
- capital flow
- main force
- buy signal
- sell signal
- recommendation
- buy/sell/hold
- target price
- support
- resistance
- breakout
- breakdown
- true liquidity
- full order book
- prediction
- confirmation

## 11. Naming policy

Schema names must not include unbounded positive labels such as signal, strength, pressure, support, resistance, breakout, breakdown, main_force, capital_flow, market_breadth, or sector_rotation except as explicit negated caveats, forbidden_interpretation text, or blocked_interpretations.

Use bounded names:
- bounded_watchlist_breadth
- bounded_relative_change
- bounded_index_relative_context
- bounded_futures_relative_context

## 12. M7D planned sequence

- M7D-00: bounded watchlist cross-context policy / scope / guardrails
- M7D-01: bounded watchlist cross-context schema
- M7D-02: pure bounded cross-context builder
- M7D-03: fixtures and safety tests
- M7D-04: controlled integration / compatibility / closure
