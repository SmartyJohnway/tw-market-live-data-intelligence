# PROJECT.md — Current Project Authority

This file describes **current** TW-Market project/product truth. It is not a chronological milestone log.
Historical root snapshots are preserved under
[`docs/archive/frontdoor/2026-10-28-pre-f3/`](docs/archive/frontdoor/2026-10-28-pre-f3/),
and detailed accepted evidence remains under `docs/governance/`, `docs/acceptance_runs/`,
`docs/reviews/`, and `docs/protocol/`.

## Project identity

**tw-market-live-data-intelligence** is local-first Taiwan market evidence and
research infrastructure for humans and AI agents.

> **Taiwan Market Evidence & Research Infrastructure for Humans and AI Agents**

It provides governed identity resolution, bounded official-source evidence,
normalization, timing/currentness, provenance, citations, auditability, and
AI-ready handoff. It is not a broker, autonomous trader, quote terminal,
general-purpose crawler, or investment-advice system.

## Current stable product

- ProductVersion: `1.5.0`
- Stable GitHub release: `v1.5.0` (published 2026-10-28)
- Frozen source commit: `acaf726a5b59baee4c5a30521ea5a5d5ec0cec76`
- Frozen source tree: `d44f66dc154c21326ac8b105d2f15fd793f6071b`
- Native Tier-1: Windows 11 x64
- Canonical release/build/CI runtime: CPython 3.13
- MCP SDK policy: exact `mcp==1.29.0`

The frozen v1.5.0 tag/assets remain the release authority even after `main`
advances through post-release documentation or future development commits.
GitHub v1.5.0 publication is complete; MCP Registry publication remains a
separate surface and is not implied by the GitHub release.

## Current runtime authority

Accepted Unified Request contracts: V1 / V2 / V3.

Current preferred family:

- Request: `unified_market_evidence_request.v3`
- Result: `unified_market_evidence_result.v3`
- Audit: `unified_market_evidence_audit_package.v3`

V1/V2 remain compatibility authorities. Existing persisted V1/V2/V3 artifacts
remain readable under their stored version and must not be silently rewritten.

The Unified MCP surface remains exactly six tools:

1. `market_describe_capabilities`
2. `market_validate_request`
3. `market_preview_request`
4. `market_read_result`
5. `market_export_ai_handoff`
6. `market_fetch_evidence`

Canonical execution remains:

```text
Request
-> Validate / Identity
-> Preview
-> explicit authorization
-> execute once
-> Result
-> Audit
-> AI Handoff
```

Preview is not authorization. Authorization is not execution. Executability is
determined by current Catalog / Routing / executor authority, not by schema or
capability names alone.

## Identity and durable local state

The installation-local Security Master is the Taiwan Market Identity Service.
For supported cash securities:

- durable instrument identity = ISIN;
- listing/routing identity = `MARKET:CODE`;
- names/aliases = metadata only.

Fresh installations may correctly report `NOT_INITIALIZED`; missing identity
authority fails closed.

Persistent Watchlists are installation-local durable user state with immutable
revisions, optimistic concurrency, explicit preview/commit mutation, and no
silent conversation-to-Watchlist persistence or successor-identity rewrite.

## Current capability state

Current accepted runtime includes, among other bounded evidence families:

- official material disclosures and latest available monthly revenue for the
  accepted TWSE/TPEx common-share scope;
- `market_state_context` on accepted I1 production routes;
- `index_futures_context` through the accepted bounded TAIFEX-backed I2 route;
- `cash_institutional_flow_context` through accepted I3 production routes;
- selected Phase H trading-status / recent-performance routes where current
  Catalog/Routing authority marks them executable.

Phase G/H historical implementation depth must not be converted into a claim
that every durable Roadmap G/H item is complete. Current executability always
comes from the machine-readable Catalog / Routing / executor authority.

## Lifecycle status

