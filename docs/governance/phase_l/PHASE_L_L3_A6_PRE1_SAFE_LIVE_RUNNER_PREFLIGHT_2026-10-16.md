# Phase L L3-A6-PRE1 — Safe Live Runner Preflight

**Status:** offline implementation candidate; independent review pending
**Entry HEAD:** `d9d8001b66e4c82ff7c8015fa2264c4bc8cf8365`
**Canonical `origin/main`:** `7b3e73b2f3e2c2bec167b6d66f1846846fe4ec4c`
**Branch:** `phase-l/l3-a6-bounded-live-source-drift-recertification`

## Authority and boundary

The original one-shot A6 live authority remains `AUTHORIZED / NOT CONSUMED`.
PRE1 is offline-only. It performed no market/provider acquisition and did not
create a final `authority_reservation.json`. The run includes only a clearly
marked `NOT_RESERVED_PREVIEW_ONLY` template. No P01-P18 or B01-B05 transport
was invoked.

The prior A6 preflight stopped before live because a safe physical dispatch
accounting and one-shot latch had not yet been established. The current A0
inventory remains the authority for exactly 18 Unified contracts (P01-P18) and
five bootstrap members (B01-B05), or 23 logical entries.

## Transport families and controls

The machine-readable plan groups sources into F01-F10 while retaining one
independent logical result per source. `transport_contract_matrix.json` records
the production executor, transport boundary, finite timeout expression,
per-source physical ceiling, redirect behavior, persistence behavior and
instrumentation strategy for every entry.

The A6-only `A6DispatchController` does not perform HTTP. It reserves each
dispatch before the existing transport boundary, validates the frozen source,
hostname, method, route, logical sequence and quota, and enforces the global
ceiling of 27. Baseline is 23; only P04-P07 may each use one existing governed
JSON alternate, for an absolute maximum of 27. HTTP 429 records the raw
Retry-After fact and suppresses only later entries on the same exact hostname.
404 and 410 are observations and do not suppress or mutate source state.

P01 uses the existing M5K observation path with `write_latest=false` and
`allow_individual_fallback=false`; its offline failure witness observed one
physical opener dispatch. P12's witness calls the source-level H3 month fetch
once for 2330 / 2026-10 and does not invoke the multi-month walker. P17 is
already frozen by P0-R5 as TWSE:2330 / 2026-10-15; no resolver or provider date
discovery was performed here.

Bootstrap probes use the existing `probe_sources.probe` seam with timeout 20,
`max_followed_redirects=0`, and `save_raw=None`. The adapter exposes only the
existing dispatch-budget compatibility surface and reserves through the global
A6 controller. An attempted redirect is observed without following it.

The authority latch requires a final reservation bound to exact pre-network
HEAD/tree and the original A6 authority ID. It atomically writes
`authority_consumed.json` before delegating the first transport call; a later
process sees that consumed receipt and refuses reuse. PRE1's live entrypoint
always fails with `A6_LIVE_RESERVATION_NOT_FINALIZED`.

## P0-R5 prerequisite binding

The PRE1 plan binds the retained normalized calendar SHA
`28c07f487c120a26c5b7c4cef1c74542880c85827b91878662dcfc88e2be9ca8`, R4 daily
artifact and response SHA values, R5 manifest and P17-resolution artifact,
`closure_authority_complete=true`, and the frozen P17 date `2026-10-15`.
Calendar, closure, DGPA and NCDR sources were not reacquired.

## Offline verification

The new controller test module passed **31 tests**. The guarded integrated
source regression gate ran **544 tests: 543 passed, 1 failed**. The failing
pre-existing test is
`test_lifecycle_drift_failure_report_preserves_code_without_retry_authority`:
its JSON file selection matches `bootstrap_failure_code` nested inside the
source evidence manifest, then expects that nested value at the top level.
The failure is in the existing test's report selection, not in a PRE1-modified
bootstrap module. It is retained as a failed gate and is not patched here.

The external socket sentinel recorded **0** attempts. The five requested
validators passed: source registry, Portable Catalog sync, runtime/Skill
sync (tool count 6), V1 public contracts (tool count 6), and Phase H V3
contracts. `compileall` and `git diff --check` passed. No production state,
Security Master, Watchlist, Result/Audit, Catalog, Route or activation state
was mutated.

Run evidence is retained in
`acceptance_runs/l3-a6-pre1-20261016T075811Z/`. Since the integrated gate was
not fully green, PRE1 disposition is
`A6_PREFLIGHT_DISPATCH_ACCOUNTING_UNRESOLVED`. This wording records a blocked
acceptance gate; it does not claim that the identified test failure proves a
physical dispatch counter defect.

## Deferred boundary

No final live reservation was created. No source request, retry, sleep,
backoff, scheduler or polling was performed or authorized by this candidate.
The original A6 authority remains unconsumed. A6 live recertification,
independent review and any later live reservation are outside this PRE1
candidate.

## PRE1-R1 amendment — governed test-selection debt normalization

The original PRE1 gate remains immutable at
`acceptance_runs/l3-a6-pre1-20261016T075811Z/` with disposition
`A6_PREFLIGHT_DISPATCH_ACCOUNTING_UNRESOLVED`. It conservatively included the
known bootstrap report-selection test and failed on its traversal-order
selection behavior.

The exact test-selection debt and its accepted exclusion are already recorded
in the A0 source inventory and A5 lifecycle drift contract. PRE1-R1 reused only
that exclusion. It did not edit the test or bootstrap production runtime, and
the excluded test is not represented as passing. Its separate module run
reported **22 passed, 1 deselected**. The normalized integrated gate reported
**543 passed, 1 deselected, 0 failed**; the single deselection is exactly
`test_lifecycle_drift_failure_report_preserves_code_without_retry_authority`.

PRE1-R1 controller tests reported **31 passed**. Source registry, Portable
Catalog sync, runtime/Skill sync (exactly six MCP tools), V1 public contracts
(exactly six tools), Phase H V3 contracts, compileall and `git diff --check`
passed. The network sentinel recorded zero external socket attempts. The new
R1 evidence records the original PRE1 run as failed, binds the exact candidate
file hashes, and retains a preview-only authority state. No final reservation
was created and the one-shot A6 live authority remains unconsumed.

PRE1-R1 disposition: `PASS_READY_FOR_FINAL_LIVE_RESERVATION`. This is a
technical preflight candidate disposition only; independent review remains
pending. It does not authorize live execution or create a live reservation.
