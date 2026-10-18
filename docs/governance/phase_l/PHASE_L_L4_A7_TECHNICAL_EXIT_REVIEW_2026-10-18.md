# Phase L4-A7 ? Security & Resource Boundaries Technical Exit Review

**Date:** 2026-10-18
**Authority:** `USER_CHAT_2026-10-18_L4_A7_TECHNICAL_EXIT_REVIEW_AUTHORIZATION`
**Review base:** `origin/main@1884f9e9be2430d8d18cfaa13641c67a8ab9e6ae`
**Review tree:** `1df1b86a748ae30487781aca36bad7a90d64bc3e`
**Branch:** `phase-l/l4-a7-technical-exit-review`
**Technical disposition:** `PHASE_L_L4_EXIT_REVIEW_PASS`
**L4 status:** `TECHNICAL EXIT PASS / NOT YET OWNER-CLOSED`
**Owner final closure:** `PENDING`
**L5-L7:** `NOT AUTHORIZED`

## 1. Purpose and authority

This is the formal technical exit review for Phase L4 ? Security & Resource Boundaries. It is governance-only and offline. It does not add runtime behavior, change the six-tool MCP surface, authorize provider acquisition, mutate production user state, repair historical Mode C replay debt, normalize immutable evidence bytes, start L5, or make the Owner final-closure decision.

Authority order:

1. frozen L0 production boundary and architecture contract;
2. Owner-accepted L4-A0 security/resource inventory;
3. Owner-accepted and merged A1-A6 tranche authorities;
4. current `PROJECT.md`, `HANDOFF.md`, `ROADMAP.md`, and recovery index;
5. exact merged-main implementation reality at the review base.

The frozen L4 obligation is localhost exposure, path containment, bounded input/output/artifacts, prompt/tool-injection and authorization boundaries, dependency/supply-chain hardening, timeouts, memory/disk bounds, and realistic bounded Watchlist/disclosure/concurrent-Agent cases.

## 2. Accepted and merged L4 chain

| Tranche | Technical scope | Merge reality |
|---|---|---|
| A0 | Security & Resource Boundary Inventory | PR #369 / `6c0759b384516d0a933a341cb8de4b9ef6c2cc2b` |
| A1 | Localhost / Network Exposure | PR #370 / `2ef46379d6ca81ecff134192116cedfb5215dc8f` |
| A2 | Filesystem / Path Containment | PR #371 / `6f896c124918c9b340358f7010f4c3403e862335` |
| A3 | Input / Output / Artifact Bounds | PR #372 / `a23c9aeb48c120f1fd5c1d2fc168f86c5ada59d6` |
| A4 | Injection / Authorization / Secret Boundary | PR #373 / `a2dfd7ff7c062257a7c7c8f193fced4f9c707a29` |
| A5 | Dependency / Supply Chain | PR #374 / `c8c23e2c1c47d7695ee63c3c527b8461a9cf16b2` |
| A6 | Resource / Load / Concurrency Acceptance | PR #375 / `9a3a274df1f2602dced30633ea5fa119bc39d0e6` |
| A6 post-merge sync | canonical merged-state sync | PR #376 / `f845a2c3f1247a5fccebd60c3f379766c8b89e46` |
| A6 final sync R1 | final canonical front-door repair | PR #377 / `1884f9e9be2430d8d18cfaa13641c67a8ab9e6ae` |

All listed merge commits independently verify as ancestors of this A7 review base. No A7 conclusion relies on unmerged A1-A6 implementation work.

## 3. A0 inventory closure

A0 inventoried 33 security/resource boundary items: 7 `COVERED`, 19 `PARTIAL`, 3 `GAP`, 2 `DEFERRED_VALUE`, and 2 `NOT_APPLICABLE`. Its gap register contained 22 PARTIAL/GAP items, each assigned to exactly one later tranche; `RES-002` and `LOAD-004` were the two deferred-value items assigned to A6.

A7 reconciles all 33 items against accepted A1-A6 authority. Final exit counts are:

- `COVERED`: **31**
- `NOT_APPLICABLE`: **2**
- unresolved L4 blockers: **0**

