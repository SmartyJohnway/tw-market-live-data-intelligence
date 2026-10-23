# Governance Index

## Current L7-A0 inventory / governance contract (2026-10-24)

L6 remains **CLOSED** under `PHASE_L_L6_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`.
L7 is **STARTED**. L7-A0 is **TECHNICAL INVENTORY / GOVERNANCE CONTRACT COMPLETE**;
**OWNER ACCEPTANCE PENDING** under
`L7_A0_CI_RELEASE_CURRENT_STATE_INVENTORY_AND_GOVERNANCE_CONTRACT_FROZEN`.
**L7-A1+ NOT AUTHORIZED. Stable release / publication NOT AUTHORIZED.
Phase M NOT AUTHORIZED. Phase L NOT CLOSED.** Merge/auto-merge are not authorized.

The 15-obligation inventory freezes the proposed A1-A7 sequence and canonical
29-item final exit contract, with 21 owned gaps. Default CI remains overall FAIL
(1245 passed / 45 failed / 4 skipped / 5 deselected; candidate-only failures=0);
expanded evidence remains FAIL (525 passed / 2 historical assertions). A0 changes
no product, tests, workflows, dependencies, VERSION or GitHub settings. Python,
SDK compatibility, final version and publication decisions remain later work.

Authority/report: `docs/governance/phase_l/PHASE_L_L7_A0_CI_RELEASE_CURRENT_STATE_INVENTORY_AND_GOVERNANCE_CONTRACT_2026-10-23.md`.
Evidence: `docs/governance/phase_l/acceptance_runs/l7-a0-20261023T164344Z/`.
The following L6 closure text is historical authority for L6; its former L7
authorization boundary is superseded only by this bounded A0 authorization.

## Historical L6 closure state ? CLOSED (2026-10-23)

L6 is **CLOSED** under `PHASE_L_L6_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`, following
technical exit `PHASE_L_L6_EXIT_REVIEW_PASS`. L6-A6 is OWNER-ACCEPTED AND MERGED
via PR #406 at normal merge `5a071013a5d0d333f32e1928a4d081904078197a`, tree
`e29ff3fd71805fdeedcd647004e44434ae26f171`; the accepted A6 candidate is
`4bf95ca87211e16e9c53a1a935cf731bdca5ebd3`. Independent review disposition is
`L6_A6_INDEPENDENT_TECHNICAL_REVIEW_PASS`; Owner disposition is
`L6_A6_OWNER_ACCEPTED_FOR_MERGE`.

The accepted exit retains 23/23 L6 criteria PASS, unresolved A0 findings=0,
unresolved A1 gaps=0, P1?P6 PASS, post-A5 product drift=0, exact-six MCP, and L2
as the sole backup/verify/isolated-restore/migration authority. Default CI remains
overall FAIL at 1245 passed / 45 failed / 4 skipped / 5 deselected on both base
and candidate with candidate-only failures=0; expanded validation remains overall
FAIL at 525 passed / 2 unchanged historical L5 scope assertions. Retained A6
limitations remain visible and unchanged.

No L6-A7 is created or authorized. **L7 remains NOT AUTHORIZED. Phase M remains
NOT AUTHORIZED.** Release/signing/publication, image publication, installer work,
and any new product capability remain outside this closure. Phase L itself is not
closed because L7 has not been authorized or completed.

Closure: `docs/governance/phase_l/PHASE_L_L6_OWNER_FINAL_CLOSURE_2026-10-23.md`.
Technical review: `docs/governance/phase_l/PHASE_L_L6_A6_PACKAGING_PORTABILITY_TECHNICAL_EXIT_REVIEW_2026-10-23.md`.
Evidence: `docs/governance/phase_l/acceptance_runs/l6-a6-20261023T141800Z/`.

## Historical L6-A5 merged state (2026-10-23)

L6-A5 is **OWNER-ACCEPTED AND MERGED**. Technical disposition is
`L6_A5_INTEGRATED_P1_P6_PORTABILITY_ACCEPTANCE_PASS`; independent review is
`L6_A5_INDEPENDENT_TECHNICAL_REVIEW_PASS`; Owner disposition is
`L6_A5_OWNER_ACCEPTED_FOR_MERGE`. P1=PASS, P2=PASS, P3=PASS, P4=PASS,
P5=PASS and P6=PASS.

