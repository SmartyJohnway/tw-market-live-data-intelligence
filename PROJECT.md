# PROJECT.md — Current Project Authority

## Project identity

**tw-market-live-data-intelligence** is a local-first Taiwan market evidence and
research infrastructure for humans and AI agents.

Product positioning:

> **Taiwan Market Evidence & Research Infrastructure for Humans and AI Agents**

The project provides governed identity resolution, market/research evidence,
bounded execution, provenance, currentness, citations, auditability, and
AI-ready handoff. It is not a broker, autonomous trader, technical-analysis
signal engine, general-purpose crawler, or investment-advice system.

## Current product baseline

- Stable product release: `v1.0.0`
- Stable release commit: `e02bcb125999f542308a75f349c212f0ff3fee83`
- Stable release tags/releases are immutable historical product authorities.
- The current development line extends the stable product without retagging or
  rewriting the `v1.0.0` release.
- Canonical long-term roadmap: [ROADMAP.md](ROADMAP.md), Roadmap V3.2.
- Current operational handoff: [HANDOFF.md](HANDOFF.md).
- Agent/repository working rules: [AGENTS.md](AGENTS.md).

## Current runtime authority

The current development line has completed H-ACT-V3 promotion.

### Unified contract family

Accepted request contracts:

- `unified_market_evidence_request.v1`
- `unified_market_evidence_request.v2`
- `unified_market_evidence_request.v3`

Current preferred authority:

- Request: `unified_market_evidence_request.v3`
- New governed Result materialization: `unified_market_evidence_result.v3`
- New governed Audit materialization: `unified_market_evidence_audit_package.v3`

V1 and V2 remain compatibility contracts. Existing persisted V1/V2/V3
artifacts remain readable under their stored version and must not be silently
rewritten.

### Unified MCP

The MCP surface remains exactly six tools:

1. `market_describe_capabilities`
2. `market_validate_request`
3. `market_preview_request`
4. `market_read_result`
5. `market_export_ai_handoff`
6. `market_fetch_evidence`

Do not infer that a preferred contract change authorizes a seventh tool.

### Execution model

Canonical flow:

```text
AI / Human
  -> Unified Request
  -> Validate / identity resolution
  -> Preview
  -> explicit authorization
  -> execute once
  -> Result
  -> Audit
  -> AI Handoff
```

Preview is not authorization. Authorization is not execution. Network execution
is explicit, bounded, and governed by the current Catalog/Route/Executor truth.

## Identity and persistence authority

### Taiwan Market Identity Service

The installation-local Security Master is the Taiwan Market Identity Service.

For supported cash-market securities:

- durable instrument identity = ISIN;
- listing/routing identity = `MARKET:CODE`;
- names/aliases are metadata, never durable primary identity.

A fresh installation may legally be `NOT_INITIALIZED`. Missing identity
authority fails closed; fixtures or historical Candidate B data must not become
silent production fallback.

### Persistent Watchlists

Persistent Watchlists are installation-local durable user state with:

- ISIN durable references;
- immutable revision history;
- optimistic concurrency;
- explicit preview -> commit mutation;
- no silent conversation-to-watchlist persistence;
- no silent successor-identity rewrite.

## Implemented post-v1 capability state

### Phase G implementation evidence

The repository contains accepted Phase G PR-D evidence for the initial G1/G2
runtime slice:

- official material disclosures for eligible TWSE/TPEX company common shares;
- latest available official monthly revenue;
- controlled, bounded official source acquisition;
- Result/Audit/citation integration;
- V1 compatibility;
- no scheduler/polling/background research warehouse.

The accepted closure is
`docs/acceptance_runs/phase_g_pr_d_closure.json`.

This does **not** mean every item described by Roadmap Phase G is complete.
Roadmap V3.2 includes a broader research-evidence ambition; therefore the
Roadmap Phase G checkbox remains a separate Owner-level completion decision.

### Phase H implementation evidence

Completed governance/runtime milestones include:

- frozen V3 Request/Result/Audit contracts;
- H4 deterministic discontinuity-safety contract and projection;
- one activated bounded-live H1 route:
  `H1-TPEX-ATTENTION-OPENAPI`;
- selected-product H-ACC-7L live E2E;
- H-ACT-V3 promotion to preferred V3 runtime authority;
- actual V3-preferred -> V2-preferred rollback rehearsal.

Current Phase H source truth:

- active Phase H sources: exactly 1;
- TPEx attention route: executable;
- broader H1 types remain uncovered/inactive;
- H2 corporate-action activation: not started;
- H3 recent-reference activation: not started;
- complete H1 coverage must not be claimed.

Accepted promotion ledger:
`docs/governance/phase_h/PHASE_H_H_ACT_V3_PROMOTION_ACCEPTANCE_LEDGER.json`.

Again, H-ACT-V3 closure is a runtime/governance milestone, not proof that the
entire Roadmap Phase H scope is finished.

## Roadmap status

The durable Roadmap V3.2 phase definitions live in [ROADMAP.md](ROADMAP.md).

Current interpretation:

- Phases A-F and V1 Release Gate: established product foundation.
- Phase G: substantial accepted implementation exists; broader Roadmap phase
  completion is not declared by this file.
- Phase H: substantial contract/runtime work exists and V3 promotion is
  complete; broader H1/H2/H3 Roadmap coverage remains incomplete.
- **Phase I: not started.**
- No Phase I implementation is authorized merely by completing this
  documentation/governance consolidation.

## Current authority hierarchy

When artifacts disagree, do not guess. Use this order for the type of fact
being resolved:

1. frozen schemas/contracts and accepted acceptance ledgers for the historical
   gate they govern;
2. current runtime Catalog/Route/Executor configuration for executable product
   truth;
3. `PROJECT.md` for current project/product state;
4. `HANDOFF.md` for the current operational stopping point and next action;
5. `ROADMAP.md` for durable direction and phase scope;
6. `AGENTS.md` for collaboration and repository working rules;
7. current operator/reference/architecture docs;
8. historical reviews, protocols, milestone roadmaps, and archived documents.

Historical evidence is authoritative about **what was true at that gate**. It
is not automatically current-state authority.

## Documentation lifecycle

Repository prose must be classified as one of:

- **CURRENT** — describes current product/runtime/governance;
- **FROZEN CONTRACT** — immutable accepted contract or gate authority;
- **HISTORICAL EVIDENCE** — accurate snapshot of an earlier state;
- **ARCHIVE** — superseded planning/entry-point material retained for history.

Never perform global prose replacement across historical acceptance evidence
just because current runtime state changed.

## Core validation

The default deterministic/non-network profile remains the normal regression
gate:

```bash
python -m compileall -q scripts server tests
python scripts/validate_phase_h_v3_contracts.py
python scripts/validate_portable_catalog_sync.py
python scripts/validate_runtime_skill_guide_sync.py
python scripts/run_test_profile.py default-ci
git diff --check
```

Live network acceptance is separate, bounded, explicitly authorized, and must
not be inferred from ordinary CI.

## Non-negotiable product boundaries

- no trading or order routing;
- no broker credential handling;
- no hidden startup market fetch;
- no default polling or scheduler;
- no silent background refresh;
- no hidden full-market scan;
- no unbounded crawl;
- no silent persistent mutation;
- no parallel identity authority;
- no competing AI-facing request/result core;
- no fixture promoted into production authority;
- missing/unsupported/failed/stale are distinct semantics;
- evidence is not an investment conclusion.
