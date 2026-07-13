# M8C TAIFEX MIS session timestamp and currentness preflight

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

## TAIFEX-MIS-specific currentness axes

transport_state, session_alignment, market_phase, source_timestamp_state, quote_age_state, calendar_evidence, and overall_ai_currentness. `closed_session_latest_completed` must never be upgraded by the generic M8 evaluator to `fresh_intraday_snapshot`. After-hours CDate is not simple calendar subtraction; a verified trading calendar is required to resolve business dates around weekends, holidays, special closures, and typhoon closures.

## Currentness precedence for M8C-02

Future builder integration must apply this precedence: (1) TAIFEX-MIS-specific `overall_ai_currentness`, (2) source-specific market phase and session alignment, (3) source timestamp age, and (4) retrieved-at fallback only when source-specific evidence is absent. Generic fallback must fail closed and must not upgrade unresolved or closed data to fresh.
