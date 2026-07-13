# M8C TAIFEX MIS failure and bounded transport contract

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

## Failure/status vocabulary

operator_confirmation_required, rejected_invalid_scope, frontend_contract_drift, rest_bootstrap_failure, rest_schema_drift, bootstrap_byte_limit_reached, bootstrap_row_limit_reached, option_identity_discovery_network_limit_reached, option_identity_not_found, ambiguous_option_identity, unsupported_weekly_symbol_identity, sockjs_info_contract_drift, sockjs_open_frame_missing, sockjs_session_affinity_failure, sockjs_send_failure, sockjs_frame_decode_failure, sockjs_close_frame_received, sockjs_transport_failure, subscription_rejected, unexpected_quote_mode, active_session_delta_not_observed, change_date_semantics_unresolved, change_source_semantics_unresolved, wire_byte_limit_reached, frame_limit_reached, decoded_message_limit_reached, bounded_time_limit_reached, reconnect_limit_reached, source_timestamp_missing, source_timestamp_unresolved, session_semantics_unresolved, market_phase_unresolved, snapshot_incomplete, successful_initial_state_probe, partial_probe_success.
