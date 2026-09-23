# AGENTS.md — Repository Governance and AI Collaboration Contract

## 1. Read this repository in the right order

Before substantial work, read these root governance files:

1. `PROJECT.md` — current product/project truth;
2. `ROADMAP.md` — durable architecture and phase scope;
3. `HANDOFF.md` — current stopping point, accepted evidence, and next boundary;
4. `AGENTS.md` — working rules.

Then inspect the exact current runtime authority and the frozen contract/ledger
for the task. Do not reconstruct "current state" by reading old milestone
documents in chronological order.

## 2. Product objective

TW-Market is:

> **Taiwan Market Evidence & Research Infrastructure for Humans and AI Agents**

It provides governed Taiwan-market identity, evidence acquisition,
normalization, timing/currentness semantics, bounded execution, provenance,
citations, audit, and AI-ready handoff.

It is not a broker, autonomous trader, portfolio accounting system,
general-purpose crawler, general-purpose RAG system, or technical-analysis
signal engine.

## 3. Current contract boundary

Current development-line authority:

- accepted Unified Requests: V1 / V2 / V3;
- preferred Unified Request: V3;
- new governed Result/Audit materialization: V3;
- V1/V2 remain compatibility authorities;
- MCP surface: exactly six tools;
- installation-local Security Master = Taiwan Market Identity Service;
- cash-security durable identity = ISIN;
- listing/routing identity = `MARKET:CODE`;
- Persistent Watchlist = installation-local durable state;
- Phase H active route set is incremental, not implied by schema support.

Never equate "contract exists" with "route executable".

## 4. Current roadmap boundary

Roadmap V3.2 is the durable roadmap authority.

A Roadmap phase is not complete merely because one implementation tranche,
schema, route, or promotion gate closed. Use exact evidence.

As of this governance consolidation:

- initial Phase G G1/G2 runtime evidence exists and is accepted;
- H-ACT-V3 promotion is accepted;
- H1 coverage remains partial;
- H2/H3 activation remains incomplete;
- **Phase I has not started.**

Do not begin Phase I implementation without explicit Owner authorization.

## 5. Authority hierarchy

Use the artifact appropriate to the question:

### Exact historical gate truth

Frozen contracts, manifests, and accepted ledgers govern what was accepted at
that gate. Do not rewrite them after later promotion.

### Current executable product truth

Use current:

- `docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json`
- `docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json`
- executor registry/configuration
- current service implementation and tests

### Current project/roadmap/operations truth

Use root:

- `PROJECT.md`
- `ROADMAP.md`
- `HANDOFF.md`
- `AGENTS.md`

When two artifacts disagree, identify whether one is historical before treating
the disagreement as a defect.

## 6. Documentation lifecycle

Every human-readable document should be understood as one of:

- **CURRENT** — intended to describe current product use or architecture;
- **FROZEN CONTRACT** — accepted and protected contract;
- **HISTORICAL EVIDENCE** — accurate record of an earlier milestone;
- **ARCHIVE** — superseded planning/front-door material retained for history.

Rules:

1. Do not silently update historical evidence to current wording.
2. Do not use historical "next task" prose as current authorization.
3. Do not create a second current roadmap, source catalog, request language, or
   architecture narrative.
4. Prefer updating an existing current authority over adding another parallel
   "current" document.
5. If a document is superseded as a navigation/planning surface, archive it or
   clearly mark it historical.
6. Tests that protect historical artifacts should remain historical tests; add
   separate current-state tests rather than changing history.

## 7. Execution and safety rules

Non-negotiable:

- no trading;
- no order routing;
- no broker credential handling;
- no hidden startup network acquisition;
- no default scheduler;
- no default polling;
- no silent background refresh;
- no broad/unbounded crawl;
- no hidden full-market scan;
- no automatic Watchlist-driven market execution;
- no silent persistent mutation;
- no fixture fallback as production authority;
- no identity-authority fork;
- no unsupported realtime guarantee.

