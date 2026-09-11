# V1.0 Release Readiness and Public Contract Freeze Preflight

## Decision

Baseline `2740e4982d77bd3bd192bed4aceeaab8302e4aa6` is feature-complete for Phase F, but it is not release-ready. The next authorized step is one consolidated **V1.0 Release Readiness Implementation & RC Candidate Preparation** tranche. Do not tag or publish `v1.0.0` yet.

Principal decision: `READY_FOR_V1_0_RELEASE_READINESS_IMPLEMENTATION`.

The governing distinction is:

- V1 feature complete: true.
- V1 release ready: false.
- V1 release candidate: false.
- V1 released: false.

No market network or production persistent-state mutation occurred during this audit.

## Baseline and release provenance

- Commit: `2740e4982d77bd3bd192bed4aceeaab8302e4aa6`
- Tree: `a81e93af55527ab78e3c3493010c8a85abdcdcb0`
- Branch: `codex/v1-release-readiness-preflight`
- Current public product version authority: Git tag and GitHub Release `v0.1.0`.
- Tag commit: `804496ca1b015fc8e6340a8ba8c524106fb9d4a2`.
- Release: **v0.1.0 – Initial Local-first Preview**, published 2026-06-30T11:21:07Z, not draft/prerelease, no uploaded assets.
- No other GitHub Release was found.

The FastAPI `version="1.0.0"` is not established product SemVer. It is ambiguous stale OpenAPI metadata attached to an M5F-era title and description. Before v1, one machine-readable product version/release-manifest authority must be established and FastAPI metadata must state whether it is product or API version.

## Product to freeze

Proposed current-first statement:

> **TW-Market Live Data Intelligence — A stable local-first governed Taiwan Market Evidence Workbench.**

The implemented loop is: fresh installation → Security Master initialization → persistent Watchlists or temporary targets → Unified Request → validate → preview → authorize → explicit execute once → Result/Audit → AI handoff.

This is not production market-data infrastructure, a realtime-guaranteed feed, an investment adviser, or a trading/order-routing system.

### Capability boundary

Supported:

- installation-local Security Master and ISIN-based cash identity;
- persistent versioned Watchlists and nonpersistent temporary targets;
- Unified validation, preview, explicit authorization and bounded execute-once;
- Result/Audit reconstruction and AI handoff;
- exact six-tool Unified MCP;
- canonical `/workbench/` browser surface;
- governed TWSE/TPEX evidence routes, subject to currentness/source caveats.

Supported with caveats or plan-only:

- TAIFEX is provisional and non-executable in the Unified production path;
- `recent_performance` is plan-only;
- `session_status` has governed semantics but no production execution route;
- current observations are not automatically realtime.

Stable v1 safety boundaries must include no trading, broker integration, order routing, recommendations, target prices, scheduler, polling, automatic refresh/retry/batching, startup market network, silent persistence, full-market autonomous scan, or credential storage.

## Public contract freeze proposal

`PUBLIC_STABLE_V1`:

- Unified Request, validation/preview behavior, Result and Audit Package v1;
- Capability Catalog v1;
- Watchlist Evidence Selection Request/Selection v1;
- Persistent Watchlist, Entry, Revision, Mutation Command/Preview and Export v1;
- Taiwan Market Identity record/release/status/active-pointer semantics and externally visible resolver statuses;
- exact six Unified MCP tool names and input envelopes;
- structured AI handoff Result/Audit lineage;
- canonical `/workbench/` route.
- current portable Skill user-facing safety/workflow semantics (not exact prose).

`PUBLIC_COMPATIBILITY_V1`:

- `/workbench/mode-a/` redirect, retained through v1.x and removable no earlier than v2;
- governed M5N/M5K Watchlist import through explicit preview/commit.

Internal contracts not to freeze as public include SQLite table layout, control-package filesystem layout, projector internals, executor registry, authorization/receipt/consumption journals, and rendered prose wording. Historical M5/M7 schemas, the legacy MCP server and readonly frontend are not current public authority.

### Foundational semantics

