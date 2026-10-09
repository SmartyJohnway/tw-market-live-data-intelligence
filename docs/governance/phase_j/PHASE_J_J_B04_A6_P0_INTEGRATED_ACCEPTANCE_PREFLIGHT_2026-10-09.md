# J-B04-A6-P0 — Integrated Acceptance Preflight

**Disposition:** `J_B04_A6_P0_BLOCKED_SECURITY_MASTER_NOT_INITIALIZED`

The architecture preflight is complete. The Cloud installation has no active
canonical Security Master release, so production identity cannot be verified.
This is the expected fail-closed state for a clean installation. No H3/H2
operation, bootstrap, or market request was attempted.

## Baseline and A5 authority

```text
starting HEAD = 0576c8304764e6b7ba9e90305b34b63c50fd3fc6
starting TREE = b8eafbef94ee1fc688f04fa633721d98b1d6f5d6
main          = 6daf6e2dcc6fd34e00e7e3831c25e98bb4d2399a
A5            = COMPLETE_PASS
```

The A5 closeout is [the authoritative record](PHASE_J_J_B04_A5_FINAL_CLOSEOUT_2026-10-09.md).
Session #1 remains a historical pre-transport hard block. Session #2 remains
independently verified PASS. Neither session directory nor the A5 closeout was
changed for A6-P0.

## Canonical Security Master preflight

The read-only manager status and the production Mode A loader both report
`NOT_INITIALIZED`. The loader selected the canonical installation-local root;
`TW_MARKET_SECURITY_MASTER_ROOT` was not configured. No active selector,
release ID, release state, qualification, manifest hash, or index hash exists.

```text
production identity verified = false
identity result              = not attempted (authority absent)
acceptance-only target       = prohibited for A6
bootstrap                    = not performed
```

A6 requires an ACTIVE, QUALIFIED, hash-verified installation-local release.
After that separate prerequisite exists, a fresh process must use the
production loader and resolve `TWSE:2330` with `market_hint="TWSE"`. The
resolution must be `resolved` for `exact_listing_id`, with exact market/code,
`company_share` / `common_share`, and execution eligibility `allowed`.
Ambiguous, missing, unsupported, fixture, Candidate-B, and company-name
fallback results block before any H3/H2 execution.

## Existing production call graph

| Stage | Existing implementation | Contract and boundary |
|---|---|---|
| Identity | `scripts.m8r_06_01c2_mode_a_security_master_loader.get_production_mode_a_security_master` and `TaiwanMarketIdentityService.resolve` | ACTIVE/QUALIFIED release; exact `TWSE:2330`; no bootstrap or fallback |
| Request, plan, authorization | `server.services.unified_mode_b2.build_local_operator_execution_ticket` | Existing Unified Request → F3 validation → plan → authorization/claim/preflight |
| H3 | `scripts.m8r_06_03_production_adapter._phase_h_h3_twse_recent_performance` | `phase_h_h3_twse_recent_performance_executor`; H3 owns the comparison window; one target, lookback 1–20, at most three unique TWSE `STOCK_DAY` months; partial/source-failed outcomes remain explicit |
| H2 | `server.services.phase_h_h2_twse_exright_executor.execute_h2_twse_exright_pre` | `phase_h_h2_twse_exright_pre_executor`; same-target H3 artifact/window is required; one `TWT48U_ALL` GET; route is currently plan-only and inactive |
| H4 | `derive_h4_for_completed_plan` → frozen `derive_discontinuity_safety` | Deterministic and zero-network; partial corporate-action coverage may correctly remain `coverage_incomplete` with ordinary-return interpretation blocked |
| Result V3 | `scripts.m8r_05c.result_builder.build_result` | Projects canonical identity, H3/H2/H4, citations, lineage, partial/failure status, and guards |
| Audit V3 | `scripts.m8r_05c.audit_package_builder.build_audit_package` | Records Security Master hashes/release when bound, plan/authorization/claim/receipt/bundle, operation lineage, evidence hashes/citations, source coverage/outcomes, and H4 derivation inputs/guard |
| Handoff | `server.services.unified_mode_c.build_mode_c_result_package` / `build_mode_c_ai_handoff` | Verifies and exports Result/Audit and guarded Markdown |
| Service/API/Workbench/MCP | `fetch_market_evidence`, `/api/unified/fetch-evidence`, Workbench router, `server.unified_mcp` | Shared governed Local Service path; the six MCP tools remain unchanged |

