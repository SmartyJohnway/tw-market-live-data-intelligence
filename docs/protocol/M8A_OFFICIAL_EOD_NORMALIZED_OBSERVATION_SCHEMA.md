# M8A official EOD normalized observation schema

Status: m8a_00_official_eod_adapter_scope_and_contract_preflight_complete
Generated: 2026-07-11T10:24:35Z
Next task: M8A-01-03-OFFICIAL-EOD-ADAPTERS-CONTEXT-INTEGRATION-AND-FINAL-ACCEPTANCE


Schema version: `m8a_official_eod_observation.v1`.

## Required top-level fields
`schema_version`, `source_id`, `endpoint_contract_id`, `authority_level`, `timing_class`, `market`, `symbol`, `name`, `instrument_type`, `trade_date`, `retrieved_at_utc`, `source_status`, `observation_status`, `currency`, `price`, `activity`, `field_validation`, `source_fields_present`, `omitted_source_fields`, `derived_fields`, `caveats`, `provenance`.

## Example shape
```json
{"schema_version":"m8a_official_eod_observation.v1","source_id":"TWSE_OPENAPI","endpoint_contract_id":"twse_openapi_stock_day_all_v1","authority_level":"official_documented","timing_class":"official_eod","market":"listed","symbol":"2330","name":"台積電","instrument_type":"equity","trade_date":"2026-07-09","retrieved_at_utc":"2026-07-11T10:24:35Z","source_status":"ok","observation_status":"complete","currency":"TWD","price":{"open":null,"high":null,"low":null,"close":null,"previous_close":null,"change":null,"change_percent":null},"activity":{"trade_volume":null,"trade_value":null,"transaction_count":null},"field_validation":{},"source_fields_present":[],"omitted_source_fields":[],"derived_fields":[],"caveats":[],"provenance":{}}
```

## Source identity
`source_id` is `TWSE_OPENAPI` or `TPEX_OPENAPI`; `endpoint_contract_id` is the selected contract ID. Authority is `official_documented`; timing class is `official_eod`.

## Market/symbol identity
Canonical identity is `(market, symbol)` with market values `listed` and `tpex_otc`. Symbol alone is invalid identity.

## Row validity
A valid complete row has identity, trade date, instrument classification, close, and all core activity fields valid. A valid partial row has identity and date but one or more nullable numeric fields missing/invalid with field_validation caveats. A no-trade row is valid when source markers or zeros indicate no activity without malformed identity/date. A suspended row is valid partial unless source status means the row is not a trade observation. Unclassified instrument rows are retained with caveat but excluded from deterministic metrics/AI context by default. Invalid identity/date rows are rejected. Invalid numeric fields are omitted field-by-field unless required for the selected context.

## Batch validity
Statuses: successful batch, successful empty batch, partial batch, source-declared error, HTTP error, schema drift, duplicate row, mixed-date response, requested-date mismatch.

## Numeric policy
Use Decimal-compatible strings/Decimal for prices and change; integers for volume, value, transaction_count after comma removal. Do not use float for persisted contract values. Missing markers: empty, `-`, `--`, `---`. Preserve negative signs and leading plus signs. Malformed numbers are not silently coerced. Overflow fails field validation.

## Price/activity structures
`price` contains source-reported `open`, `high`, `low`, `close`, source-reported `change`, derived `previous_close`, derived/deferred `change_percent`. `activity` contains `trade_volume`, `trade_value`, `transaction_count`.

## Validation and provenance
`field_validation` records per-field parse/validation status. `provenance` includes documentation URL, endpoint URL, retrieval time, endpoint contract ID, source row Date, and parser version.

## Partial-row policy
Partial rows may enter safe artifacts with caveats. AI context eligibility requires valid identity/date plus at least one valid factual field and source/instrument policy approval. Invalid numeric fields are omitted while valid fields remain.

## Raw payload policy
Full raw payloads and cookies/session values are forbidden in normalized observations. Allowed: `source_fields_present`, omitted field names, compact provenance, and tiny debug evidence in explicit probe artifacts.

## Derivation policy
`change` is source-reported. `previous_close` is derived only when `close` and `change` are valid: `previous_close = close - change`; record in `derived_fields`. `change_percent` is deferred initially; if enabled later, denominator must be derived previous_close and zero/undefined must produce null.
