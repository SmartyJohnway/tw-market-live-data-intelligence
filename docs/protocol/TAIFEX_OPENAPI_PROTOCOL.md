# TAIFEX OpenAPI Protocol

## Purpose

`TAIFEX_OpenAPI` is registered as a distinct official TAIFEX OpenAPI/OAS source family for endpoint inventory and source-contract preflight. It is not a runtime market observation source in this repository.

## Official endpoint metadata

- Official catalog URL: `https://openapi.taifex.com.tw/`
- Official OAS URL inspected: `https://openapi.taifex.com.tw/swagger.json`
- OAS title observed: `臺灣期貨交易所 OAS`
- OAS version observed: OpenAPI `3.0.0`, API metadata version `1.0.0`
- Server observed in schema: `https://openapi.taifex.com.tw/v1`
- Paths observed in schema: 135
- Response media advertised for relevant endpoints: `application/json` and `text/csv`
- Parameters observed for inventoried GET operations: none in the OAS operation metadata inspected.

## Source-family distinction vs TAIFEX_MIS

| Source family | Current repository role | Runtime integrated? | Timing semantics | Notes |
| --- | --- | ---: | --- | --- |
| `TAIFEX_MIS` | Bounded intraday/front-month TX observation candidate using TAIFEX MIS browser JSON | Yes | `live_or_intraday` candidate with caveats | Existing parser and adapter path are unchanged by this registration. |
| `TAIFEX_OpenAPI` | Official OAS/OpenAPI endpoint inventory and contract preflight | No | Official daily/statistical/reference/historical candidate; not live unless separately proven | This task does not authorize runtime use. |

## Authority class

`authority_class: official_openapi` because the inspected metadata is hosted under TAIFEX's official OpenAPI domain and identifies itself as the Taiwan Futures Exchange OAS information service.

## Timing class decision

Overall timing class is `official_statistical` with endpoint-level classes of `official_daily`, `official_statistical`, `official_reference`, or `historical`. The OAS schema exposes report-style endpoints such as daily futures/options market reports, Put/Call Ratio, institutional trader reports, large-trader open-interest reports, daily FX reference rates, final settlement prices, margin references, and daily time-and-sales files. The schema alone does not prove realtime service levels, so no endpoint is classified as realtime or live.

## Endpoint inventory summary

The machine-readable inventory is maintained in `docs/data_capabilities/taifex_openapi_endpoint_inventory.json`. Materially relevant endpoint categories inventoried are:

- `futures_daily_quote`
- `options_daily_quote`
- `put_call_ratio`
- `institutional_investor_futures`
- `institutional_investor_options`
- `large_trader_open_interest`
- `settlement_or_reference`
- `foreign_exchange_reference`
- `historical_time_and_sales`
- `margin_or_fee_reference`
- plus deferred administrative/statistical categories.

Representative paths include `/DailyMarketReportFut`, `/DailyMarketReportOpt`, `/PutCallRatio`, `/MarketDataOfMajorInstitutionalTradersDetailsOfFuturesContractsBytheDate`, `/OpenInterestOfLargeTradersFutures`, `/DailyForeignExchangeRates`, `/FinalSettlementPrice`, `/TimeAndSalesData`, and `/OptionsTimeAndSalesData`.

## Parameter model summary

The inspected OAS operations for the inventoried paths are `GET` operations with no operation parameters listed. This should not be interpreted as proof that the service is complete for all filtering use cases; any future M8 contract must validate query behavior, row limits, freshness, and date coverage explicitly.

## Response-shape summary

The relevant schemas are object-shaped report rows with string fields. Examples include:

- Futures daily report fields: `Date`, `Contract`, `ContractMonth(Week)`, `Open`, `High`, `Low`, `Last`, `Volume`, `SettlementPrice`, `OpenInterest`, `BestBid`, `BestAsk`.
- Options daily report fields: `Date`, `Contract`, `StrikePrice`, `CallPut`, `Open`, `High`, `Low`, `Close`, `Volume`, `SettlementPrice`, `OpenInterest`.
- Put/Call Ratio fields: `Date`, `PutVolume`, `CallVolume`, `PutCallVolumeRatio%`, `PutOI`, `CallOI`, `PutCallOIRatio%`.
- Institutional and large-trader fields include long/short volume, value, and open-interest counts.

## Semantic caveats

Official OpenAPI does not mean current live observation. These endpoints are report/statistical/reference candidates unless future evidence proves otherwise and a later milestone explicitly accepts the semantics. Derivatives statistics can be descriptive context, but they must not be phrased as predictions, recommendations, or trading signals.

## Allowed use

- Official TAIFEX OpenAPI / OAS source inventory.
- Official derivatives EOD/statistical context planning.
- Official reference context planning.
- Contract preflight and documentation.
- Future M8 normalized context design after freshness validation.

## Forbidden use

- Runtime FastAPI, MCP, frontend, scheduler, or startup network integration from this task.
- Live observation claims.
- Replacing or merging `TAIFEX_MIS`.
- Buy/sell/hold, target price, support/resistance, leading/contrarian indicator, or predictive institutional-flow language.

## M7/M8/M9 recommendation

- M7: register only; keep non-runtime and separate from `TAIFEX_MIS`.
- M8: consider official derivatives EOD/statistical/reference context after field-level validation.
- M9: keep interpretation-heavy sentiment/cross-market narratives research-only with strict semantic guardrails.

## Evidence references

- `https://openapi.taifex.com.tw/swagger.json`
- `docs/data_capabilities/taifex_openapi_endpoint_inventory.json`
- `docs/m5l_taifex_live_source_validation.md`
- `config/m5l_live_source_adapter_matrix.json`
