# HANDOFF.md — Current Operational Handoff

## Current I3-A4 stopping point (2026-10-05)

I3-A0 is `GO_PASS`, I3-A1 is `FROZEN_PASS`, and I3-A2-R1 is `PASS`.
I3-A3 is `OWNER_ACCEPTED_INDEPENDENTLY_ACCEPTED_BOUNDED_LIVE_PASS` under
`docs/governance/phase_i/PHASE_I_I3_A3_OWNER_FINAL_ACCEPTANCE_CLOSURE_2026-10-04.json`.
Attempts 1–3 remain historical HOLD outcomes; Attempt 4 is the accepted PASS.
Its single-use live authority is consumed. No further A3 acquisition or
Attempt 5 is authorized or required.

I3-A4 is `OWNER_ACCEPTED_INDEPENDENTLY_ACCEPTED_PRODUCTION_ACTIVATION_PASS` and
closed under final Owner acceptance. Current topology is two active
official sources, one logical same-market route, and two default-runtime
market executor registrations. Governed TWSE date binding is pre-authorization;
Public V3 and evidence V2 are active. This tranche performed no market GETs.
Additional live acceptance was not required. PR #301 merged as
`39e162fa9f0b321b23300b20bfac8ce096646b63`. Phase I final exit review passed;
Phase J is not started or authorized. MCP remains exactly six tools.

Activation ledger:
`docs/governance/phase_i/PHASE_I_I3_A4_BOUNDED_PRODUCTION_ACTIVATION_2026-10-05.json`.

Final Owner acceptance closure:
`docs/governance/phase_i/PHASE_I_I3_A4_FINAL_OWNER_ACCEPTANCE_AND_CLOSURE_2026-10-05.json`.

Phase I exit review and closure:
`docs/governance/phase_i/PHASE_I_FINAL_EXIT_REVIEW_2026-10-05.json`;
`docs/governance/phase_i/PHASE_I_FINAL_CLOSURE_2026-10-05.json`.

## Current I2 production activation boundary (2026-10-01)

I2-A4 production activation is Owner-accepted and merge-authorized.

- Catalog: `index_futures_context` is runtime executable with
  `phase_i_activation_state=selected_route_active`.
- Routing: resolved, approval required, `same_source`, selected
  `phase_i_i2_index_futures_context_executor`; one normal TWSE production route.
- Source authority: one active TAIFEX source; eligible cash targets remain TWSE
  company/common shares. Loading is explicit/optional only, never startup refresh.
- `I2-ROLL-001`: PASS; deterministic rollback target remains
  `7ffbdf7fb102668457b2a15877c10ad7673da9bf`.
- No additional market request was authorized or performed for activation.
- I1 remains active with two routes and three sources; MCP remains exactly six.
- I3-A3 and I3-A4 are Owner-accepted and merged; Phase I exit review passed.
  Phase J is not started or authorized.

Activation evidence:

`docs/governance/phase_i/PHASE_I_I2_A4_PRODUCTION_ROUTE_ACTIVATION_CANDIDATE_2026-10-01.json`

`docs/governance/phase_i/PHASE_I_I2_A4_PRODUCTION_ROUTE_ACTIVATION_ACCEPTANCE_LEDGER_2026-10-01.json`

## Status

Date: **2026-10-05**

Baseline main before this documentation-governance consolidation:

`f70c5d8dcd580bbd6c9c66d15dbf76d56ca84c96`

Current workstream:

