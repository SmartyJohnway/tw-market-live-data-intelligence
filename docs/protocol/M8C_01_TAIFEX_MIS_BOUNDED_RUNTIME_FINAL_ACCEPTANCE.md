# M8C-01 TAIFEX MIS bounded runtime final acceptance

Final status: `m8c_01_taifex_mis_bounded_snapshot_runtime_pass_with_caveats`.

M8C-01 implements the accepted M8C-00 architecture: same-origin REST bootstrap, ephemeral SockJS XHR polling, exact runtime-symbol subscription, `mode=1` initial quote-state collection, bounded termination, and compact normalized observations. Regular session is the only supported runtime session in this PR.

## Corrected runtime safeguards

- SockJS numeric QIDs and REST named fields are normalized through one canonical extraction path. Required QIDs include `125=CLastPrice`, `129=CRefPrice`, `143=CTime`, `144=CDate`, `145=Status`, `404=CTotalVolume`, and the competing top-of-book families `101/102/113/114` and `743/744/745/746`. QID `101` is never interpreted as last price.
- REST, `/rt/info`, XHR open, `xhr_send`, and XHR poll responses use shared streaming bounded reads with `Content-Length` precheck, remaining total payload limit, chunk accounting, monotonic deadline checks, per-request timeout clamped to remaining deadline, and HTTP status validation before response materialization.
- Identity resolution is per selector. Failed selectors produce failed selector results; successful symbols are still subscribed and retained. Mixed outcomes return `partial_source_success`.
- Currentness is fail-closed. Raw TAIFEX `Status` values are mapped only through directly allowed status codes; unknown statuses become `market_phase_unresolved`. Fresh promotion also requires accepted `mode=1`, non-future source timestamp, regular-session suffix/session alignment, evaluation time inside the validated regular window, and verified active phase.
- Selector validation rejects invalid `YYYYMM`, unsupported weekly strings, and zero/negative/non-finite strikes before any network request.

## Caveats and boundaries

After-hours remains disabled unless separately live-validated; cross-midnight semantics remain unresolved; deltas are disabled and unsupported quote modes are counted but ignored; reconnect is disabled (`MAX_RECONNECT_ATTEMPTS=0`); no unsubscribe message is invented; raw payloads, cookies, SockJS session IDs, full option chains, raw QID maps, and `trueValues` are not retained or exposed; AI context, conversation projection, public API, MCP, frontend, scheduler, daemon, DB writes, and trading/recommendation behavior remain disabled until a later task.

Canonical next task: `M8C-02-TAIFEX-MIS-M8-CURRENTNESS-CONTEXT-INTEGRATION-AND-FINAL-ACCEPTANCE`.