The exact per-item mapping is recorded in `acceptance_runs/l4-a7-20261018T063000Z/obligation_reconciliation.json`.

## 4. Network and path boundaries

A1 closes NET-002 for application-visible socket-origin exposure while retaining the explicit limitation that local relays can present loopback origin. A4 subsequently freezes caller authority as same-user local-process trust rather than inventing individual authentication.

A2 closes PATH-001, PATH-003, and PATH-005 with lexical containment, reparse/symlink checks, root/leaf identity checks, and publication/path tests. The exit review does not claim immunity to a hostile same-user process changing filesystem state after a check.

## 5. Input, output, artifact, and load bounds

A3 closes the assigned ingress, MCP frame, target/catalog/schema, public projection, handoff, and serialized artifact dimensions. The accepted bounds include the 1 MiB request envelope, 8 MiB public response/projection envelope, existing target/operation/Watchlist limits, and bounded producer projections.

A3 deliberately deferred cumulative-history, peak-memory, disk-pressure, and long-handoff resource behavior to A6 rather than inventing arbitrary ceilings. A6 closes those residuals through dynamic fail-closed write admission, resource-intensive concurrency ceiling 1 per app process, finite external/network action execution envelopes, and long-horizon representative memory acceptance. Therefore the A3 resource residual reconciliation is `RESOLVED`.

## 6. Injection, authorization, and secrets

A4 closes INJ-001, AUTH-001, AUTH-002, and SEC-002. Source, agent, evidence, and artifact content remain data rather than control-plane authority; identified legacy network execution routes are disabled; server-owned authorization remains authoritative; active inventoried output surfaces pass deterministic secret-canary coverage.

The accepted contract does not claim control over downstream model cognition, individual-user authentication, or future uninspected output surfaces.

## 7. Dependency and supply-chain boundary

A5 closes DEP-001 and DEP-002 for repository-controlled install authority, exact dependency locking, restricted dependency forms/index behavior, and the active executable-selection surface. The exit review preserves A5 limitations: it does not claim cryptographic provenance for OS/Python/Git binaries and does not perform an online vulnerability-freshness check.

## 8. Resource, timeout, disk, memory, and concurrency boundary

A6's final accepted findings are `RES-001/002/003 = COVERED` and `LOAD-001/004 = COVERED`, with A3 resource residuals resolved. The frozen resource policy is:

- resource-intensive concurrency ceiling: **1 per app process**, fail-fast, no queue;
- whole-server global hard deadline: **`NOT_USED_BY_DESIGN`**;
- memory hard runtime kill threshold: **`NOT_USED`**;
- persistent write disk admission: **`DYNAMIC_FAIL_CLOSED`**;
- automatic governed revision truncation: **`NO`**.

`NOT_USED_BY_DESIGN` and `NOT_USED` are explicit accepted policy choices, not missing values. Active network/action paths have finite execution envelopes; local bounded deterministic work relies on structural bounds rather than an unsafe generic cancellation wrapper. No mathematical machine-independent maximum RSS is claimed.

## 9. Integrated A7 deterministic gate

Run: `l4-a7-20261018T063000Z`.

The bounded merged-main gate completed:

- **308 passed**
- **1 skipped**
- **2 governed deselected**
- **0 failed**
- external socket attempts: **0**
- provider requests: **0**
- live market acquisition: **0**
- production user-state mutations: **0**

The two deselected nodes are the already-governed TG4 Mode C historical V1 replay gaps. They remain `KNOWN_HISTORICAL_REPLAY_GAP_NOT_CURRENT_PROTECTION`, are not repaired, and are not represented as passing. The one skip is the existing Git-ignored local-candidate integration fixture skip.

## 10. Validators and public compatibility

All A7 exit validators pass on the review base:

- dependency supply-chain verification;
- environment verification;
- `pip check`;
- source registry validation;
- Portable Catalog synchronization;
- runtime/Skill exact-six validation;
- V1 public exact-six validation;
- Unified market-evidence contracts;
- Phase H V3 contracts;
- `compileall`.