The accepted runtime/package source is `3707c553497240f6ff0f7e5358301395fd60205a`, tree
`946e765b26b2520f623672dc49a51c913139f44f`. The exact accepted A5 candidate is `32bc480cccdd7eb394062ccfe34a44958fc56bf1`,
tree `041f7c660a3fba40b84d5fbab869c2ee353919ac`. PR #404 normal-merged that exact candidate at
`08bec63ec3d924d2c3b206ecc4fcc017b259ea75`, tree `041f7c660a3fba40b84d5fbab869c2ee353919ac`. Merge parents are prior canonical main
`d5dac702c25e9728db86e9ef32f4fe8185086b89` and the accepted A5 candidate; GitHub merge verification is valid.

Accepted artifact identities remain Native ZIP SHA-256 `6772e8c3550525ff0d952929c7e36cef4833e265936b0009b6d517152ab74e04`, Docker source
image `sha256:2b25c1e54879b0761d3c0a3591236cb2a1f820c1530fee25f643ec93cf962675`, and Docker replacement image
`sha256:98bafa33505e0d5f4c088e58949e388768b21b0a0741f4da5649eff539f91323`. Default CI remains FAIL at 1245 passed / 45 failed /
4 skipped / 5 deselected on both exact base and final candidate, with identical failed-node
sets and candidate-only regressions = 0. The expanded applicability suite remains
525 passed / 2 unchanged historical L5 scope-assertion failures. No acceptance result is
rerun or rewritten by this reconciliation.

Phase L/L6 is **not closed**. L6-A6 technical exit review, L7, Phase M,
installer/release work and image publication remain **NOT AUTHORIZED**. The next bounded
action requires separate Owner authorization for L6-A6.

See `docs/governance/phase_l/PHASE_L_L6_A5_INTEGRATED_P1_P6_PORTABILITY_ACCEPTANCE_2026-10-23.md`,
`docs/governance/phase_l/acceptance_runs/l6-a5-20261023T132500Z/`, and
`docs/governance/phase_l/PHASE_L_L6_A5_POST_MERGE_GOVERNANCE_RECONCILIATION_2026-10-23.md`.


This directory contains repository governance and accepted gate evidence.

## Current governance front door

The repository-level governance authority is intentionally small:

- [PROJECT.md](../../PROJECT.md) — current project/product truth
- [ROADMAP.md](../../ROADMAP.md) — durable Roadmap V3.2
- [HANDOFF.md](../../HANDOFF.md) — current operational state
- [AGENTS.md](../../AGENTS.md) — repository working rules

## Historical Phase L / L6-A4 disposition (2026-10-23)

L6-A4 Docker Local Service Packaging is technically complete; Owner acceptance
is pending. P6 is `IMPLEMENTED_A4 / FINAL_ACCEPTANCE_PENDING_A5`. L6-A5, L7 and
Phase M remain unauthorized, and merge is not authorized. See the [A4 technical
record](phase_l/PHASE_L_L6_A4_DOCKER_LOCAL_SERVICE_PACKAGING_2026-10-23.md) and
[acceptance evidence](phase_l/acceptance_runs/l6-a4-20261023T061105Z/).

## Current runtime governance

Phase J remains not started. The [G/H/I integrated Phase J readiness preflight](phase_j/PHASE_J_GHI_INTEGRATED_READINESS_PREFLIGHT_2026-10-05.md)
preserves all J.1 scenarios and records the product-intent realignment to a
two-gap conversational-correctness HOLD;
the [structured record](phase_j/PHASE_J_GHI_INTEGRATED_READINESS_PREFLIGHT_2026-10-05.json)
is the validator input. The preflight makes no market acquisition or product
activation.

I2-A4 and I3-A4 production activation are Owner-accepted. I3 has two active
official sources, one logical route, two runtime market registrations, active
Unified V3 integration, and production evidence V2. PR #301 merged as
`39e162fa9f0b321b23300b20bfac8ce096646b63`. A3 bounded-live evidence was
sufficient for A4 closure; Phase I exit review passed, while Phase J remains
unauthorized. MCP remains six tools.

- [I2-A4 activation candidate and I2-ROLL-001 proof](phase_i/PHASE_I_I2_A4_PRODUCTION_ROUTE_ACTIVATION_CANDIDATE_2026-10-01.json)
- [I2-A4 final production activation acceptance](phase_i/PHASE_I_I2_A4_PRODUCTION_ROUTE_ACTIVATION_ACCEPTANCE_LEDGER_2026-10-01.json)

Current executable truth is governed by:

- [Capability Catalog V3](../data_capabilities/unified_market_evidence_capability_catalog.v3.json)
- [Routing Matrix V3](../data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json)
- executor registry/configuration
- current implementation and tests

