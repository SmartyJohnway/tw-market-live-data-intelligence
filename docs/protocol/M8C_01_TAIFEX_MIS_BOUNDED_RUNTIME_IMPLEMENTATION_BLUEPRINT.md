# M8C-01 TAIFEX MIS bounded runtime implementation blueprint

Status: `m8c_00_taifex_mis_preflight_pass_with_caveats`

This M8C-00 artifact is a protocol/preflight contract only. It does not implement a production TAIFEX MIS runtime, scheduler, daemon, public API, frontend panel, MCP tool, database write, persistent cache, AI/model call, recommendation, or trading signal. Raw full quote payloads, cookies, session identifiers, and full option-chain payloads are not retained.

## Evidence posture

Operator-provided observations were treated as hypotheses. The repository baseline is `93ac89aa3548fb1cfa0b13048487bed54c3414bf` (PR #130 merge commit present in the local repository snapshot). Remote `origin` was unavailable in this environment, so `git fetch origin` could not be completed; local HEAD was exactly the expected baseline before branching.

## Compatibility matrix

| Existing M8/M8B field or policy | Reusable for M8C | Must be extended | Must not be reused | Reason |
|---|---:|---:|---:|---|
| source_id / authority_level / timing_class | yes | yes | no | TAIFEX_MIS is official-undocumented browser transport, not documented TAIFEX OpenAPI. |
| raw payload prohibited | yes | no | no | Same no-raw-payload AI governance applies. |
| M8 generic retrieved_at intraday freshness | no | yes | yes | Recent retrieval must not upgrade an old closed TAIFEX MIS CDate/CTime quote. |
| M8B TAIFEX_OPENAPI EOD semantics | partial | yes | yes | M8B is official EOD/statistical; M8C is live-ish browser snapshot. |
| bounded retained scope | yes | yes | no | Option discovery can be whole requested month-chain network scope but retained exact strike/type only. |

## Core decisions

- Preferred M8C-01 transport: bounded SockJS XHR polling after same-origin REST bootstrap.
- WebSocket may be server-advertised but is not required for M8C-01 unless directly reproduced later.
- Snapshot runtime readiness: `go_with_caveats` when REST, XHR polling, exact subscription, futures initial state, options initial state, hard limits, identity support, and currentness contracts are reproduced.
- Delta runtime readiness: `conditional_no_go` until active follow-up quote mode and merge semantics are directly verified.
- Unknown weekly option identities fail closed and must be resolved from official MIS bootstrap rows, not guessed.

## M8C-01 recommended flow

operator confirmation -> validate bounded selectors -> create one ephemeral HTTP session -> REST product/month/exact identity resolution -> for options, one bounded whole-requested-month-chain discovery when needed with exact retained strike/type only -> get exact quote detail -> SockJS info/open/send exact subscribe/receive initial quote/stop polling/close -> discard cookies and session IDs -> normalize compact observations -> TAIFEX-MIS currentness.

Recommended public function: `execute_taifex_mis_snapshot(..., transport_preference="xhr_polling", max_reconnect_attempts=0, max_wire_bytes=2000000, max_retained_observations=100)`.

## Executable limits and scoped request contracts

M8C-01 must use the same bounded reader semantics as the preflight tools: reject oversized `Content-Length`, stream with a byte cap before JSON materialization, enforce a monotonic total deadline, row caps, symbol/product/month/strike caps, SockJS frame and decoded-message caps, per-poll timeout, and reconnect cap. REST bootstrap request bodies are JSON objects using `MarketType`, `SymbolType`, `KindID`, `CID`, and `ExpireMonth` for futures/options list endpoints; exact detail uses `{"SymbolID": ["..."]}`. Options discovery is whole requested month/week-chain network scope and exact retained identity scope.

## ProbeBudget requirement

M8C-01 must carry one shared `ProbeBudget` through REST bootstrap, `/rt/info`, XHR open, `xhr_send`, and XHR polling. The budget owns the absolute monotonic deadline, total accounted payload-byte cap (response bodies plus SockJS send payload bytes; HTTP headers excluded), REST row cap, frame cap, decoded-message cap, selector caps, symbol cap, and reconnect cap. Request timeout is `min(single_request_timeout, remaining_total_deadline)`, and every increment is checked immediately after it is added.


## Scoped option identity resolution

Because observed `getQuoteListOption` rows do not carry `CID` or `ExpireMonth`, M8C-01 must keep validated request-scope provenance (`CID`, `ExpireMonth`, `MarketType`, `SymbolType`) separate from exact row identity (`SymbolID`, `StrikePrice`, `CP`, session suffix). Option identity resolution must fail closed when scope provenance is absent or inconsistent; it must not substitute target scope values into rows as if those fields were observed.
