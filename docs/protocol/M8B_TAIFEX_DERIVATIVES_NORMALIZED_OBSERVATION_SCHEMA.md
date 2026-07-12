# M8B TAIFEX derivatives normalized observation schema

Status: m8b_00_preflight_contract_complete_adapter_pending
Schema version: `m8b_taifex_derivatives_eod_observation.v1`.

## Purpose and boundary
This schema is for official TAIFEX OpenAPI derivatives EOD context only. It is not realtime, not TAIFEX_MIS, not a production adapter, and not a trading-signal schema.

## Required top-level fields
`schema_version`, `source_id`, `endpoint_contract_id`, `authority_level`, `timing_class`, `market`, `instrument_type`, `product_id`, `product_name`, `contract_identity`, `trade_date`, `retrieved_at_utc`, `source_status`, `observation_status`, `session`, `currency`, `price`, `activity`, `open_interest`, `field_validation`, `source_fields_present`, `omitted_source_fields`, `derived_fields`, `caveats`, and `provenance`.

```json
{"schema_version":"m8b_taifex_derivatives_eod_observation.v1","source_id":"TAIFEX_OPENAPI","endpoint_contract_id":"taifex_openapi_daily_market_report_fut_v1","authority_level":"official_documented","timing_class":"official_derivatives_eod","market":"taifex","instrument_type":"futures","product_id":"TX","product_name":null,"contract_identity":{"identity_type":"taifex_futures_contract.v1","product_id":"TX","contract_month":"202607","contract_code":null,"expiry_date":null},"trade_date":"2026-07-09","retrieved_at_utc":"2026-07-12T02:36:27Z","source_status":"ok","observation_status":"complete","session":"regular","currency":"TWD","price":{"open":null,"high":null,"low":null,"close":null,"last":null,"settlement":null,"reference":null,"change":null,"change_percent":null,"limit_up":null,"limit_down":null},"activity":{"volume":null,"trade_value":null,"transaction_count":null},"open_interest":{"open_interest":null,"open_interest_change":null},"field_validation":{},"source_fields_present":[],"omitted_source_fields":[],"derived_fields":[],"caveats":[],"provenance":{}}
```

## Futures identity
Futures identity uses `taifex_futures_contract.v1` with `product_id`, `contract_month`, optional `contract_code`, and optional `expiry_date`. Required unique key: `market + instrument_type + product_id + contract_month + session + trade_date`. Symbol-only identity is invalid.

## Options identity
Options identity uses `taifex_option_contract.v1` with `product_id`, `contract_month`, `strike_price`, `option_type`, optional `contract_code`, and optional `expiry_date`. Required unique key: `market + instrument_type + product_id + contract_month + strike_price + option_type + session + trade_date`. `CallPut` must map from official source values such as `買權` and `賣權`; do not guess option type from names.

## Session
Source field `TradingSession` was observed. Known observed regular value is `一般`; it maps to `regular` only after adapter validation. If missing or unmapped, use `unknown` with caveat `session_semantics_unresolved`; missing session is not a source error.

## Price semantics
Required price object:
```json
{"open":null,"high":null,"low":null,"close":null,"last":null,"settlement":null,"reference":null,"change":null,"change_percent":null,"limit_up":null,"limit_down":null}
```
Rules: `settlement != close`; `reference != last`; `last != close` unless source explicitly defines it. Futures `Last` maps to `price.last`; options source `Close` is documented as final traded price and maps to `price.last`, not generic close. Daily `SettlementPrice` remains `price.settlement`. `TheFinalSettlementPrice` is expiry final settlement, not daily settlement. Use Decimal-compatible strings, never floats. Negative prices are invalid; signed change is allowed when source-reported.

## Activity and open interest
`activity.volume` is contract count from `Volume`; `trade_value` and `transaction_count` are null unless official fields are selected later. `open_interest.open_interest` is contract count from `OpenInterest`; `open_interest_change` is null unless source-reported. Units remain `contracts` for volume/open interest.

## Validation and raw payload policy
Identity/date failures reject the row. Optional malformed numeric fields produce partial rows unless required by a selected context. Duplicate derivative contract identity fails closed for that identity. Full raw payload retention is forbidden; compact field names, counts, sample rows, and provenance are allowed in preflight evidence.
