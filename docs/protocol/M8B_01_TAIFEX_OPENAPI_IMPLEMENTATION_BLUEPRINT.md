# M8B-01 TAIFEX OpenAPI implementation blueprint

Next PR: `M8B-01-TAIFEX-OPENAPI-OFFICIAL-DERIVATIVES-EOD-ADAPTERS-AND-CONTEXT-INTEGRATION`.

Implement `scripts/m8b_taifex_derivatives_observation.py`, `scripts/m8b_taifex_openapi_futures_adapter.py`, `scripts/m8b_taifex_openapi_options_adapter.py`, `scripts/m8b_taifex_openapi_execution.py`, and `scripts/validate_m8b_taifex_openapi_live.py`. A unified low-level fetch helper is acceptable, but futures/options parsers should stay separate because option identity requires strike and call/put.

Required behavior: explicit operator confirmation; selected products/contracts; bounded retained scope; no full raw payload retention; no scheduler, polling, startup fetch, or DB write; normalized derivatives observations; futures context projection; options context projection only when identity is robust; source-specific currentness; conversation projection; README/source registry update; final acceptance.

Suggested commits: (1) derivatives observation and parser helpers, (2) futures/options adapters and fixtures, (3) controlled execution and M8 context integration, (4) conversation projection, README, live validation, final acceptance.


## Implementation matrix

| Endpoint | Context type | Readiness | Implement in M8B-01? | Parser module | Projection type | Caveats |
|---|---|---|---|---|---|---|
| DailyMarketReportFut | official_derivatives_futures_eod_reference | go | yes | `scripts/m8b_taifex_openapi_futures_adapter.py` | bounded futures EOD observation/context | whole-endpoint fetch with bounded retention; no runtime in M8B-00 |
| DailyMarketReportOpt | official_derivatives_options_eod_reference | conditional_go | yes | `scripts/m8b_taifex_openapi_options_adapter.py` | bounded options EOD observation/context | option `Close` maps to `price.close` until official last-price evidence exists; identity validation required |
| FinalSettlementPrice | official_derivatives_final_settlement_reference | conditional_go | yes | `scripts/m8b_taifex_openapi_final_settlement_adapter.py` or shared settlement parser | final settlement reference | expiry final settlement only; no daily volume/open-interest/session |
| OpenInterestOfLargeTradersFutures | official_derivatives_large_trader_open_interest_reference | conditional_go | yes | `scripts/m8b_taifex_openapi_large_trader_oi_adapter.py` | factual large-trader OI reference | no bullish/bearish signal or recommendation; TypeOfTraders code validation required |
| OpenInterestOfLargeTradersOptions | official_derivatives_large_trader_open_interest_reference | conditional_go | yes | `scripts/m8b_taifex_openapi_large_trader_oi_adapter.py` | factual large-trader OI reference | option CallPut mapping must fail closed on unknown values |
| PutCallRatio | official_derivatives_put_call_ratio_reference | conditional_go | yes | `scripts/m8b_taifex_openapi_put_call_ratio_adapter.py` | factual put/call ratio reference | ratio is context only, not sentiment/signal scoring |
| BlockTrade | official_derivatives_block_trade_reference | conditional_go | yes | `scripts/m8b_taifex_openapi_block_trade_adapter.py` | factual block-trade activity reference | no strategy interpretation; bounded product retention |
| ContractAdj | official_derivatives_contract_adjustment_reference | conditional_go | defer unless needed by selected-contract identity normalization | `scripts/m8b_taifex_openapi_contract_metadata_adapter.py` | product/contract adjustment metadata | field `Contact`/identity semantics require separate review |
| productsExemptedAH | official_derivatives_after_hours_product_reference | conditional_go | defer unless needed for session/product metadata | `scripts/m8b_taifex_openapi_contract_metadata_adapter.py` | product/session metadata | not a trading calendar; after-hours liquidation exemption semantics only |
| Trading calendar | official_derivatives_trading_calendar_reference | blocked/unresolved | no | none | none | no official TAIFEX OpenAPI trading-calendar endpoint identified in bounded Swagger discovery |

All M8B-01 implementations must preserve explicit operator confirmation, bounded retained scope, no full raw payload retention, no scheduler/polling/startup fetch, no DB write, no TAIFEX_MIS, no Yahoo, no FinMind, no recommendations, and no model calls.
