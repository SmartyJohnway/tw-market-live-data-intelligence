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

The current authorized workstream is **Post-v1.5 Productization & Stabilization**.
P0 — Current-state Reconciliation is complete and was committed/pushed to `main`
as `430d320784d5249508c37bbd6e8272732bf63ee8` after independent re-review.

The active productization tranche is **P1 — Windows Launcher / First-run UX**.
P1-A0 architecture audit is complete. P1-A1 First-run / Setup UX Contract and
P1-A2 Daily Main Launcher / Runtime Control UX Contract are both **OWNER_FROZEN**
on 2026-10-29. The first independent review of P1-A3 returned
`CHANGES_REQUIRED`; the bounded P1-A3-R1 correction then received an independent
re-review that was also `CHANGES_REQUIRED`. The bounded **P1-A3-R2** correction
closed the two remaining defects; deterministic P1-A3/lifecycle/package
revalidation is `97 passed`. Exact-current Windows Sandbox **R5** headless
lifecycle + fresh interactive GUI acceptance passed against launcher SHA-256
`96f9cbaeaf61d7292aa5ff0e783e32e8d17689056ce8dfdbfa60eedf1e299aa5`, and a
separate interactive failure-path probe verified Setup failure Technical Details
remains `SETUP_BLOCKED / EXISTING_STATE_REQUIRES_EXPLICIT_TRANSFER`. A fresh
Codex independent re-review of P1-A3-R2/R5 returned **PASS_WITH_NOTES** with zero
blocking findings. Owner then explicitly authorized the controlled commit/push.
P1-A3-R2 implementation, tests, R1–R5 evidence and post-v1.5 governance were
committed and pushed to `main` as `3059531b7cb02bede681938228a0f258b8b5b9d9`.
P2–P5 remain later bounded tranches and Phase M remains separately unauthorized.

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
