# M8B TAIFEX derivatives currentness, session, and failure contract

Official TAIFEX OpenAPI derivatives EOD is not realtime. `retrieved_at_utc` is fetch time only and must never be treated as market value freshness. The source `Date` field is the market trade date for daily report rows; `TheFinalSettlementDay` is final settlement date for expiry settlement rows.

## Currentness statuses
- `current_official_derivatives_eod`
- `matches_expected_latest_trade_date_after_emergency_closure`
- `delayed_one_trading_day`
- `stale_official_derivatives_eod`
- `unresolved_date_mismatch`
- `session_semantics_unresolved`

Weekend latest-prior-date behavior is acceptable when the reported TAIFEX trade date equals the expected latest completed TAIFEX trading day. Emergency closure can explain a previous date, but TAIFEX currentness remains source-specific: do not force TAIFEX to match TWSE/TPEx if the official derivatives endpoint reports a different latest date. M8A NCDR/DGPA Taipei closure evidence may be relevant because Taiwan exchange closures often follow Taipei public-agency closure rules, but TAIFEX-specific special-closure differences remain unresolved until separately documented.

## Session and night-session caveat
`TradingSession` is source-reported on selected daily quote endpoints. Preflight observed `一般` rows. The next adapter must preserve the raw source session label and map only documented/validated labels to `regular`, `after_hours`, or `combined`. If session is absent or unmapped, set session to `unknown` and caveat `session_semantics_unresolved`; this is not schema drift.

## Settlement timing
Daily `SettlementPrice` is an official EOD settlement value and is distinct from last traded price. `FinalSettlementPrice` is final expiry settlement and should be projected separately from daily settlement context.

## Failure classifications
- `successful_derivatives_eod_batch`
- `empty_non_trading_day`
- `source_unavailable`
- `source_error`
- `schema_drift`
- `identity_parse_failure`
- `date_mismatch`
- `partial_source_success`
- `valid_zero_trade_contract`
- `unresolved_session_semantics`

HTTP/network failure maps to `source_unavailable` or `source_error`. Schema drift fails closed. Missing identity fields map to `identity_parse_failure`. Missing optional price/activity fields produce partial rows. Duplicate derivative contract identity fails closed for that identity. Mixed dates are `date_mismatch` or `partial_source_success` by severity. Zero volume with valid identity/date is `valid_zero_trade_contract`. Missing session yields unknown session and a caveat, not source error.

## M8B-03 runtime status enum reconciliation

The runtime TAIFEX adapter/execution failure-status set is exactly:

- `successful_derivatives_eod_batch`
- `empty_non_trading_day`
- `source_unavailable`
- `source_error`
- `schema_drift`
- `identity_parse_failure`
- `invalid_required_fields`
- `date_mismatch`
- `partial_source_success`
- `valid_zero_trade_contract`
- `unresolved_session_semantics`
- `no_matching_bounded_scope`
- `rejected_invalid_scope`
- `operator_confirmation_required`

The TAIFEX derivatives currentness status set is:

- `current_official_derivatives_eod`
- `matches_expected_latest_trade_date_after_emergency_closure`
- `delayed_one_trading_day`
- `stale_official_derivatives_eod`
- `unresolved_date_mismatch`
- `session_semantics_unresolved`

Generic equity currentness names such as `current_official_eod` and `stale_official_eod` are upstream resolver inputs only and must not be emitted by TAIFEX observations.