> **H-ACT-H3 is Owner-accepted. Phase I I1 production activation is
> Owner-accepted and merged. I2-A0/A1/A2/A3 are accepted, and I2-A4 final
> production activation is Owner-accepted with rollback proof. `index_futures_context`
> is production executable on one approval-gated TWSE route backed by one active
> TAIFEX source. I3-A3 bounded-live adapter acceptance is Owner-accepted.
> I3-A4 production activation is Owner-accepted and closed; live acquisition
> was not performed for A4 closure.**

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
I2-A3                       OWNER_ACCEPTED / BOUNDED LIVE PASS / MERGE AUTHORIZED
I2 production activation    OWNER_ACTIVATION_ACCEPTED
I2 runtime                  PRODUCTION EXECUTABLE / APPROVAL-GATED
I2 active sources / routes   1 / 1
I2 selected executor        phase_i_i2_index_futures_context_executor
I3-A3                        OWNER_ACCEPTED / BOUNDED LIVE PASS
I3 active sources            2 (TWSE + TPEX)
I3 logical production route  1 (same_market)
I3 runtime market routes    2 (TWSE + TPEX)
I3 A4                        OWNER_ACCEPTED / CLOSED / MERGED
I3 final-closure market GETs 0; additional A4 live acceptance not required
Phase I                      EXIT REVIEW PASS / COMPLETE
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
Owner authority. I2 runtime is now active under its separately accepted A4
route. I3-A3 is Owner-accepted. At the time of this 2026-10-04 I1 activation
snapshot, I3 production remained inactive; the later I3-A4 activation is
documented in the current handoff section above. The broader Roadmap Phase I
remains incomplete.

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
I2-A2 dormant offline implementation and I2-A3 bounded-live acceptance are
accepted historical stages. I2-A4 production activation is now Owner-accepted
and merge-authorized for PR #299. Its
live ledger is `docs/governance/phase_i/PHASE_I_I2_A3_BOUNDED_LIVE_ACCEPTANCE_LEDGER_2026-10-01.json`; the Owner acceptance / merge closure ledger is
`docs/governance/phase_i/PHASE_I_I2_A3_OWNER_ACCEPTANCE_AND_MERGE_CLOSURE_2026-10-01.json`.
Exactly one TAIFEX GET was used, retry zero, TWSE/TPEx GETs zero. Two target
operations share the acquisition; both are complete, with alignment
not_comparable and currentness unknown. No further live request is authorized.
I3-A3 and I3-A4 are Owner-accepted. I3 production is active; additional live
acquisition was not required. PR #301 is merged; Phase I exit review passed.

## Explicit stop boundary

**Do not repeat I1 live acceptance or rollback, the consumed I2-A3 single GET,
or I3-A3 live acceptance. Preserve accepted evidence. I3-A4 is closed,
Owner-accepted, and merged. Phase I exit review is PASS; Phase J remains
unauthorized.**

Roadmap Phase I is Cross-Market & Optional Context. I0, I1 source contract,
and I2-A1 source/evidence contract are frozen; I1 is accepted and active. The
one I2-A0 probe is historical preflight evidence only. I2-A2 dormant offline
implementation is Owner-accepted; A3 bounded live acceptance is PASS. Runtime
is production executable under the accepted I2-A4 route. I3-A3 is separately
Owner-accepted. This paragraph is a historical checkpoint preceding the
2026-10-05 activation; current I3 authority is summarized at the top of this
handoff. The old unused A3 authority is superseded_without_use and the fresh
single-GET authority is consumed. At that historical checkpoint, broader Phase I
was incomplete; the current exit disposition is recorded in the Phase I final
exit review linked above.

## Before any future Phase I work

At minimum:

1. read `ROADMAP.md` Phase I;
2. preserve the completed I3-A0 preflight and A1 frozen contract; do not
   repeat source acquisition under consumed A3 authority;
3. apply the Evidence Value Gate to each candidate evidence family;
4. keep derivatives identity separate from cash-security ISIN identity;
5. preserve explicit/optional bounded loading;
6. preserve accepted I1/I2/I3 evidence; Phase I is closed. Any future change to
   a production authority requires separate authorization, and Phase J is not
   authorized by this closure.

## Historical-document rule

Do not "fix" accepted historical ledgers to match the current V3 state. A
statement such as "V2 remained preferred" inside an H-ACT-H1 ledger is correct
for that gate's time and must remain intact.

Current-state contradictions belong in current entry-point docs, not by
rewriting history.