## Phase H accepted governance

Key current/historical Phase H evidence:

- [H-ACT-H1 TPEx attention acceptance](phase_h/PHASE_H_H_ACT_H1_TPEX_ATTENTION_ACCEPTANCE_LEDGER.json)
- [H-ACT-H3 TWSE recent-performance final acceptance](phase_h/PHASE_H_H_ACT_H3_TWSE_RECENT_PERFORMANCE_ACCEPTANCE_LEDGER.json)
- [H-ACC-7L selected-product live E2E](phase_h/PHASE_H_H_ACC_7L_SELECTED_PRODUCT_LIVE_E2E_LEDGER.json)
- [H-ACT-V3 promotion preflight](phase_h/PHASE_H_H_ACT_V3_PROMOTION_PREFLIGHT_AND_AUTHORITY_IMPACT_INVENTORY.json)
- [H-ACT-V3 promotion acceptance](phase_h/PHASE_H_H_ACT_V3_PROMOTION_ACCEPTANCE_LEDGER.json)
- [H0-H implementation gate matrix](phase_h/PHASE_H_H0_H_IMPLEMENTATION_GATE_MATRIX.json)

Frozen contracts/manifests under `phase_h/` remain immutable evidence of their
accepted gate. They must not be rewritten merely because the current preferred
runtime later changed.

## Phase I accepted governance

- [I2-A0 TAIFEX TX bounded preflight](phase_i/PHASE_I_I2_A0_TX_REGULAR_SESSION_GO_NO_GO_PREFLIGHT_2026-09-30.json)
- [I2-A1 TX regular-session source/evidence contract (authoritative JSON)](phase_i/PHASE_I_I2_TX_REGULAR_SESSION_SOURCE_EVIDENCE_CONTRACT_2026-09-30_FROZEN.json)
- [I2-A1 TX regular-session source/evidence contract (Markdown companion)](phase_i/Phase_I_I2_TX_Regular_Session_Source_Evidence_Contract_2026-09-30_FROZEN.md)
- [I2-A1 Owner acceptance / merge authorization ledger](phase_i/PHASE_I_I2_A1_SOURCE_EVIDENCE_CONTRACT_ACCEPTANCE_LEDGER_2026-09-30.json)
- [I2-A2 dormant offline implementation candidate](phase_i/PHASE_I_I2_A2_DORMANT_OFFLINE_IMPLEMENTATION_CANDIDATE_2026-09-30.json)
- [I2-A2 Owner acceptance / merge authorization ledger](phase_i/PHASE_I_I2_A2_DORMANT_OFFLINE_IMPLEMENTATION_ACCEPTANCE_LEDGER_2026-10-01.json)
- [I2-A3 historical pre-network governed runner candidate](phase_i/PHASE_I_I2_A3_PRE_NETWORK_GOVERNED_RUNNER_CANDIDATE_2026-10-01.json)
- [I2-A3 single-GET bounded live acceptance PASS](phase_i/PHASE_I_I2_A3_BOUNDED_LIVE_ACCEPTANCE_LEDGER_2026-10-01.json)
- [I2-A3 Owner acceptance / merge closure](phase_i/PHASE_I_I2_A3_OWNER_ACCEPTANCE_AND_MERGE_CLOSURE_2026-10-01.json)
- [I2-A4 technical activation candidate / rollback proof](phase_i/PHASE_I_I2_A4_PRODUCTION_ROUTE_ACTIVATION_CANDIDATE_2026-10-01.json)
- [I2-A4 final production activation acceptance](phase_i/PHASE_I_I2_A4_PRODUCTION_ROUTE_ACTIVATION_ACCEPTANCE_LEDGER_2026-10-01.json)
- [I2 active source authority descriptor](../data_capabilities/phase_i_i2_source_authority.v1.json)(../data_capabilities/phase_i_i2_source_authority.v1.json)
- [I1 frozen source contract](phase_i/PHASE_I_I1_MARKET_STATE_SOURCE_CONTRACT_2026-09-29_FROZEN.json)
- [I1 bounded live acceptance](phase_i/PHASE_I_I1_BOUNDED_LIVE_ACCEPTANCE_LEDGER_2026-09-30.json)
- [I1 technical activation candidate snapshot](phase_i/PHASE_I_I1_PRODUCTION_ROUTE_ACTIVATION_CANDIDATE_2026-09-30.json)
- [I1 final production route activation acceptance](phase_i/PHASE_I_I1_PRODUCTION_ROUTE_ACTIVATION_ACCEPTANCE_LEDGER_2026-09-30.json)
- [I3-A0 final source/timing/symmetry composite GO](phase_i/PHASE_I_I3_A0_FINAL_COMPOSITE_CLOSURE_2026-10-03.json)
- [I3-A1 frozen cash institutional flow source/evidence contract](phase_i/PHASE_I_I3_A1_CASH_INSTITUTIONAL_FLOW_SOURCE_EVIDENCE_CONTRACT_2026-10-03_FROZEN.json)
- [I3-A2-R1 offline optional-detail repair closure](phase_i/PHASE_I_I3_A2_R1_OPTIONAL_SOURCE_NATIVE_FAILURE_SEMANTICS_CLOSURE_2026-10-03.json)
- [I3-A3 Attempt 4 accepted bounded-live evidence](phase_i/PHASE_I_I3_A3_ATTEMPT_4_BOUNDED_LIVE_ADAPTER_ACCEPTANCE_2026-10-04.json)
- [I3-A3-R4 post-live lifecycle and independent-review candidate](phase_i/PHASE_I_I3_A3_R4_ATTEMPT_4_POST_LIVE_LIFECYCLE_AND_INDEPENDENT_REVIEW_CLOSURE_2026-10-04.json)
- [I3-A3 Owner final acceptance closure](phase_i/PHASE_I_I3_A3_OWNER_FINAL_ACCEPTANCE_CLOSURE_2026-10-04.json)
- [I3-A3 final merge / I3-A4 preflight transition](phase_i/PHASE_I_I3_A3_FINAL_MERGE_AND_A4_PREFLIGHT_TRANSITION_2026-10-04.json)
- [I3-A4 production evidence V2 decision](phase_i/PHASE_I_I3_A4_PRODUCTION_EVIDENCE_V2_DECISION_2026-10-04.json)
- [I3-A4 technical activation candidate](phase_i/PHASE_I_I3_A4_TECHNICAL_ACTIVATION_CANDIDATE_2026-10-04.json)
- [I3-A4 bounded production activation implementation](phase_i/PHASE_I_I3_A4_BOUNDED_PRODUCTION_ACTIVATION_2026-10-05.json)
- [I3-A4 portable lineage sync repair](phase_i/PHASE_I_I3_A4_ACTIVATION_ACCEPTANCE_R1_PORTABLE_LINEAGE_SYNC_2026-10-05.json)
- [I3-A4 final Owner acceptance and closure](phase_i/PHASE_I_I3_A4_FINAL_OWNER_ACCEPTANCE_AND_CLOSURE_2026-10-05.json)
- [Phase I final exit review](phase_i/PHASE_I_FINAL_EXIT_REVIEW_2026-10-05.json)
- [Phase I final closure](phase_i/PHASE_I_FINAL_CLOSURE_2026-10-05.json)

