# M8C TAIFEX MIS runtime selector and execution-result contract

M8C-01 accepts only regular-session selectors. Futures require `instrument_type=future`, `requested_product_id`, `contract_month_or_week`, and `session=regular`. Options additionally require Decimal-normalized `strike_price` and `option_type` normalized from C/Call or P/Put.

All selectors and caller limits are validated before network. Mixed sessions, after-hours, duplicates, invalid scope, and caller limits above hard maxima are rejected with no network request.

Execution uses one ephemeral HTTP session: REST product/month/CID validation, exact identity resolution, exact quote detail bootstrap, SockJS `/futures/rt/info`, XHR open requiring `o`, exact-symbol subscribe, bounded polling, accept first valid `mode=1` quote per symbol, stop polling, and close the session in `finally`. There is no reconnect, no silent REST retry, and no unsubscribe invention.

Options use whole requested contract-month chain as network scope and exact strike/type as retained scope. Weekly SymbolIDs are never synthesized.

Result statuses are `operator_confirmation_required`, `rejected_invalid_scope`, `successful_liveish_snapshot`, `partial_source_success`, `snapshot_incomplete`, `transport_bootstrap_failure`, `transport_connection_failure`, or `source_error`. Results include compact timing, accounting, transport summary, selector results, observations, and caveats; they never include raw REST payloads, raw SockJS frames, full option chains, cookies, SockJS session IDs, `trueValues`, or complete QID maps.


## Monthly-only scope

M8C-01 runtime selectors are narrowed to monthly `YYYYMM` contracts only. Weekly option selector formats such as `YYYYMMF1-F5` and `YYYYMMW1-W5` remain deferred until exact DDL validation and row-based SymbolID resolution are separately accepted; weekly SymbolIDs are never synthesized.