- Phases A–F and V1 Release Gate: completed product foundation.
- Phase I: COMPLETE.
- Phase J: COMPLETE.
- Phase K: COMPLETE.
- Phase L: **CLOSED** under Owner final closure on 2026-10-28.
- L7 canonical exit contract: 29/29 PASS.
- Stable v1.5.0 GitHub publication: PASS.
- Phase M: **NOT_AUTHORIZED**.

The current workstream remains **Post-v1.5 Productization & Stabilization**.
P0 and the original P1 Windows Launcher tranche are complete. Subsequent bounded
stabilization produced three local commits on `main` ahead of `origin/main`:
Launcher v2 / native-entry guard (`b38fde12`), explicit verified-TLS compatibility
retry for Security Master (`8b482be4`), and Native packaging closure for the Mode
B2 execute-once wrapper (`b84f9fc8`). RMA then produced additional bounded,
RMA-accepted candidate repairs across lifecycle/Launcher, deterministic verified TLS,
Result V3 truthfulness, Workbench request/preview/authorization UX, explicit
network-confirmation UX, and Mode C handoff projection. Those repairs are accepted
RMA candidate content selected for the Owner-authorized local clean-source gate; GitHub publication remains separately governed.

The **RMA — v1.5.1 Real-Machine Acceptance & Patch Release Preflight** tranche is
now complete. It validated the actual Windows Native Launcher -> installation/runtime
-> Security Master -> Local Service -> six-tool MCP -> explicit
Request/Preview/Authorization -> Mode B2 -> official evidence -> Result/Audit /
AI Handoff chain. `VERSION` is selected as `1.5.1` for an unpublished local
candidate. Frozen v1.5.0 tag/assets remain unchanged; exact Native final-build
and release gate are separate from the already closed RMA program.

RMA is governed by the post-v1.5 RMA Test Contract, Defect Register, per-group
closure records and Release Preflight/Continuity record. `RMA-0` through `RMA-11`
are all **PASS/CLOSED**. The final defect register contains zero open blockers and
zero open majors; `RMA-D022` and `RMA-D025` remain explicitly preserved as
`DEFERRED_NON_BLOCKING` observations rather than being erased.

RMA-4 proved `/api/health`, Local Service contract v2, MCP startup-check, stdio
initialize, exact six-tool `tools/list`, all six public tool paths, Request
V1/V2/V3 validation/preview, and Capability Catalog access on the current
candidate. The existing Stable `tw-market-local` deployment separately proved the
real Native -> Local Service -> MCP -> Secure MCP Tunnel -> ChatGPT deployment
path without repointing or modifying Stable. Harness-only `RMA-D008` is
`CLOSED_PASS`.

RMA-5 proved public identity resolution across code, `MARKET:CODE`, ISIN, Chinese
name, TPEx common-share and non-common-share cases, plus fail-closed treatment of
unsupported and nonexistent targets. The current Security Master contains no
natural exact-token ambiguity across the exhaustively scanned identity tokens.
Harness-only `RMA-D009` and `RMA-D010` are `CLOSED_PASS`.

RMA-6 proved the governed capability execution chain through offline inventory,
Validate/Preview, explicit authorization, Execute Once, Result/Audit materialization,
and bounded governed rejection. `RMA-D013` exposed a real Result V3 false-success
projection defect for failed typed evidence; its bounded repair passed affected and
cross-version regression plus a fresh targeted network-enabled Sandbox retest and
is now `CLOSED_PASS`.

RMA-7 — Official-source / TLS matrix is now **PASS/CLOSED**. It reproduced and
localized `RMA-D001`, proved cold Windows/Python trust-store timing dependence,
qualified the bundled certifi trust set against all 23 production source cases,
and completed an authorized bounded repair. Fresh packaged cold-Sandbox retest
returned 23/23 production routes usable with certificate/hostname verification,
zero retry, correct strict/compatibility semantics, and 23/23 product parser/schema
PASS. `RMA-D001` is `CLOSED_PASS`.