Technical-candidate records remain historical. The final I1/I2/I3 acceptance
ledgers govern their respective capabilities; the Phase I exit review and
closure record the completed Roadmap Phase I scope.

I2-A0 is accepted preflight evidence. I2-A1 source/evidence contract, I2-A2
dormant implementation, and I2-A3 bounded-live acceptance are accepted historical
gates. I2-A4 production activation is independently reviewed and Owner-accepted:
the selected executor is `phase_i_i2_index_futures_context_executor`, with one
active TAIFEX source and one normal approval-gated TWSE production route.
`I2-ROLL-001` preserves deterministic rollback to `7ffbdf7f...`. The earlier
unused I2 live authority is superseded_without_use. I3-A3 bounded-live adapter
acceptance is independently reviewed and Owner-accepted. Attempts 1–3 remain
historical HOLD outcomes; Attempt 4 is accepted PASS. I3-A4 technical candidate
implementation including production evidence V2 and Public V3 integration is
now production-active, Owner-accepted, and merged on PR #301: two official
sources, one logical route, and two runtime market registrations. A3 evidence
was sufficient; final A4 closure performed no market GET. Phase I exit review
passed; Phase J remains unauthorized. MCP remains exactly six tools.

## Governance policy

- [Governance policy manifest](governance_policy_manifest.json)
- [Workflow policy matrix](workflow_policy_matrix.json)

## Documentation lifecycle

Use four classes:

1. **CURRENT** — current product/runtime/navigation.
2. **FROZEN CONTRACT** — accepted contract/gate authority.
3. **HISTORICAL EVIDENCE** — earlier milestone truth.
4. **ARCHIVE** — superseded navigation/planning material.

A historical statement is not a current-status bug unless the document is still
presented as a current authority.