- TWSE/TPEX cash durable identity is ISIN; `MARKET:CODE` is listing/routing identity.
- Names and codes are resolver inputs, not persistence authority.
- Missing a current snapshot is not delisting.
- Successor ISIN requires explicit migration review.
- TAIFEX does not inherit cash identity semantics automatically.
- Watchlist persistence is installation-local, explicit preview/commit, optimistic, revisioned, zero-or-one default, and network-free.
- Temporary targets never become persistent silently; enabled does not mean executable.
- Watchlist Mutation Confirmation, Evidence Authorization, and Network Execute Once Confirmation remain separate.
- Result/Audit lineage and currentness distinctions must not be weakened in 1.x.
- `/workbench/`, the Capability Catalog, Watchlist selection and structured AI handoff retain their required v1 semantics through all v1.x; removal is not before v2.
- Skill wording may improve, but it may not instruct persistence, execution, capability use or confirmation bypass contrary to runtime authority.

### SemVer

- PATCH: defect fixes with no intentional public-contract change.
- MINOR: backward-compatible capabilities, optional fields and additive endpoints.
- MAJOR: breaking identity, required field, machine error category, MCP name/input, compatibility or safety-behavior changes.

Schema versions remain independent: product v1.x may continue to use `*.v1` contracts.

## Unified MCP and Local Service

The exact six names to freeze are:

1. `market_describe_capabilities`
2. `market_validate_request`
3. `market_preview_request`
4. `market_read_result`
5. `market_export_ai_handoff`
6. `market_fetch_evidence`

Names, the exact six-tool baseline, and required parameters are stable through v1.x. Optional backward-compatible fields on existing tools may be added; a seventh canonical tool requires v2-level public-contract governance. Machine error codes/categories should be stable; English prose is not. Read/validate/preview/export operations perform no market network; fetch is the one explicit bounded action. Before v1, correct or explicitly justify the `readOnlyHint=false` metadata on the two semantically read-only Result/handoff tools.

Public error policy: `WATCHLIST_*` categories are stable for v1, but an exact-code allowlist must be generated from current `WatchlistError` authorities before promising exact-code stability. Externally observable `IDENTITY_*` categories are stable while loader details remain internal; legacy Mode A/B/C family names are compatibility/internal unless explicitly surfaced; confirmation/refusal/execute-once categories are stable while adapter prose is not. MCP success is `content[TextContent] + structuredContent + isError=false`; errors carry machine JSON in both content/structuredContent with `isError=true`. For `market_read_result`, the Result is in `structuredContent`; text is only a fixed notice.

`/workbench/` is the canonical public route. `/api/unified/*`, `/api/watchlists/*`, `/api/evidence-request-previews`, and `/api/watchlist-mutations/*` are canonical Workbench backend routes, but should not accidentally be promised as a general external HTTP API without an explicit decision. Legacy M5/M7 and source-health routes require visible deprecation and v2 removal policy. Hidden `/api/probe/*` routes are historical/deprecation candidates.

## Storage and upgrade contract

`data/watchlists/watchlists.sqlite3` is ignored installation-local state using storage schema 1. Current code opens schema 1 and fails closed on unsupported future versions. A git update preserves the ignored database by normal operation.

The v1 commitment should be: keep schema 1 through v1.x unless a tested forward-only migration is introduced; downgrade may be unsupported; recommend explicit Watchlist export/backup before upgrade; never silently migrate user state. Existing-state survival is supported by the current schema-1 component path, but is **not yet proven on an exact RC** and therefore remains a release gate.

The v0.1.0 → v1 path is explicit: install locked v1 → verify environment → inspect/initialize or strictly migrate Security Master → start Local Service → import M5N/M5K Watchlist through governed preview → confirm persistence → validate Workbench and Unified MCP. Existing pre-v1 users must separately verify that their schema-1 database and compatible qualified Security Master remain readable. Candidate A/B history is not an installation prerequisite.

## Current documentation and version drift

P1 before v1:

- README still says **Local Release Candidate**, says there is no persistent Watchlist, centers the old M5K/M5N workflow and old MCP/frontend paths, and presents M8-through-M8C as current architecture.
- `docs/INDEX.md`, `docs/operator/`, `docs/reference/`, and `docs/release/` remain M5-era.
- the canonical Capability Catalog still contains limitation prose saying Unified runtime work belongs to M8R-06 or is unimplemented;
- CHANGELOG has only v0.1.0;
- FastAPI title/description/version are semantically inconsistent;
- no single product-version/release-manifest authority exists.