The runtime/Skill validator reports exactly six tools: `market_describe_capabilities`, `market_validate_request`, `market_preview_request`, `market_read_result`, `market_export_ai_handoff`, and `market_fetch_evidence`. A7 adds no tool, capability, provider route, trading/order surface, scheduler, polling loop, startup acquisition, or parallel identity authority.

## 11. Evidence integrity

A1, A2, A3, A4, A5, A6, R3, R3-R1, and R3-R2 listed manifest artifacts verify by bytes and SHA-256 under their respective path conventions.

A0's manifest correctly binds its technical-candidate governance document at commit `83f47b4b12874b3ce31cbfc38085ee27b9056c4b`; the manifest hash `7c311d3b...` matches that ancestor exactly. Owner-acceptance commit `047f90cf917c8b1f27711320c75dc833fdf03bd7` later appended governance text to the same document, producing the current different hash. The other seven A0 manifest artifacts remain byte/hash valid. This is expected governance supersession, not evidence tamper.

Seven A6 historical memory-evidence JSON files retain one hash-bound EOF `CRCRLF` each. They remain the accepted immutable-evidence format exception; normalization would break the historical hash chain. No generic whitespace waiver exists.

## 12. Retained non-blocking limitations

A7 retains, rather than hides, the following limitations:

1. same-user local-process trust is the caller boundary; no individual caller authentication is claimed;
2. no hostile same-user post-check filesystem-race immunity is claimed;
3. downstream model cognition is outside the TW-Market control-plane guarantee;
4. OS/Python/Git binary authenticity and online vulnerability freshness are outside A5's repository supply-chain guarantee;
5. no hard RSS kill threshold or machine-independent RSS ceiling is claimed;
6. no generic whole-server ASGI deadline is used; finite action/network execution envelopes are enforced at the executable/transport seams;
7. concurrency ceiling 1 is per app process; no multi-process coordinator is claimed;
8. governed Watchlist/evidence history is not automatically truncated; new writes require dynamic disk admission;
9. two historical Mode C replay nodes remain governed debt and are not passing;
10. seven immutable historical evidence EOF-format exceptions remain preserved.

None contradicts a frozen L4 exit obligation or leaves an A0 blocker unresolved.

## 13. Exit decision

`PHASE_L_L4_EXIT_REVIEW_PASS`

No unresolved blocker remains against the frozen L4 Security & Resource Boundaries contract. All 22 A0 PARTIAL/GAP findings and both deferred-value resource decisions have accepted closure authority; the seven originally-covered findings remain covered and the two not-applicable findings remain not applicable. The merged-main deterministic gate and validators pass without external network activity.

This technical pass does **not** constitute Owner-final closure of L4.

## 14. Next boundary

L4 is `TECHNICAL EXIT PASS / NOT YET OWNER-CLOSED`. Owner final closure is `PENDING`.

L5-L7 remain `NOT AUTHORIZED`. This A7 authorization does not start Extension Architecture, Packaging/Portability, or Release Governance work.


## Owner Final Closure

Disposition: `PHASE_L_L4_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`.

Owner authority: `USER_CHAT_2026-10-18_PHASE_L_L4_OWNER_FINAL_CLOSURE_AND_A7_MERGE_AUTHORIZATION`.

The Owner accepts `PHASE_L_L4_EXIT_REVIEW_PASS`, authorizes the A7 technical-exit-review candidate for merge, and accepts final closure of L4 once that merge is verified on canonical `origin/main`. All 33 A0 inventory rows retain the A7 reconciliation of 31 `COVERED` plus 2 `NOT_APPLICABLE`, with zero unresolved blocker. The two TG4 historical Mode C replay nodes remain governed debt and are not represented as passing. The seven immutable evidence EOF format exceptions remain byte-preserved and do not establish a generic whitespace waiver.

This Owner closure does not authorize L5, L6, or L7 work. Until the A7 merge is verified, canonical state is `OWNER FINAL CLOSURE ACCEPTED FOR MERGE`; after verified merge, L4 may be recorded as `CLOSED` under `PHASE_L_L4_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`.
