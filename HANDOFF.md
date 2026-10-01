# HANDOFF.md — Current Operational Handoff

## Status

Date: **2026-10-01**

Baseline main before this documentation-governance consolidation:

`f70c5d8dcd580bbd6c9c66d15dbf76d56ca84c96`

Current workstream:

> **H-ACT-H3 is Owner-accepted. Phase I I1 production activation is
> Owner-accepted and merged after bounded live acceptance and deterministic
> rollback proof. I2-A0/A1 are complete; I2-A2 dormant offline implementation
> is Owner-accepted with zero I2 runtime routes/sources and no selected executor.
> A3 bounded live acceptance is PASS; production activation is NOT_AUTHORIZED.
> I2 remains dormant with zero active sources/routes. I3 is not started.**

The purpose of this handoff is to let a new human or agent resume without
reconstructing the repository from hundreds of historical milestone documents.

## Most recent accepted runtime milestones

### H-ACT-H1

- PR #244
- selected route: `H1-TPEX-ATTENTION-OPENAPI`
- market: TPEx
- capability: `trading_status_context`
- route-level bounded-live: PASS
- route rollback: PASS
- complete H1 coverage: **not claimed**

### H-ACC-7L

- PR #245
- selected-product full governed E2E: PASS
- workflow run: `35797640831`
- Request -> identity -> preview -> authorization -> execute-once -> live TPEx
  -> Result V3 -> Audit V3 -> AI handoff
- broad crawl/polling/retry storm: none

### H-ACT-V3 preflight

- PR #246
- promotion preflight and exact authority inventory: PASS

### H-ACT-V3 promotion

- PR #247
- merge commit: `f70c5d8dcd580bbd6c9c66d15dbf76d56ca84c96`
- workflow run: `35807933991`
- focused promotion acceptance: 5 passed
- default non-network CI: 1241 passed, 4 skipped, 9 deselected
- actual V3 -> V2 preferred-version rollback rehearsal: PASS
- frozen/source activation containment: PASS

## Current runtime truth

```text
Accepted Requests     V1 / V2 / V3
Preferred Request     V3
Preferred new Result  V3
Preferred new Audit   V3
MCP tools             exactly 6
Phase H active source count  2
Active Phase H routes        H1-TPEX-ATTENTION-OPENAPI
                             H3-TWSE-DEFAULT-BOUNDED
H1 complete coverage         NO
H2 activation                NOT STARTED / INACTIVE
H3 TWSE recent_performance   ACTIVE; H0H-LIVE-003 PASS; H0H-ROLL-004 PASS
H3 TPEX                      BLOCKED / NON-EXECUTABLE
Provider automation         NOT_ESTABLISHED_TERMS_CONFLICTED
Phase I I1 implementation    ACCEPTED
I1 bounded live acceptance   ACCEPTED / PASS
I1-ROLL-001                  PASS
I1 production activation     OWNER_ACTIVATION_ACCEPTED / MERGED
Catalog/Routing              runtime_executable / resolved
selected executor            phase_i_i1_market_state_executor
normal production I1 routes  2 (TWSE + TPEX)
Phase I active sources       3
I2-A0                        PASS_GO (one previously Owner-executed bounded probe)
I2-A1                        SOURCE / EVIDENCE CONTRACT FROZEN_PASS
I2-A2                       OWNER_ACCEPTED / DORMANT OFFLINE IMPLEMENTATION
I2-A3                       BOUNDED LIVE ACCEPTANCE PASS / PENDING INDEPENDENT REVIEW
I2 production activation    NOT_AUTHORIZED
I2 runtime                  INACTIVE / NOT PRODUCTION EXECUTABLE
I2 active sources / routes   0 / 0
I2 selected executor        null
I3                           NOT STARTED
Broader Phase I              INCOMPLETE
```

V1/V2 remain compatibility contracts. Existing persisted artifacts retain their
stored schema version.

## Phase G truth

The accepted PR-D closure proves the initial G1/G2 production slice:

- material disclosures;
- monthly revenue;
- TWSE/TPEX eligible company common-share scope;
- official bounded source acquisition;
- Result/Audit/citation integration.

Primary evidence:

- `docs/acceptance_runs/phase_g_pr_d_closure.json`
- `docs/acceptance_runs/phase_g_pr_d_p0_ledger.json`
- `docs/acceptance_runs/phase_g_pr_d_controlled_live.json`

Do not convert this into a claim that every Roadmap V3.2 Phase G research item
is complete.

## Phase H truth

Primary current evidence:

- `docs/governance/phase_h/PHASE_H_H_ACT_H1_TPEX_ATTENTION_ACCEPTANCE_LEDGER.json`
- `docs/governance/phase_h/PHASE_H_H_ACC_7L_SELECTED_PRODUCT_LIVE_E2E_LEDGER.json`
- `docs/governance/phase_h/PHASE_H_H_ACT_V3_PROMOTION_ACCEPTANCE_LEDGER.json`
- `docs/governance/phase_h/PHASE_H_H_ACT_H3_TWSE_RECENT_PERFORMANCE_ACCEPTANCE_LEDGER.json`
- `docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json`
- `docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json`

Important distinction:

> H-ACT-V3 is closed; the full Roadmap Phase H capability scope is not.

The active H1 product slice is TPEx attention only. H3 is limited to the
Owner-accepted bounded TWSE `recent_performance` route; TPEx H3 remains blocked,
H2 remains inactive, and provider automation permission is not established.
Attempt #2E is valid bounded-live evidence after offline corrected acceptance
verification; its original runner nonzero exit remains recorded as a harness
false negative. No new live execution is required for this closure.

