# M8C-00 TAIFEX MIS preflight final acceptance

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

## Final result

`m8c_00_taifex_mis_preflight_pass_with_caveats`

Readiness fields: transport_reproduced = evidence-captured in compact probe summaries; rest_bootstrap_reproduced = true with caveats when endpoint summaries are current; sockjs_xhr_polling_reproduced = true with caveats when initial state probe summary is current; futures_initial_state_reproduced = true with caveats; options_initial_state_reproduced = true with caveats; regular_active_session_observed = false in this execution window; after_hours_active_session_observed = false in this execution window; cross_midnight_observed = not_observed_due_execution_window; delta_semantics_verified = false; changeDate_semantics_verified = false; changeSource_semantics_verified = false; snapshot_runtime_readiness = go_with_caveats; delta_runtime_readiness = conditional_no_go; personal_use_access_disposition = operator_accepted_personal_local_research_only; next task = M8C-01-TAIFEX-MIS-BOUNDED-REST-SOCKJS-SNAPSHOT-RUNTIME.

## Validation evidence

Focused M8C tests passed in this branch. All M8-family unit tests passed. Default CI passed. Full non-network retained the accepted M5D/M5E frontend publication baseline drift caveat and is not caused by M8C changes. No M8C probe performs network without `--confirm-live-probe`.

## Review-blocker follow-up evidence

The bounded SockJS sequence was reproduced end-to-end: `/info`, XHR open `o`, `xhr_send` subscription with dynamically resolved `TXFG6-F`, `MXFG6-F`, and `TXV40100G6-O`, and array quote frames for all three symbols. Only compact counts and presence flags were retained: mode `1`, 62/62 values/trueValues for TX and MTX, 43/43 for TXO, CDate/CTime/Status present, 6,472 wire bytes, 85 frames, 87 decoded messages, and 3.104 seconds. REST was re-probed with scoped bodies, including product/month DDL, narrowed futures quote lists, a whole requested TXO week/month chain, ineffective RowSize/PageNo/StrikePrice/CP network narrowing, and exact quote detail for futures/options/multiple symbols.

## Commit 3 review-blocker corrections

Corrected counter semantics: `wire_bytes` is the shared total budget across REST and SockJS request/response bodies, `frame_count` starts with the SockJS open frame and increments once per received SockJS frame, and `decoded_message_count` counts only decoded messages inside SockJS array frames. The corrected live probe observed `frame_count=2` and `decoded_message_count=3` for the initial-state sequence. Candidate field presence is now recorded by QID presence booleans only; field semantics and active delta remain unresolved.