Preview != authorization.

Authorization != execution.

Execution must be explicit, bounded, and auditable.

## 8. Source and evidence discipline

Prefer official authoritative Taiwan-market sources when available.

For every source/evidence family preserve, as applicable:

- source identity and authority;
- target binding;
- source/effective/published/observed time;
- currentness;
- coverage;
- missing/unsupported/not-published/source-failed distinctions;
- fallback use;
- citation;
- lineage;
- raw-artifact policy;
- legal/usage constraints.

Never convert missing to zero. Never convert source failure to
"no evidence". Never use a company-name match as a silent identity fallback.

## 9. Identity discipline

For supported cash securities:

```text
ISIN                     durable instrument identity
MARKET:CODE              current listing/routing identity
name / alias / shorthand metadata only
```

Knowledge universe != execution universe.

A known identity may still be unsupported for a capability.

Successor identity changes require explicit review; do not silently migrate
durable Watchlist references.

## 10. Unified contract discipline

Extend the existing Unified Request/Result family. Do not create a competing
AI-facing request language or parallel execution system.

New evidence families should normally follow:

```text
source inventory
-> source contract
-> capability
-> schema
-> adapter
-> normalization
-> timing/currentness
-> Result projection
-> tests
-> Skill/guide update
-> acceptance
```

The existence of V3 does not authorize every V3 capability route.

## 11. MCP discipline

The current MCP product surface is exactly:

1. `market_describe_capabilities`
2. `market_validate_request`
3. `market_preview_request`
4. `market_read_result`
5. `market_export_ai_handoff`
6. `market_fetch_evidence`

Do not add a seventh tool unless an explicit future contract decision proves
the six-tool surface cannot represent the required semantics.

MCP, Workbench, and Local Service must reuse the same canonical contract and
execution boundaries.

## 12. Network-work discipline

Default development/CI must be non-network.

Live network work requires an explicit bounded acceptance purpose. Record:

- authorization;
- exact target(s);
- exact source route;
- request/call bounds;
- timeout;
- retry policy;
- payload persistence policy;
- result/evidence hashes where governed;
- failure outcome.

Do not convert a live probe into a recurring monitor.

## 13. Test and acceptance discipline

Normal regression baseline:

```bash
python -m compileall -q scripts server tests
python scripts/validate_phase_h_v3_contracts.py
python scripts/validate_portable_catalog_sync.py
python scripts/validate_runtime_skill_guide_sync.py
python scripts/run_test_profile.py default-ci
git diff --check
```

For a change that affects a frozen/current authority, add focused tests for the
specific contract rather than relying only on the full suite.

Do not claim success until the relevant acceptance evidence exists.

## 14. Change discipline

Before implementation:

1. identify the current authority;
2. identify frozen/historical artifacts that must not change;
3. identify allowed mutation surfaces;
4. define rollback target;
5. define acceptance evidence.

During implementation:

- fail closed on unsupported ambiguity;
- preserve compatibility unless the approved change explicitly removes it;
- do not broaden source/network scope to make tests pass;
- keep current-state prose synchronized with runtime truth.

After implementation:

- run focused and full deterministic validation;
- record acceptance;
- verify changed-file containment;
- verify post-merge state if merged.

## 15. Repository areas

Common current-authority areas:

- `server/`
- `scripts/`
- `schemas/`
- `config/`
- `docs/data_capabilities/`
- `docs/governance/`
- `skills/tw-market-evidence-agent/`
- `frontend/unified-workbench/`
- `tests/`

Historical-heavy areas include many files under:

- `docs/reviews/`
- `docs/protocol/`
- `docs/acceptance_runs/`
- `docs/acceptance/`

Do not assume historical-heavy means deletable; these directories contain
important audit evidence.

## 16. Current stop rule

For the present repository state:

> **Do not enter Phase I implementation.**

Documentation cleanup, governance reconciliation, archive organization, and
current-state validation are allowed. A separate Owner authorization is
required before Phase I implementation begins.