Target README order: product overview/status → quick start → Security Master → Local Service and `/workbench/` → Unified MCP → core workflow/Watchlists → capability/safety boundaries → testing/docs/upgrade → historical architecture link.

V1 CHANGELOG/release notes must separate Added, Changed, Stable public contracts, Migration, Deprecated, Known limitations, and Security/governance.

## Exact test evidence

All local evidence below ran on the exact baseline and without intentional market network:

| Gate | Result |
|---|---|
| environment verifier | PASS on Windows 10 x64, CPython 3.13.7 |
| pip dependency check | PASS |
| Unified contract validator | PASS |
| runtime/Skill/Guide drift validator | PASS, six tools |
| portable catalog deep equality | PASS |
| Market Evidence Skill validator | PASS |
| Security Master Skill validator | PASS, 201 checks |
| compileall | PASS |
| three canonical Workbench JavaScript syntax checks | PASS |
| operator-preflight | PASS, five authoritative runners |
| browser-e2e profile | PASS check-only; actual Playwright pytest was skipped |
| default-ci | **FAIL: 929 passed, 10 failed, 2 skipped** |
| full-non-network | **FAIL: 2375 passed, 69 failed, 15 skipped, 1 deselected** |
| broad pytest diagnostic | **FAIL: 2376 passed, 69 failed, 15 skipped** |

The earlier milestone closure called the 69-failure broad suite “default CI”; current profile execution proves that label is inaccurate. Actual `default-ci` selects 941 outcomes and has ten failures: nine Mode-C/M8R-05C lineage nodes plus one localhost vertical node.

Compared with the M8R-10 69-node set, 68 nodes are unchanged. The prior environment-sensitive `test_real_stdio_to_actual_loopback_http_service` node resolved, while `test_real_localhost_authorize_execute_once_vertical` newly appears. A same-baseline focused rerun failed after its bounded 30-second health wait with `supported localhost launcher did not become healthy`; it did not reach Mode C. The dependency on non-self-contained launcher/Security Master startup state supports category F (environment-dependent harness), not a proven current behavior defect. This one-for-one migration must still be repaired before release.

The browser profile currently validates an old M6G check-only runner. Because `requirements-browser-e2e.txt` leaves Playwright unpinned and the actual Playwright test skipped, this is not sufficient final v1 browser evidence. The mandatory exact-RC browser gate must cover persistent Watchlists, temporary-target nonpersistence, three distinct confirmations, advanced JSON, Result/Audit/handoff, XSS-safe rendering, CSP-clean execution and zero unauthorized load-time market network.

The broad suite had 15 skips: one missing-Playwright browser path, four expected POSIX-only checks on Windows, nine installation-local sealed/compact Security Master checks, and one active-release HTTP E2E lacking an initialized local release. The browser skip is v1-critical; the local-authority skips require synthetic exact-RC equivalence where applicable rather than copying private installation state.

The operator/browser check-only runners also rewrote three tracked historical reports and created three untracked report/context files. The exact generated paths were inspected and restored/removed; no product state was involved. Release profiles must use isolated external output roots and end with an asserted-clean repository.

### 69-node disposition

| Category | Count |
|---|---:|
| A current product bug | 0 |
| B current public-contract regression | 0 |
| C stale test expectation | 11 |
| D historical fixture/provenance debt | 48 |
| E legacy component outside v1 | 5 |
| F environment-dependent test design | 3 |
| G duplicate/obsolete test | 2 |
| H unknown | 0 |
| **Total** | **69** |

The machine artifact records all 69 exact node IDs and their family/category. No current product defect is proven by these failures, but that is not release permission: red active tests leave important integrity behavior unexercised.

Release-blocking families:

- 14 Security Master Skill-hash fixtures;
- 9 M8R-05C/Mode-C artifact-lineage fixtures;
- 24 historical M5 artifact-binding fixtures;
- 1 M4 evidence ledger;
- 10 M8R-05A stale schema/text expectations;
- 1 stale M5B error-code expectation;
- 4 broken legacy M3G CLI tests;
- 1 legacy Phase-C plugin test;
- 3 non-isolated loopback/operator tests;
- 2 duplicate proxy tests.

Policy: **ACTIVE V1 RELEASE GATES MUST BE GREEN.** Repair or regenerate valid active fixtures, update stale semantic assertions, and archive/reclassify truly historical tests. Do not mass-xfail or weaken integrity checks.

