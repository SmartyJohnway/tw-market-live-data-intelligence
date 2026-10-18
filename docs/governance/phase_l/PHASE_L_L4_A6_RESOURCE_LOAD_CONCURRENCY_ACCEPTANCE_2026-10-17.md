# Phase L4-A6 — Resource / Load / Concurrency Acceptance

## Authority and base

This bounded, offline-only technical candidate was prepared on branch
`phase-l/l4-a6-resource-load-concurrency-numeric-ceiling-freeze` from the
merged L4-A5 main commit `c8c23e2c1c47d7695ee63c3c527b8461a9cf16b2`, tree
`536190b51d1374763ed4eaf70d6b670626fb2d50`. The authorized scope is L4-A6:
resource/load/concurrency acceptance and numeric ceiling reconciliation. No
provider acquisition, external socket attempt, destructive disk fill, OOM test,
real-user Watchlist mutation, or A7 work was performed.

## Frozen inputs and findings

L4-A0 assigned `RES-001`, `RES-002`, `RES-003`, `LOAD-001`, and `LOAD-004` to
this tranche. L4-A3 separately left cumulative SQLite/revision growth, peak
serialization memory, aggregate evidence, and long-handoff performance as
resource residuals. A3's serialized contracts remain unchanged.

The numeric ledger retains existing product limits: 1 MiB Unified request,
8 MiB bounded response, 50 targets, 100 operations, 500 records, a 20-day
recent-performance window, 32 Watchlists with 500 entries per list, 1 MiB
Watchlist import, 50 material-disclosure items, source-specific finite
transport timeouts, a 130-second Mode B2 child timeout, and a 145-second
Local Service client action timeout. No new target, response, or revision
truncation behavior was introduced.

## Implemented controls

`server/resource_boundaries.py` adds a process-local, fail-fast resource
admission ceiling of one in-flight resource-intensive request. It does not
queue work. Concurrent resource actions, projections, persistent mutations,
offline planning, and unknown write routes receive HTTP 503 with the stable
reason `resource_concurrency_limit`; light reads and health remain available.
The limit is process-local. The normal launcher uses one Uvicorn worker; custom
multi-process hosting is not covered by a shared cross-process coordinator.

Dynamic disk admission now precedes Watchlist SQLite schema initialization,
preview insertion, and commit writes; Mode B2 control-package publication; and
Mode C's three-file Result/Audit/Markdown publication. SQLite estimates use
measured current database size and exact serialized entry/revision payloads,
with a rollback/growth envelope. Mode B2 and Mode C use the UTF-8 byte sum of
the materialized members. Unobservable or insufficient free space fails closed
with stable reason codes. This is per-write admission, not a quota or a
reservation against other processes.

Persistent Watchlist revision history remains append-only. No automatic
revision truncation, cleanup, database migration, or user-state mutation was
added.

## Timeout and memory boundaries

Current finite source transport boundaries and the 130-second child / 145-second
client action limits are recorded without changing their values. A single
server-wide deadline covering all synchronous work and filesystem publication
is not present. An ASGI cancellation wrapper cannot safely terminate the
synchronous source/serialization work in its thread, so this tranche does not
claim a global request deadline.

No process RSS ceiling is frozen. Existing request/response, target, operation,
source-response, and concurrency bounds reduce load, but they do not establish
a machine-independent process memory maximum. No OOM or pressure test was run.
Selecting an RSS number without a supported host-memory floor or representative
calibration would invent an operational constant. This remains an explicit
deferred value.

## Acceptance evidence

Run `l4-a6-20261017T134505Z` contains the numeric ledger, resource and A3
reconciliations, timeout/concurrency/disk/memory/load matrices, retention rule,
offline review, preflight result, and a canonical SHA-256 manifest. The scoped
offline gate completed with 348 passed, 4 platform-specific skips, 2 previously
known A0/A2 Mode C historical tamper-helper tests deselected, and 0 failures.
Those two tests are not represented as passing. The external socket sentinel
recorded 0 attempts. Validators, compileall, py_compile, and `git diff --check`
passed.

No validator changed the six-tool MCP surface, Unified public schemas, Catalog,
Route, capabilities, provider routes, Security Master authority, or trading
boundary. No production Result/Audit or real Watchlist state was mutated.

## Finding reconciliation

| Finding | A6 result | Rationale |
|---|---|---|
| RES-001 | PARTIAL | Individual transports and child/client boundaries are finite; no enforceable whole-server deadline covers all synchronous and filesystem work. |
| RES-002 | PARTIAL | Disk admission is enforced at identified writers; process RSS ceiling and fixed cumulative storage policy remain deferred. |
| RES-003 | COVERED | One in-flight resource request per app process; fail-fast, no queue. |
| LOAD-001 | COVERED | Existing hard limits retained and maximum synthetic target/Watchlist fixtures accepted at limit and rejected above it. |
| LOAD-004 | PARTIAL | Concurrency and disk admission are enforced; no RSS cap or destructive pressure test. |

