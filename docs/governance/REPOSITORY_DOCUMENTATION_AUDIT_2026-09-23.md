# Repository Documentation & Governance Audit — 2026-09-23

Baseline main: `f70c5d8dcd580bbd6c9c66d15dbf76d56ca84c96`

Scope: **repository-wide documentation/governance consolidation only. Phase I
implementation is explicitly out of scope.**

Machine-readable companion:
`docs/governance/REPOSITORY_DOCUMENTATION_AUDIT_2026-09-23.json`.

## Executive result

The repository had accumulated a large and valuable engineering-history corpus,
but current navigation no longer reliably separated present authority from
historical milestone state.

Inventory at the consolidation candidate:

- 2,165 repository blobs;
- 1,429 documentation/config-like text files;
- 744 such files under `docs/`;
- 255 review files;
- 153 protocol files;
- 43 contract files;
- 38 data-capability files;
- 31 governance files.

The correct cleanup is **not** to rewrite or delete hundreds of historical
artifacts. The correct cleanup is to establish a small current authority layer,
archive obsolete planning surfaces where safe, and make historical evidence
obviously historical.

## New repository governance front door

```text
PROJECT.md   current project/product truth
ROADMAP.md   canonical durable Roadmap V3.2
HANDOFF.md   current operational stopping point
AGENTS.md    repository and AI collaboration contract
```

A new human or agent should start with those four files, then inspect current
Catalog/Route/Executor authority and only then open the specific frozen ledger
needed for the task.

## Documentation lifecycle

Four lifecycle classes now govern repository prose:

### CURRENT

Current product/runtime/operator/reference/navigation documents. These must
track present authority.

### FROZEN CONTRACT

Accepted schema, freeze manifest or gate contract. Later runtime promotion does
not authorize rewriting it.

### HISTORICAL EVIDENCE

An accurate record of an earlier state. For example, an H-ACT-H1 ledger saying
"V2 remains preferred" is historically correct even though V3 is preferred now.

### ARCHIVE

Superseded planning/navigation material retained for history but removed from
current authority.

## High-impact drift closed

### Roadmap authority

Roadmap V3.2 existed outside the repo while
`docs/roadmap/M8_POST_M8C_REVISED_ROADMAP.md` still looked current and defined
different Phase H/I meanings.

The complete V3.2 source is now root `ROADMAP.md`, with an explicit
2026-09-23 reconciliation note. The durable 2026-09-14 phase definitions were
not silently rewritten.

### V3 current authority

Root READMEs and several current reference/operator pages still described V2 or
the historical M5/M6 architecture.

Current front-door docs now state:

```text
accepted Requests: V1 / V2 / V3
preferred Request: V3
new Result/Audit: V3
MCP tools: exactly 6
Phase H active routes: exactly one TPEx attention route
complete H1: no
H2/H3: not activated
```

### Catalog metadata

The V3 machine Catalog itself still contained two stale prose limitations:
"V2 remains preferred" and "V3 contract candidate only" for a Phase H
capability.

Those current metadata statements were corrected without changing route
activation, executor selection, source contracts or frozen schemas. Portable
Skill projections were regenerated from the corrected Catalog.

## Archived planning files

Moved from `docs/roadmap/` to `docs/archive/roadmap/`:

- `M8_POST_M8C_REPOSITORY_STATE_INVENTORY.md`
- `M8_POST_M8C_ROADMAP_CONFLICT_MATRIX.md`
- `M8_REMEDIATION_AND_CLEANUP_PLAN.md`
- `NEXT_BUNDLE_ROADMAP_AFTER_M4_OMEGA.md`

Two historical files remain at their exact original paths for compatibility:

- `M8_POST_M8C_REVISED_ROADMAP.md`
- `M8R_05A_F1_AI_GUIDE_SKILL_AND_CONTRACT_REALIGNMENT_MIGRATION_PLAN.md`

The first is referenced by tests and accepted closure evidence; the second is
read by a unit test. They are now excluded from current roadmap navigation and
explicitly classified as historical.

## Historical evidence deliberately not rewritten

The following areas are history/audit-heavy and remain preserved:

- `docs/reviews/`
- `docs/protocol/`
- `docs/acceptance/`
- `docs/acceptance_runs/`
- accepted freeze manifests and ledgers under `docs/governance/`

A phrase that is stale **as current state** may still be correct inside these
documents because it records the state at acceptance time.

## Roadmap reconciliation

This consolidation deliberately does **not** claim that Roadmap Phase G or
Phase H is wholly complete merely because major implementation gates closed.

Phase G has accepted G1/G2 material-disclosure/monthly-revenue runtime evidence.
Roadmap V3.2 Phase G is broader.

Phase H has accepted V3 contracts, deterministic safety, one active H1 route,
selected-product live E2E and H-ACT-V3 promotion. Broader H1 status coverage,
H2 corporate-action execution and H3 recent-reference execution remain
incomplete.

Therefore:

```text
Phase G whole-roadmap completion: not declared
Phase H whole-roadmap completion: not declared
Phase I: NOT STARTED
Phase I implementation authorization: NONE
```

## Current navigation rule

Current docs should point toward the root governance files and current Unified
V3 operator/reference/architecture pages. Historical milestone-specific M5/M6
documents may remain in place when useful for audit or compatibility, but
should not be the first path a new user or agent follows.

## Cleanup anti-patterns

Do not:

- globally replace every "V2 preferred" sentence;
- update old acceptance ledgers to V3 wording;
- delete reviews/protocols just because they are old;
- move exact-path historical evidence when tests or accepted artifacts depend
  on that location;
- use this documentation consolidation as implied authorization for Phase I.

## Exit target

This consolidation closes only when:

1. the four root governance files exist;
2. V3.2 is canonical in the repo;
3. current front-door docs agree with current runtime authority;
4. archived planning material is no longer presented as current;
5. portable Catalog/Skill projections are synchronized;
6. full deterministic CI passes;
7. Phase I remains untouched.