## Current closure and next boundary

The H-ACT-H3 final activation is Owner-accepted for the selected bounded TWSE
`recent_performance` route. The route-specific acceptance ledger records the
technical candidate and its live/rollback evidence. Separately, Owner accepted
the frozen Phase I I1 source contract and authorized a bounded,
production-capable executor candidate for `market_state_context`. The separate
`PHASE_I_I1_BOUNDED_LIVE_ACCEPTANCE` gate is accepted PASS under Owner authority;
its ledger is
`docs/governance/phase_i/PHASE_I_I1_BOUNDED_LIVE_ACCEPTANCE_LEDGER_2026-09-30.json`.
The acceptance used exactly three official GETs (TWSE FMTQIK 1, TWSE breadth 1,
TPEx 1), zero retries; TWSE is governed partial due to preserved date mismatch
and TPEx is complete. The final Owner decision accepts production activation
of the selected I1 market-state route. Current runtime authority has two normal
production routes (TWSE and TPEx) and exactly three active I1 sources.
`I1-ROLL-001` passed. No new market requests were made during final activation
closure. I2-A0/A1 are complete. I2-A2 dormant offline implementation is
Owner-accepted; A3 bounded live acceptance is PASS under the fresh single-GET
Owner authority. Runtime remains inactive and production activation is
NOT_AUTHORIZED. I3 is not started. The broader Roadmap Phase I remains incomplete.

I1 timing semantics: acceptance execution/acquisition reference timestamp is
`2026-09-30T01:56:37Z`; each source transport retrieval timestamp is recorded
individually in bounded-live telemetry. Normalized evidence `retrieved_at` uses
the governed execution/acquisition reference timestamp for the I1 v1 contract;
transport telemetry `retrieved_at` is the individual HTTP retrieval observation
time.

## Historical documentation problem already closed

Before this consolidation, repository documentation had multiple competing
eras:

- root/product docs partly current;
- `docs/roadmap/M8_POST_M8C_REVISED_ROADMAP.md` still acted like a current
  roadmap while containing obsolete phase definitions and pre-v1 release prose;
- several operator/reference/architecture pages still described the M5/M6
  product model;
- historical acceptance and reviews correctly preserved old facts but were easy
  to mistake for current state;
- root `AGENTS.md` still described a high-freedom source-discovery project
  rather than the governed product now in the repository.

This consolidation establishes the four-file governance front door:

```text
PROJECT.md   current project/product state
ROADMAP.md   durable Roadmap V3.2 direction and phase scope
HANDOFF.md   current operational stopping point and evidence pointers
AGENTS.md    repository/agent working rules
```

## Resume order

A new agent should read, in order:

1. `PROJECT.md`
2. `ROADMAP.md`
3. `HANDOFF.md`
4. `AGENTS.md`
5. current Catalog/Route authority
6. only then the specific frozen contract/ledger relevant to the task

Do not start by reading hundreds of `docs/reviews/` or `docs/protocol/`
files unless the task requires historical evidence.

## Current allowed next work

I1 production activation has been Owner-accepted and merged after bounded live
acceptance and deterministic rollback proof. Do not repeat live acquisition or
rollback. I2-A0 is PASS_GO and I2-A1 source/evidence contract is FROZEN_PASS.
I2-A2 dormant offline implementation is Owner-accepted. Production runtime
remains inactive and I2 active sources/routes remain zero. I2-A3 bounded live
acceptance is PASS and ready for independent review in Draft PR #298. Its
ledger is `docs/governance/phase_i/PHASE_I_I2_A3_BOUNDED_LIVE_ACCEPTANCE_LEDGER_2026-10-01.json`.
Exactly one TAIFEX GET was used, retry zero, TWSE/TPEx GETs zero. Two target
operations share the acquisition; both are complete, with alignment
not_comparable and currentness unknown. No further live request is authorized.
I3 is not started.

## Explicit stop boundary

**Do not repeat I1 live acceptance or rollback, or the consumed I2-A3 single GET.
I2 production activation and merge are NOT_AUTHORIZED. Do not begin I3 or
Phase J without separate authorization.**

Roadmap Phase I is Cross-Market & Optional Context. I0, I1 source contract,
and I2-A1 source/evidence contract are frozen; I1 is accepted and active. The
one I2-A0 probe is historical preflight evidence only. I2-A2 dormant offline
implementation is Owner-accepted; A3 bounded live acceptance is PASS. Runtime
remains dormant/inactive pending a separate production activation decision.
The old unused A3 authority is superseded_without_use; the fresh single-GET
authority is consumed. I3 remains not started. Broader Phase I is incomplete.

## Before any future Phase I work

At minimum:

1. read `ROADMAP.md` Phase I;
2. establish a Phase I preflight rather than immediately integrating data;
3. apply the Evidence Value Gate to each candidate evidence family;
4. keep derivatives identity separate from cash-security ISIN identity;
5. preserve explicit/optional bounded loading;
6. preserve the accepted I1 evidence; I2/I3 each require separate Owner
   authorization before implementation.

## Historical-document rule

Do not "fix" accepted historical ledgers to match the current V3 state. A
statement such as "V2 remained preferred" inside an H-ACT-H1 ledger is correct
for that gate's time and must remain intact.

Current-state contradictions belong in current entry-point docs, not by
rewriting history.