The A3 residual reconciliation keeps `IN-003`, `OUT-002`, `OUT-003`,
`LOAD-002`, and `LOAD-003` PARTIAL for cumulative history or peak-memory/
whole-route resource behavior. A3's serialized bounds remain covered.

## Disposition and stop boundary

Technical disposition: `L4_A6_RESOURCE_LOAD_CONCURRENCY_ACCEPTANCE_HOLD`.
The bounded controls and evidence pass, but the frozen A0 scope still has the
unresolved whole-request deadline and machine-independent process-memory
ceiling questions above, and cumulative Watchlist history remains uncapped.
This record does not claim the full A6 numeric ceiling freeze is complete.

L4-A7 remains unauthorized. No A7 technical exit review was started. L5-L7
remain unauthorized.


## R3 continuation reference

The initial candidate disposition above remains historical and unchanged. R1 and R2 memory observations also remain immutable HOLD evidence. R3 recorded long-horizon memory stabilization and a complete timeout matrix, but the integrated bounded regression gate reproduced two historical Mode C tamper-helper failures; therefore the A6 technical disposition remains HOLD. See `PHASE_L_L4_A6_R3_MEMORY_STABILIZATION_ACCEPTANCE_2026-10-17.md` and the hash-bound R3 run `l4-a6-r3-20261017T150419Z`. No A7 work was started.


## R3-R1 acceptance-gate correction (2026-10-18)

The initial A6 candidate, R1, R2, and R3 HOLD outcomes remain historical and
unchanged. R3 correctly stopped for the exact test invocation it ran: 308 passed,
2 failed, 1 skipped, and 0 deselected. Subsequent authority reconciliation found
that invocation omitted the two already-governed TG4 historical Mode C replay
deselections. R3-R1 reran the same bounded scope with exactly those two nodes
deselected and no other selection change: 308 passed, 1 skipped, 2 governed
deselected, 0 failed. The nodes remain failing historical debt, are not repaired,
and are not represented as passing. The corrected gate, unchanged R3 resource
findings, and final technical disposition are bound by
`l4-a6-r3-r1-20261018T004303Z`.

Final technical disposition: `L4_A6_RESOURCE_LOAD_CONCURRENCY_ACCEPTANCE_PASS`.
L4-A6 remains pending Owner acceptance. L4-A7 remains unauthorized.


## Owner acceptance for merge (2026-10-18)

Owner authority: `USER_CHAT_2026-10-18_PHASE_L_L4_A6_OWNER_ACCEPTANCE_AND_MERGE_AUTHORIZATION`.

Owner acceptance token: `L4_A6_RESOURCE_LOAD_CONCURRENCY_ACCEPTANCE_OWNER_ACCEPTED_FOR_MERGE`. The Owner accepts the completed A6 tranche for merge with final technical disposition `L4_A6_RESOURCE_LOAD_CONCURRENCY_ACCEPTANCE_PASS`.

The complete history remains intact: initial A6 HOLD; R1 memory HOLD; R2 sampler repair PASS and memory HOLD; R3 memory stabilization PASS and original integrated invocation HOLD; R3-R1 governed historical gate correction PASS; and R3-R2 immutable-evidence reconciliation PASS. None of the historical HOLD outcomes is erased or rewritten.

Accepted findings: RES-001/002/003 and LOAD-001/004 are COVERED; A3 resource residuals are RESOLVED. Frozen policy remains resource-intensive concurrency ceiling 1, whole-server global hard deadline NOT_USED_BY_DESIGN, memory hard runtime kill threshold NOT_USED, persistent write disk admission DYNAMIC_FAIL_CLOSED, and automatic governed revision truncation NO.

Limitations remain explicit: Mode C historical debt is unresolved; the two TG4 nodes remain `KNOWN_HISTORICAL_REPLAY_GAP_NOT_CURRENT_PROTECTION`, governed-deselected rather than passed, with zero new deselections. The full candidate-range diff-check retains exactly seven byte-preserved immutable evidence EOF formatting exceptions; no general whitespace waiver is created.

At this pre-merge closure point, L4-A6 is Owner-accepted for merge but is not yet described as merged. L4-A7 and L5-L7 remain NOT AUTHORIZED.


## Post-merge governance verification (2026-10-18)

Owner acceptance: `L4_A6_RESOURCE_LOAD_CONCURRENCY_ACCEPTANCE_OWNER_ACCEPTED_FOR_MERGE`. PR #375 is MERGED. Merge commit: `9a3a274df1f2602dced30633ea5fa119bc39d0e6`. Post-merge `origin/main`: `9a3a274df1f2602dced30633ea5fa119bc39d0e6`.

Ancestry verification: A6 candidate `e5bb67862fe4309d7f83f73a374aa0f1756987d9`, R3-R2 reconciliation commit `e5bb67862fe4309d7f83f73a374aa0f1756987d9`, and Owner closure commit `f95469e475ba629248ae8ef6a103295a692143bc` are ancestors of post-merge `origin/main` (PASS). L4-A6 final tranche state is `OWNER-ACCEPTED AND MERGED`. L4-A7 and L5-L7 remain NOT AUTHORIZED.
