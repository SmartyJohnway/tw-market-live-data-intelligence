# Source Adapter Architecture

Source adapters converge source-specific evidence into shared route, observation, and failure contracts.

## Practical interface

A source adapter is represented by:

- an adapter id in `config/m5l_live_source_adapter_matrix.json`,
- a route plan returned by `source_plan_for_instrument()`,
- source-specific fetch code when explicit execution is allowed,
- shared normalization helpers in `scripts/observation_contract.py`.

## Current adapters

- `twse_mis_equity_etf_quote`
- `twse_mis_taiex_index_quote`
- `taifex_mis_tx_futures_quote`

## Convergence rule

Adapters may differ in request mechanics, but they must emit the same observation/failure contract. Source-specific frontend rendering should be avoided; frontend and API clients should inspect shared fields such as `source`, `adapter_id`, `freshness_assessment`, `delay_status`, `contract`, `reference_only`, `price_like_value`, and `failures`.
