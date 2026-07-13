# M8C TAIFEX MIS identity and symbol resolution contract

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

## Required identity fields

requested_product_id, mis_cid, runtime_symbol_id, market_type, session, contract_month_or_week, strike_price, option_type, source_contract_name, identity_resolution_method, identity_resolution_status. The identity key is `(runtime_symbol_id, session, market_type)`, so regular and after-hours observations cannot overwrite each other. Product IDs, MIS CIDs, and runtime SymbolIDs are distinct.

## Weekly options

Weekly option SymbolID must be resolved from official MIS bootstrap rows. Unsupported or ambiguous weekly contracts return `unsupported_weekly_symbol_identity`, `ambiguous_option_identity`, `multiple_symbol_matches`, or `no_symbol_match`; no formula-based prefix synthesis is allowed.

## Session suffix preflight contract

Candidate suffixes are regular futures `-F`, after-hours futures `-M`, regular options `-O`, and after-hours options `-N`. These suffixes are part of the runtime identity and must be revalidated in M8C-01 for the requested product/month before use.


## Scoped option-chain identity rule

Observed option-chain rows may omit `CID` and `ExpireMonth`. The resolver must therefore accept explicit validated request-scope provenance (`CID`, `ExpireMonth`, `MarketType`, `SymbolType`) and match exact row identity only on `SymbolID`, Decimal-normalized `StrikePrice`, normalized `CP`/`CallPut`, and the expected session suffix. Missing or inconsistent scope provenance fails closed; row fields must not be silently filled from target values.