## Dependencies and platform proposal

`requirements-lock.txt` is an exact disposable CPython 3.11.15 / Windows 11 x86_64 graph. The current verifier also passed on CPython 3.13.7, but that is not lock-equivalent evidence. Proposed support is CPython 3.11 minimum/recommended, with 3.13 supported only after exact RC matrix validation. Windows is primary; Linux becomes supported after the exact Ubuntu RC workflow passes; macOS remains unverified.

`requirements-browser-e2e.txt` must pin the tested Playwright version and record the Chromium build. The 1,077 full-suite warnings are `jsonschema.RefResolver` deprecations; migrate to `referencing` or explicitly bound and carry the dependency policy before upstream removal.

## Hygiene, security, and release artifacts

No secret value was proven. Static path-only token/key matches were variable names/placeholders; exact RC still requires a dedicated secrets scan. Ignored runtime/Watchlist/Security Master directories were not tracked and the worktree remained clean.

`mode_a_fixes.patch` is a tracked root patch artifact (P1 archive/remove). `FINAL_DELIVERY_REPORT.md` is a competing historical root report (P2 move/archive).

V1 should publish an immutable annotated tag, GitHub Release, source ZIP/tarball, release notes, and a small machine-readable release manifest containing product version, release commit/tree, Python support, lock hash, public-contract inventory and validation evidence. A desktop executable is not required. The exact RC source archive must be tested because release operation must not depend on `.git` metadata. The repository is MIT-licensed; description/topics exist, homepage is absent, and the description needs current v1 wording before release.

## Release candidate policy

`v1.0.0-rc.1` is recommended because the jump from v0.1.0 adds persistent storage, a new Identity/Security Master architecture, canonical Workbench, public contracts and legacy migration.

Mandatory RC gates: clean fresh install, existing-install upgrade, default-ci, full-non-network, operator preflight, actual canonical browser E2E, Unified MCP, both Skills, environment/contract/drift validators, security scan, documentation link check and manual operator smoke.

One bounded live E2E is `RECOMMENDED_MANUAL_POLICY_BOUND`, not automatic CI: one explicit TWSE:2330 `current_observation` request, one source invocation, no retries/fallback, with source/retrieval timestamps, Receipt, Result, Audit and handoff retained. External volatility must not make reproducible offline correctness nondeterministic.

Exact sequence: merge one consolidated readiness PR → verify exact main SHA/tree → designate an **untagged immutable RC-candidate commit** → run every mandatory gate, including fresh-install, existing-install upgrade and actual browser acceptance, on that exact commit → tag/publish `v1.0.0-rc.1` → collect policy-bound feedback without execution-code drift → if code changes, create and fully validate a new RC → repeat final gates on the exact final commit → tag that commit `v1.0.0` → publish GitHub Release from the same tag. Never tag a mutable branch; release validation must not first occur after publication.

## Required next tranche

One consolidated **V1.0 Release Readiness Implementation & RC Candidate Preparation** PR should:

1. repair/reclassify every active red test and prove exact profile node sets green;
2. align README, index, operator/reference/release docs and archive historical surfaces;
3. establish the product version and release-manifest authority;
4. publish public-contract, SemVer, migration and deprecation policy;
5. pin the browser environment and run canonical Workbench E2E;
6. run exact RC fresh-install, upgrade, MCP, Skills, contracts, security and link gates;
7. draft CHANGELOG and release notes.

No owner decision is required to start that tranche. No security-critical split was proven, so one exact validated candidate state is preferred.

## Blocking findings

- P0: `default-ci` and `full-non-network` are red.
- P1: current public documentation and Capability Catalog prose contradict implemented product state.
- P1: product/API version semantics and public-contract freeze are missing.
- P1: exact RC clean-install, upgrade and canonical browser evidence is missing.
- P1: browser dependency/release process is not reproducibly pinned and pre-tag enforced.
- P1: MCP read-only annotations and the documented category-level output/error freeze remain unfinished; exact Watchlist code stability is intentionally not promised until a future explicit allowlist exists.
- P1: current schema-1 support exists, but exact-RC existing-install survival is unverified.
- P1: release runners write repository report paths and tracked root historical artifacts need disposition.
- P1: exact-RC secret scan and documentation-link evidence are missing.

Therefore `v1.0.0` cannot be released immediately.
