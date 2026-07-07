# M7C deterministic metrics policy

## 1. Purpose

M7C moves deterministic arithmetic out of AI free-form reasoning and into tested, policy-gated code. It defines factual, arithmetic metrics that can later be computed from already-normalized observations and/or M7B AI-safe projection candidates.

M7C does not discover new data sources, does not validate a new source, and does not change source freshness governance. M7C is deterministic metrics policy and schema, not multi-source/source-freshness governance, not a trading-signal layer, and not a recommendation layer.

## 2. Dependency

M7C depends on M7B final acceptance: `pass_with_caveats`.

Authoritative dependency references:

- `docs/protocol/M7B_AI_SAFE_MARKET_CONTEXT_FINAL_ACCEPTANCE.md`
- `docs/protocol/M7B_AI_SAFE_MARKET_CONTEXT_PROJECTION_POLICY.md`
- `docs/data_capabilities/twse_mis_rich_field_inventory.json`

## 3. Scope

Allowed in M7C:

- define deterministic metrics policy
- define metrics schema
- define required inputs
- define quality gates
- define blocked interpretations
- define future pure builder requirements

Not allowed in M7C-00/M7C-01:

- calculation builder
- runtime integration
- conversation context integration
- FastAPI/MCP/frontend integration
- source-health integration
- source discovery
- live probe

## 4. Metric families

Allowed metric families:

- `price_change_metrics`
- `intraday_range_metrics`
- `open_high_low_position_metrics`
- `displayed_quote_spread_metrics`
- `displayed_depth_balance_metrics`
- `data_quality_metrics`
- `caveat_context`

## 5. Required input policy

Price metrics require:

- `last_value`
- `previous_close`
- `open`
- `high`
- `low`

Displayed spread metrics require:

- `best_bid`
- `best_ask`

Displayed depth balance metrics require `sanitized_top5_bid_quantities` and `sanitized_top5_ask_quantities`, or safe local builder inputs derived from M7A/M7B displayed-depth snapshot facts that pass quality gates. The builder must not expose raw `bid_prices`, `ask_prices`, `bid_quantities_raw`, `ask_quantities_raw`, or full ladder arrays in the M7C output.

Quality flags must be checked before metrics are considered available.

## 6. Quality gate policy

Metric status values:

- `schema_only`
- `not_computed`
- `computed`
- `blocked_missing_required_fields`
- `blocked_quality_flags`
- `blocked_zero_denominator`
- `blocked_non_numeric`

Rules:

- compute only when required fields are present
- compute only when fields are numeric
- block division by zero
- block if malformed fields affect required inputs
- block if ladder mismatch affects displayed-depth metrics
- block if `reference_only` means `last_value` is not an actual current/last trade candidate
- keep per-metric availability and `blocked_reason`

## 7. Allowed descriptive language

Allowed AI wording after a future controlled integration may include:

- 位於今日觀測區間上緣
- 位於今日觀測區間下緣
- 距離今日高點約 X%
- 距離今日低點約 X%
- 相對昨日收盤變動 X%
- 相對開盤變動 X%
- displayed quote spread
- displayed depth ratio
- displayed bid-side / ask-side snapshot

## 8. Forbidden interpretations

Forbidden interpretations:

- signal
- buy signal
- sell signal
- recommendation
- buy/sell/hold
- target price
- support
- resistance
- breakout
- breakdown
- pressure
- main force
- true liquidity
- full order book
- execution liquidity
- predictive label
- trend confirmation

## 9. Naming policy

Strict naming policy: metric names must not include:

- `signal`
- `strength`
- `pressure`
- `support`
- `resistance`
- `breakout`
- `breakdown`
- `main_force`
- `liquidity_signal`

Allowed names should be factual and deterministic. `position_in_day_range`, `distance_from_high_percent`, and `distance_from_low_percent` are descriptive only. `displayed_spread` is displayed quote spread, not full-market liquidity. `top5_displayed_bid_volume` and `top5_displayed_ask_volume` are displayed depth sums only, not true order-book depth.

## M7C-02/M7C-03 status

M7C-02 defines a pure deterministic metrics builder but does not integrate it with runtime consumers. M7C-03 adds fixture and safety tests.

The builder output may contain `runtime_computed_candidate` metric values, but repository runtime exposure remains disabled. `safe_for_ai_context` remains false until M7C-04 controlled integration explicitly changes downstream policy.

Displayed-depth balance metrics consume sanitized top-5 displayed quantity inputs derived from M7A/M7B displayed-depth snapshot facts. The builder must not expose raw `bid_prices`, `ask_prices`, `bid_quantities_raw`, `ask_quantities_raw`, or full ladder arrays in the M7C output.

Do not mark M7C complete yet.

## 10. M7C planned sequence

- M7C-00: metrics policy / scope / guardrails
- M7C-01: deterministic metrics schema
- M7C-02: pure metrics builder
- M7C-03: fixtures and safety tests
- M7C-04: controlled integration / compatibility / closure