The execution order is **identity → H3 → H2 → H4 → Result V3 → Audit V3 →
handoff**. A3 already has a network-free integrated E2E fixture for the
production chain and partial H4 guard. It does not substitute for repeating the
integrated acceptance with a real production identity release.

### Activation boundary

H2 is registered as a candidate, but the canonical capability catalog has
`runtime_executable=false`, `phase_h_activation_state=inactive`, and
`selected_executor_id=null`; the routing matrix says `plan_only`. A6-P0 makes
no activation change. A future activation would require a separately reviewed
canonical catalog/routing selection and the existing governed Phase-H
activation authority; it must not be done as part of this preflight.

### Result and audit contracts

Result V3 already supports the H2, H3, and H4 evidence branches and the partial
state/interpretation guard, source observation dates, currentness, citations,
and lineage. Authorization and bounded operation counts are represented in
the Audit/receipt path rather than the Result evidence projection. No Result schema change is required. Audit V3
preserves target validation and Security Master release/hash identity, request
and authorization, plan and operation lineage, artifacts/citations, and
Phase-H source attempt/coverage/failure and H4 derivation semantics. No Audit
schema change is required for those facts.

One observability gap remains: Audit V3 does not encode actual HTTP dispatch
counts or redirect counts. Its source-attempt record cannot reconstruct them.
The future A6 acceptance must therefore preserve a separate sanitized
session-level transport ledger bound to the receipt and artifact hashes. This
P0 does not alter the frozen Audit schema.

## Handoff coverage at P0

| Layer | P0 status | Evidence / reason |
|---|---|---|
| Contract fixture | `COVERED` | A3 frozen contracts and A5 closeout |
| Deterministic unit | `COVERED` | Existing A3 H2/H3/H4 and Result/Audit regressions; A6 identity-gate tests |
| Integration | `READY_FOR_A6` | A3 fake-source E2E exists; canonical identity must be available for A6 |
| Service API | `READY_FOR_A6` | Existing Local Service fetch and Result/Audit package routes |
| Workbench | `READY_FOR_A6` | Existing Workbench router uses governed Local Service execution |
| MCP | `READY_FOR_A6` | Existing six-tool contract and service client; no seventh tool |
| Fresh install | `BLOCKED_WITH_REASON` | Security Master is `NOT_INITIALIZED`; fail before H3/H2 |
| Real bounded network | `BLOCKED_WITH_REASON` | Identity prerequisite absent and no A6 authorization |
| Real AI / agent | `DEFERRED_TO_LATER_PHASE_J` | Full Phase J scenario matrix is outside this bounded vertical |

The vertical is one TWSE common-share target only. TPEx H3 remains blocked and
is not part of A6. No trading, order routing, broker credentials, position
mutation, recommendation engine, or hidden scheduler is introduced.

## Future bounded-live proposal (designed, not authorized)

| Source | Endpoint | Maximum per integrated attempt | Retry | Redirect |
|---|---|---:|---:|---:|
| H3 `H3-TWSE-DEFAULT-BOUNDED` | `https://www.twse.com.tw/exchangeReport/STOCK_DAY` (monthly `response=html`, date, stockNo parameters) | 3 official GET dispatches, one per unique month | 0 | 0 |
| H2 `H2-TWSE-EXRIGHT-PRE-OPENAPI` | `https://openapi.twse.com.tw/v1/exchangeReport/TWT48U_ALL` | 1 official GET dispatch | 0 | 0 |