RMA-8 — Result / Audit / evidence integrity is now **PASS/CLOSED**. Fresh final-candidate
success cases independently verified Control Package/authorization binding, receipt,
bundle, durable evidence bytes/hashes, citation mapping, Result V3, Audit Package,
replay lineage and persisted/API/Handoff consistency without using chat output as
proof. Harness-only `RMA-D016` and `RMA-D017` are `CLOSED_PASS`.

RMA-9 — Failure and recovery matrix is now **PASS/CLOSED**. Fresh network-disabled
Sandboxes proved truthful/fail-closed handling and bounded recovery for stopped
service, unavailable MCP, port conflict, stale ownership, missing runtime,
Security Master unavailable/corrupt state, invalid Request V3, unsupported
capability, Control Package tamper and official-source unavailability. Harness-only
`RMA-D018` and `RMA-D019` are `CLOSED_PASS`; no new RMA-9 product defect was found.

RMA-10 — Native package / portability is now **PASS/CLOSED**. A fresh
network-disabled Windows Sandbox validated the same exact Native candidate from two
independently extracted locations, with identical package-manifest identity and
49/49 locked-wheel closure. Launcher, CLI, Security Master CLI, Local Service,
MCP startup and packaged Mode B2 entry all passed without developer-checkout or
Stable-installation paths present in the guest. Package tamper was rejected and
exact-byte restoration recovered normal operation. The cleanup-only RMA-D018
class was reused and remains `CLOSED_PASS`; no RMA-10 product defect was found.

RMA-11 — Operator experience acceptance is now **PASS/CLOSED**. Owner-driven E2E
validated first-time setup, Security Master, Start/Workbench, request composition,
validation/preview recovery, explicit authorization, network confirmation,
Execute Once, Result/Audit export and AI-ready handoff. Bounded repairs closed
`RMA-D020`, `RMA-D021`, `RMA-D023`, `RMA-D024`, `RMA-D026` and `RMA-D027`.
`RMA-D022` and transient `RMA-D025` are retained as `DEFERRED_NON_BLOCKING`.

`RMA-0` through `RMA-11` are therefore **PASS/CLOSED**. RMA itself is complete.
Owner separately authorized v1.5.1 local clean-source promotion and Native final-build
gate on 2026-11-04; RMA closure itself did not authorize publication. P2–P5 remain later
bounded tranches and Phase M remains separately unauthorized.

## Current authority hierarchy

When sources disagree, classify the fact before resolving it:

1. frozen schemas/contracts and accepted ledgers govern their historical gate;
2. current Catalog / Routing / executor configuration governs executability;
3. `PROJECT.md` governs current project/product state;
4. `HANDOFF.md` governs the current operational stopping point;
5. `ROADMAP.md` governs durable phase scope and direction;
6. `AGENTS.md` governs repository/AI working rules;
7. current operator/reference/architecture docs govern usage details.

Historical evidence is authoritative about what was true at that gate. It is not
current-state authority merely because it is detailed.

## Current front doors

- [README.md](README.md) — public product entry point
- [Operator Quick Start](docs/operator/QUICK_START.md) — Native / MCPB / source paths
- [Documentation Index](docs/INDEX.md) — persona-oriented documentation navigation
- [ROADMAP.md](ROADMAP.md) — canonical Roadmap V3.2
- [HANDOFF.md](HANDOFF.md) — current operational handoff
- [AGENTS.md](AGENTS.md) — collaboration and repository rules
- [Project History](docs/PROJECT_HISTORY.md) — high-level chronology
- [Governance Index](docs/governance/INDEX.md) — governance/evidence navigation

## Non-negotiable product boundaries

No trading or order routing; no broker credential handling; no hidden startup
market fetch; no default polling or scheduler; no silent background refresh; no
hidden full-market scan; no unbounded crawl; no silent persistent mutation; no
parallel identity authority; no competing AI-facing request/result core; no
fixture promoted into production authority; and no unsupported realtime claim.

Missing, unsupported, not-published, stale, and source-failed remain distinct.
Evidence is not an investment conclusion.
