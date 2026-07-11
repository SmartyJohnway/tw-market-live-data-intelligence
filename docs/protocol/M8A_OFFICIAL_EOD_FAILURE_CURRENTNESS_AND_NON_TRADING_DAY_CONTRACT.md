# M8A official EOD failure, currentness, and non-trading-day contract

Status: m8a_00_official_eod_adapter_scope_and_contract_preflight_complete
Generated: 2026-07-11T10:24:35Z
Next task: M8A-01-03-OFFICIAL-EOD-ADAPTERS-CONTEXT-INTEGRATION-AND-FINAL-ACCEPTANCE


## Required classifications
- `empty_non_trading_day`: HTTP 200/schema-valid empty result with requested/expected holiday or no trading-day evidence.
- `source_unavailable`: DNS, network failure, timeout, TLS failure.
- `source_error`: HTTP 4xx/5xx or official status/error object.
- `schema_drift`: JSON parse succeeds/fails but top-level or required fields do not match contract.
- `date_mismatch`: reported Date differs from requested/expected trade date when a requested date contract exists or calendar says latest should differ.
- `valid_zero_trade_row`: identity/date valid and activity zero/markers represent no trade or suspension-like source row.
- `successful_eod_batch`: HTTP 200 JSON array with one or more contract-valid rows.
- `partial_source_success`: one source succeeds and one source fails, or a batch has accepted rows plus rejected rows.

## Failure behavior
Network failures do not erase existing context; mark source unavailable. HTTP 4xx/5xx are source_error. JSON parse failure or missing required row fields is schema_drift. Duplicate `(market, symbol, trade_date)` rows fail closed for that identity. Mixed dates produce partial batch or schema_drift depending on severity.

## Currentness
`trade_date` is the market date from source row Date after ROC conversion. `retrieved_at_utc` is only retrieval time. EOD rows are never realtime/current price. M8 freshness evaluator should compare trade_date with Taiwan calendar/session and classify stale official EOD context without treating retrieval time as freshness of market value. Runtime must compute `expected_latest_completed_trade_date` from Taiwan-local probe time using an authority model that separates `scheduled_calendar_status` (`scheduled_trading_day`, `scheduled_holiday`, `weekend`), `emergency_closure_status` (`no_emergency_closure_found`, `emergency_closure_confirmed`, `emergency_closure_unknown`), and `actual_market_day_status` (`actual_trading_day`, `emergency_closed`, `unresolved`). Required inputs are weekend, scheduled holiday, makeup trading policy, emergency natural-disaster closure, and exchange-specific special closure. Annual holidaySchedule absence must never by itself prove `actual_trading_day`.

## Non-trading day behavior
Selected latest endpoints have no documented date parameter; weekend/holiday is inferred when latest `trade_date` remains prior trading day. Do not classify latest prior trading day as source_unavailable. If an emergency market closure is confirmed, derive expected latest completed trade date from the previous actual trading day and use `matches_expected_latest_trade_date_after_emergency_closure` when reported date matches. If reported trade_date is one trading day behind an evidence-proven actual trading day, classify currentness reconciliation as `delayed_one_trading_day`; if farther behind, classify as `stale_official_eod`; if emergency/special-closure evidence is unavailable, set `emergency_closure_status = emergency_closure_unknown`, `actual_market_day_status = unresolved`, and classify as `unresolved_date_mismatch` rather than definitive delayed status. If future historical/date endpoints are added, empty holiday responses become `empty_non_trading_day`, not source_error.

## One-source failure policy
TWSE succeeds/TPEx fails or TPEx succeeds/TWSE fails => `partial_source_success`; preserve successful source observations independently with caveats. Official EOD must not overwrite TWSE_MIS live-ish fields, and live-ish context must not rewrite official EOD trade_date.