Proposed maximum is four dispatches per integrated attempt and two attempts
per future A6 session, at most eight dispatches; the Owner-session hard ceiling
remains ten. Stop immediately on PASS or hard block. Only separately classified
transient/inconclusive outcomes may continue. No TPEx, TWT49U, TAIFEX,
unofficial API, browser, or bootstrap call is included. Security Master must be
ready before the A6 live session. The H3 route retains its existing provider
automation caveat; this proposal does not resolve that caveat.

## Separate Security Master bootstrap contract

Bootstrap is not part of A6 and has not been run. A future Owner-governed
bootstrap may use only the existing explicit
`python scripts/manage_security_master.py update --root <root> --live` lifecycle.
The current implementation invokes five logical official GET probes: TWSE
listed ISIN, TPEx listed ISIN, TWSE delisted lifecycle, TPEx delisted lifecycle,
and TWSE ETN expiry lifecycle. Each uses a 20-second timeout and 20 MiB response
ceiling. The source probe adds no project retry loop; its allowlisted urllib
redirect handler can cause additional dispatches. Any bootstrap authorization
must account for those redirects separately from the five logical requests.

The materializer writes raw HTML and provenance into ignored
`data/security_master/input_bundles`. The manager then builds a CANDIDATE,
validates schemas, uniqueness and lifecycle consistency, emits a QUALIFIED
release with index/qualification/manifest hashes, and atomically sets
`active.json` to ACTIVE. The release should be preserved with `release_id`,
`active.json`, release/index/manifest/qualification files and hashes, source
provenance hashes, and qualification report. A fresh process is required after
activation because Mode A caches the selected authority for process lifetime.

Bootstrap and a later A6 live run could occur in one Cloud task only if the
release stays available and the process is restarted, but this P0 does not
authorize that combined sequence. If the task is lost, installation-local
data may be lost too. No approved portable restore contract was found; do not
copy historical Candidate B or fixtures. A separate reviewed local backup /
restore contract or a separately authorized bootstrap is needed before A6.

## P0 result

```text
disposition                       = J_B04_A6_P0_BLOCKED_SECURITY_MASTER_NOT_INITIALIZED
architecture inventory           = complete
market GET/HEAD/POST              = 0/0/0
Security Master live acquisition  = 0
H2 runtime                        = INACTIVE
selected executor                 = null
J-B04                             = BLOCKING
Phase J                           = NOT_STARTED
MCP                               = 6
```

Machine-readable details, including paths, schemas, call budgets, and the
observed production loader result, are in the companion JSON record.

## Validation

Network-free A6 identity/inventory tests passed **9/9**. The grouped A5/A3/A6
focused regressions passed **137**, H2/H3/H4 regressions passed **115**, and
Result/Audit/service/Mode A/identity/lifecycle tests passed **76** with **1
skip**. A1/A2/A3, Phase-H V3, Phase-J GHI, portable catalog, runtime guide,
compileall, strict duplicate-key JSON parsing, and `git diff --check` passed.
The strict scan parsed 1,041 JSON files.

The exact base/head default-CI comparison used Python 3.12.14, the same
`/tmp/a5test-venv` dependency set and command on both revisions. Both collected
1,288 nodes: 1,283 selected, 5 deselected, 1,251 passed, 28 failed, and 4
skipped. The exact 28 failed nodes are identical; new and resolved failure sets
are empty, so the computed failure delta is zero. All 28 are in
`test_phase_i_i2_a4_activation.py` and stop because this clean Cloud install has
no ACTIVE Security Master; the underlying failure is `NOT_INITIALIZED`. The
profile reported `network_may_have_occurred=false`.

The legacy A5 repository-scope validators were left unchanged. Their committed
allowlist predates the independently verified Session #2 publication and A5
final closeout, so they reject those already-authoritative artifacts even at
the exact starting baseline. The A5 preflight contract assertions passed, and
the A6 validator checks the A5 closeout and verifies that both historical A5
session trees and closeout remain unchanged from the reviewed baseline.
