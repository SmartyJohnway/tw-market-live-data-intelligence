# M8C-01 TAIFEX MIS bounded runtime final acceptance

Final status: `m8c_01_taifex_mis_bounded_snapshot_runtime_pass_with_caveats`.

Tested runtime SHA: `280f9d2b34a14d9b51db2d44cd492c8873e865a0`.
Base SHA: `00760f0a4cb06ac9455d5210da3556863eb691c2`.
Canonical next task: `M8C-02-TAIFEX-MIS-M8-CURRENTNESS-CONTEXT-INTEGRATION-AND-FINAL-ACCEPTANCE`.

M8C-01 implements the accepted M8C-00 architecture: same-origin REST bootstrap, ephemeral SockJS XHR polling, exact runtime-symbol subscription, `mode=1` initial quote-state collection, bounded termination, and compact normalized observations. Regular session is the only supported runtime session in this PR.

## Corrected runtime safeguards

- SockJS numeric QIDs and REST named fields are normalized through one canonical extraction path. Required QIDs include `125=CLastPrice`, `129=CRefPrice`, `143=CTime`, `144=CDate`, `145=Status`, `404=CTotalVolume`, and the competing top-of-book families `101/102/113/114` and `743/744/745/746`. QID `101` is never interpreted as last price.
- REST, `/rt/info`, XHR open, `xhr_send`, and XHR poll responses use shared streaming bounded reads with `Content-Length` precheck, remaining total payload limit, chunk accounting, monotonic deadline checks, per-request timeout clamped to remaining deadline, and HTTP status validation before response materialization.
- Identity resolution is per selector. Failed selectors produce failed selector results; successful symbols are still subscribed and retained. Mixed outcomes return `partial_source_success`.
- Currentness is fail-closed. Raw TAIFEX `Status` values are mapped only through directly allowed status codes; unknown statuses become `market_phase_unresolved`. Fresh promotion also requires accepted `mode=1`, non-future source timestamp, regular-session suffix/session alignment, evaluation time inside the validated regular window, and verified active phase.
- Selector validation rejects invalid `YYYYMM`, unsupported weekly strings, and zero/negative/non-finite strikes before any network request.

## Partial bounded termination

Bounded termination is accepted as a controlled partial result when at least one `mode=1` initial state has already been accepted and polling later reaches a total deadline, decoded-message limit, frame limit, payload limit, or close frame. The runtime preserves accepted observations, returns `partial_source_success`, records `missing_symbols`, records the concrete `termination_reason`, and sets `limit_reached=true` for hard-limit termination. HTTP, protocol, schema, JSON, and source failures remain fail-closed source errors rather than bounded partial success.

## Live validation evidence

The bounded live auto-smoke was run against remote-resolvable runtime SHA `280f9d2b34a14d9b51db2d44cd492c8873e865a0`. The compact artifact records `tested_runtime_sha`, selected TX, MTX, and one bounded TXO monthly selector dynamically, accepted three initial states, retained no raw quote values, retained no cookies, and retained no SockJS session IDs.

Validator accounting is split and bounded:

| Accounting scope | Total accounted payload bytes | REST rows | Frames | Decoded messages | Symbols | Retained observations |
|---|---:|---:|---:|---:|---:|---:|
| Selector discovery | 346609 | 591 | 0 | 0 | 0 | 0 |
| Runtime execution | 418095 | 1357 | 2 | 3 | 3 | 3 |
| Combined validator action | 764704 | 1948 | 2 | 3 | 3 | 3 |

Combined validation remained under the 2,000,000 byte validator hard bound using separate 1,000,000 byte discovery and runtime payload caps.

## Full non-network comparison

`python scripts/run_test_profile.py full-non-network --json` was run for base `00760f0a4cb06ac9455d5210da3556863eb691c2` and tested runtime `280f9d2b34a14d9b51db2d44cd492c8873e865a0`.

| Revision | Collected | Selected | Passed | Skipped | Deselected | Failed |
|---|---:|---:|---:|---:|---:|---:|
| Base | 1270 | 1269 | 1261 | 1 | 1 | 7 |
| Tested runtime | 1281 | 1280 | 1272 | 1 | 1 | 7 |

The seven failures are the unchanged M5D/M5E frontend-publication baseline-drift failures documented in `docs/reviews/M8C_01_FULL_NON_NETWORK_BASE_HEAD_VALIDATION.md`. `failure_set_identical=true`; no new M8/M8C failure was introduced.

## Monthly-only scope

M8C-01 runtime selectors are narrowed to monthly `YYYYMM` contracts only. Weekly option selector formats such as `YYYYMMF1-F5` and `YYYYMMW1-W5` remain deferred until exact DDL validation and row-based SymbolID resolution are separately accepted; weekly SymbolIDs are never synthesized.

## Compact capability/evidence matrix

| Capability | M8C-01 status | Evidence artifact | Caveat |
|---|---|---|---|
| Regular monthly futures | implemented controlled runtime | `research/probe_runs/m8c_01_taifex_mis_runtime/m8c_01_bounded_live_validation_summary.json` | initial-state only |
| Regular monthly options | implemented controlled runtime | `research/probe_runs/m8c_01_taifex_mis_runtime/m8c_01_bounded_live_validation_summary.json` | whole-month network scope, exact strike/type retained |
| Partial bounded termination | implemented controlled runtime | deterministic unit tests | accepted observations retained; missing symbols caveated |
| Weekly options | deferred | selector contract | no synthesized SymbolID |
| After-hours | disabled | selector contract | requires direct validation later |
| Cross-midnight semantics | unresolved | M8C-00 caveat | no date subtraction inference |
| Delta/streaming | disabled | transport contract | unsupported modes counted/ignored |
| Reconnect | disabled | transport contract | `MAX_RECONNECT_ATTEMPTS=0` |
| Unsubscribe | disabled | transport contract | bounded stop/close only |
| Raw payload exposure | disabled | observation schema and artifact | no raw payload, full chain, QID map, cookies, or session IDs retained |
| AI context | disabled | source registry | M8C-02 only |

## Remaining caveats and boundaries

After-hours remains disabled unless separately live-validated; cross-midnight semantics remain unresolved; deltas are disabled and unsupported quote modes are counted but ignored; reconnect is disabled (`MAX_RECONNECT_ATTEMPTS=0`); no unsubscribe message is invented; raw payloads, cookies, SockJS session IDs, full option chains, raw QID maps, and `trueValues` are not retained or exposed; AI context, conversation projection, public API, MCP, frontend, scheduler, daemon, DB writes, and trading/recommendation behavior remain disabled until a later task.
