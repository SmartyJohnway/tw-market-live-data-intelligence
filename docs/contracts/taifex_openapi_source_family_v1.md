# TAIFEX OpenAPI Source Family Contract v1

## Contract status

Draft source-family registration and contract preflight for `TAIFEX_OpenAPI`.

## Scope

This contract registers `TAIFEX_OpenAPI` as an official OpenAPI/OAS source family for TAIFEX derivatives report, statistical, reference, and historical endpoint inventory.

## Non-runtime boundary

This is not runtime-integrated. This is not `TAIFEX_MIS`. This is not live-observation. This task does not authorize runtime use.

No FastAPI endpoint, MCP tool, frontend fetch, scheduler, startup network call, automatic polling, or production observation path is created by this contract.

## Classification

- `source_id`: `TAIFEX_OpenAPI`
- `authority_class`: `official_openapi`
- `runtime_integrated`: `false`
- `live_observation_enabled`: `false`
- `network_calls_in_runtime`: `false`
- Overall timing: official daily/statistical/reference/historical candidate; not realtime.
- Candidate milestone: `M7_or_M8_decision_pending`

## Distinction from TAIFEX_MIS

`TAIFEX_MIS` remains the existing bounded intraday TX/front-month observation candidate. `TAIFEX_OpenAPI` is an official OAS report inventory and future EOD/statistical/reference context candidate. The two source families must not share parser semantics, source IDs, runtime adapters, or freshness claims.

## Candidate normalized contexts

TAIFEX_OpenAPI currently has no normalized retained fields in this repository; the endpoint inventory records source/OAS field excerpts only. Future normalized contexts may include futures/options daily report rows, settlement/reference rows, daily FX reference rows, Put/Call Ratio rows, institutional trader rows, large-trader open-interest rows, and historical time-and-sales rows. Any future implementation must define source time, exchange time, retrieval time, delay/freshness status, units, field lifecycle, and semantic caveats before exposure.

## Semantic guardrails

Allowed language: official TAIFEX OpenAPI/OAS source, official derivatives EOD/statistical context, official reference context, descriptive derivatives statistics, not current live observation, not trading signal, not realtime SLA.

Forbidden language: leading indicator, contrarian indicator, support/resistance, buy signal, sell signal, hold, target price, foreign investors are definitely suppressing the market, retail traders are definitely wrong, Put/Call Ratio proves support or pressure, institutional positions predict tomorrow's market.
