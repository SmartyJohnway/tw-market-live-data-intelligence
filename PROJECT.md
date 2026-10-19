# PROJECT.md — Current Project Authority

## Current L5 state — A1 technical contract freeze (2026-10-18)

L4 is CLOSED under `PHASE_L_L4_OWNER_ACCEPTED_FINAL_CLOSURE_PASS` after technical
exit `PHASE_L_L4_EXIT_REVIEW_PASS`. L5 is STARTED under
`USER_CHAT_2026-10-18_PHASE_L_L5_ENTRY_AND_A0_EXTENSION_SURFACE_INVENTORY_AUTHORIZATION`.
L5-A0 is **OWNER-ACCEPTED AND MERGED** via PR #380 at `241a5249987c008a28d959677704eee483a1c216`, with disposition
`L5_A0_EVIDENCE_FAMILY_EXTENSION_SURFACE_INVENTORY_COMPLETE`.
The 14-capability inventory maps 12 descriptive archetypes plus non-capability H4;
13 representative traces cover all 14 capabilities. The minimum evidence-family extension contract is technically frozen by L5-A1; Owner acceptance is pending. Assessment: `PLUGIN_FRAMEWORK_NOT_REQUIRED_NOW`; no new family or runtime change.
Required offline baseline checks pass; extra default-ci baseline remains non-green
(1,248 passed, 41 failed, four skipped, five deselected), explicitly preserved for review.
See `docs/governance/phase_l/PHASE_L_L5_A0_EVIDENCE_FAMILY_EXTENSION_SURFACE_INVENTORY_2026-10-18.md`
and `docs/governance/phase_l/acceptance_runs/l5-a0-20261018T110810Z/offline_review.json`.
See `docs/governance/phase_l/PHASE_L_L5_A1_MINIMUM_EVIDENCE_FAMILY_EXTENSION_CONTRACT_2026-10-18.md` and `docs/governance/phase_l/acceptance_runs/l5-a1-20261018T140202Z/offline_validation.json`.
L5-A1: OWNER-ACCEPTED AND MERGED under `L5_A1_MINIMUM_EVIDENCE_FAMILY_EXTENSION_CONTRACT_OWNER_ACCEPTED_FOR_MERGE` via PR #382 at `8ff92ca79af821a8641967184a26ee37db69d326`.
L5-A2+ is NOT AUTHORIZED. L6-L7 is NOT AUTHORIZED. Phase M remains NOT AUTHORIZED.
L5-A0 is Owner-accepted and merged via PR #380 at `241a5249987c008a28d959677704eee483a1c216`. L5-A1 Owner-accepted and merged under `L5_A1_MINIMUM_EVIDENCE_FAMILY_EXTENSION_CONTRACT_OWNER_ACCEPTED_FOR_MERGE` via PR #382 at `8ff92ca79af821a8641967184a26ee37db69d326`; L5-A2+ remains NOT AUTHORIZED.

## Current Phase L boundary (2026-10-17)

L3 is CLOSED under `PHASE_L_L3_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`. Its technical exit passed under `PHASE_L_L3_EXIT_REVIEW_PASS`. A0-A6 are Owner-accepted and merged. A6's accepted live disposition remains PARTIAL (17 transport-degraded logical sources, six HTTP-200 sources, zero deterministic contract drift proven); its one-shot authority is consumed and a second run is prohibited. L4-A0 through A4 are Owner-accepted and merged. L4-A5 is Owner-accepted and merged at c8c23e2; L4-A6 is OWNER-ACCEPTED AND MERGED under `L4_A6_RESOURCE_LOAD_CONCURRENCY_ACCEPTANCE_OWNER_ACCEPTED_FOR_MERGE`, with technical disposition `L4_A6_RESOURCE_LOAD_CONCURRENCY_ACCEPTANCE_PASS` (PR #375; merge commit `9a3a274df1f2602dced30633ea5fa119bc39d0e6`); L4-A7 technical exit review passed under `PHASE_L_L4_EXIT_REVIEW_PASS`; L4 is CLOSED under `PHASE_L_L4_OWNER_ACCEPTED_FINAL_CLOSURE_PASS` after A7 merge through PR #378 at `e184e2b5abfabc4656943d9734e4dc68230a8bbd`; L5 is STARTED; L5-A0 is Owner-accepted and merged via PR #380 at `241a5249987c008a28d959677704eee483a1c216`; L5-A1 Owner-accepted and merged under `L5_A1_MINIMUM_EVIDENCE_FAMILY_EXTENSION_CONTRACT_OWNER_ACCEPTED_FOR_MERGE` via PR #382 at `8ff92ca79af821a8641967184a26ee37db69d326`; L5-A2+ and L6-L7 remain NOT AUTHORIZED.

Roadmap Phase J and Phase K are **COMPLETE**. Phase K closed under
`PHASE_K_OWNER_ACCEPTED_FINAL_CLOSURE_PASS` with three evaluated hosts, two
`NATIVE_PASS`, one bounded `HOST_LIMITATION`, zero product compatibility defects,
and zero fresh market/source acquisition during K2-B.

Phase L — Production Hardening & Extension Architecture is now **STARTED**. L0 —
Production Boundary & Architecture Contract is **FROZEN** under
`PHASE_L_L0_ARCHITECTURE_CONTRACT_FROZEN` in
`docs/governance/phase_l/PHASE_L_L0_PRODUCTION_BOUNDARY_AND_ARCHITECTURE_CONTRACT_2026-10-13.md`.
The contract freezes D01-D12: product goal, versioning rule, Windows platform tiers,
Native/Docker deployment profiles, machine/user/path/state portability, application/state
separation, state classes, configuration precedence, lifecycle UX, migration/rollback,
backup/restore, and optional Agent integrations. Provisional release target is `v1.5.0`;
`v2.0.0` requires an explicitly approved breaking change.

L1 — Runtime Operability is **CLOSED** under
`PHASE_L_L1_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`. Its merged scope covers lifecycle,
structured operational diagnostics/correlation, adapter/source timing, failure-code reuse,
and bounded resource snapshots.

L2 - Replay / Retention / Migration is **CLOSED** under
`PHASE_L_L2_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`. L2-A0 current persistence/replay
inventory is complete under `L2_A0_CURRENT_PERSISTENCE_REPLAY_INVENTORY_COMPLETE`; L2-A1
replay semantics are frozen under `L2_A1_REPLAY_SEMANTICS_CONTRACT_FROZEN`, with package vs
installation-state classification placement clarified under
`L2_A1_R1_STATE_CLASSIFICATION_SCOPE_CLARIFICATION_FROZEN`.

L2-A2 - Read-Only Finalized Package Inspector / Replayability Classifier has passed technical
review under `L2_A2_READ_ONLY_REPLAYABILITY_INSPECTOR_ACCEPTANCE_REVIEW_PASS`; Owner acceptance
is recorded under `L2_A2_READ_ONLY_REPLAYABILITY_INSPECTOR_OWNER_ACCEPTED_FOR_MERGE`. It adds an internal zero-write/zero-network package inspector only.
Public `market_read_result`, HTTP/MCP contracts, backup/restore, retention, and migration remain
unchanged.

L2-A3 - Retention Classification & Policy has passed technical review under
`L2_A3_RETENTION_CLASSIFICATION_AND_POLICY_ACCEPTANCE_REVIEW_PASS` and is Owner-accepted under
`L2_A3_RETENTION_CLASSIFICATION_AND_POLICY_OWNER_ACCEPTED_FOR_MERGE` and is merged through PR #345
at `378acb454a4e1e4e82e2be14b5957dc7d912f751`.

L2-A4 - Backup Manifest & Verification has passed technical review under
`L2_A4_BACKUP_MANIFEST_AND_VERIFICATION_ACCEPTANCE_REVIEW_PASS` and is Owner-accepted under
`L2_A4_BACKUP_MANIFEST_AND_VERIFICATION_OWNER_ACCEPTED_FOR_MERGE` and is merged through PR #347 at
`fb2fef0c50c3ee50581bc62af534b36116b332e7`.

L2-A5 - Restore Compatibility & Bounded Restore has passed technical review under
`L2_A5_RESTORE_COMPATIBILITY_AND_BOUNDED_RESTORE_ACCEPTANCE_REVIEW_PASS`, is Owner-accepted under
`L2_A5_RESTORE_COMPATIBILITY_AND_BOUNDED_RESTORE_OWNER_ACCEPTED_FOR_MERGE`, and is merged through
PR #349 at `97386f756f2dcc6dbf4d3ee7934a41066fa1b0c2`. A5 remains internal and does not activate
restored state or apply migration.

L2-A6 - Migration & Rollback Lifecycle has passed technical review under
`L2_A6_MIGRATION_AND_ROLLBACK_LIFECYCLE_ACCEPTANCE_REVIEW_PASS`, is Owner-accepted under
`L2_A6_MIGRATION_AND_ROLLBACK_LIFECYCLE_OWNER_ACCEPTED_FOR_MERGE`, and is merged through PR #351
at `e090ae353cb00d3b1d076cdb40c5a76cf2229d5d`. A6 keeps A4 as immutable source/checkpoint,
preserves A5 `MIGRATION_REQUIRED` zero-restore-write semantics, and has no production transformer
for `watchlist-schema-v0-to-v1`. The integrated L2 exit review passed under
`PHASE_L_L2_EXIT_REVIEW_PASS`, and Owner final closure is recorded under
`PHASE_L_L2_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`; PR #353 merged at
`b84ba8a4ac4819d115de33e55cf9adf2a5801e00`. L2 is CLOSED. See
`docs/governance/phase_l/PHASE_L_L2_EXIT_REVIEW_2026-10-15.md`.

L3 — Source Drift Hardening is **STARTED**. L3-A0 source-drift inventory is complete under
`L3_A0_SOURCE_DRIFT_SURFACE_INVENTORY_COMPLETE`, passed independent review under
`L3_A0_SOURCE_DRIFT_SURFACE_INVENTORY_ACCEPTANCE_REVIEW_PASS`, and is Owner-accepted under
`L3_A0_SOURCE_DRIFT_SURFACE_INVENTORY_OWNER_ACCEPTED_FOR_MERGE`; PR #355 merged at
`1983c1d5363fe3253a3c5e556508ba5138163337`. Current acquisition contracts and drift gaps are
documented in `docs/governance/phase_l/PHASE_L_L3_A0_SOURCE_DRIFT_SCOPE_AND_INVENTORY_2026-10-15.md`.
L3-A1 TWSE MIS returned-identity/response-contract guard passed independent review under
`L3_A1_TWSE_MIS_RESPONSE_CONTRACT_GUARD_ACCEPTANCE_REVIEW_PASS`, is Owner-accepted under
`L3_A1_TWSE_MIS_RESPONSE_CONTRACT_GUARD_OWNER_ACCEPTED_FOR_MERGE`, and merged through PR #357
at `b2e1908fb5d2e584b38bc354f88df6e121b7b13b`. L3-A2 passed independent review under
`L3_A2_EOD_DIAGNOSTIC_PROPAGATION_GUARD_ACCEPTANCE_REVIEW_PASS`, is Owner-accepted under
`L3_A2_EOD_DIAGNOSTIC_PROPAGATION_GUARD_OWNER_ACCEPTED_FOR_MERGE`, and merged through PR #359
at `e521a2fcc73ecd40e819a0d51342abcd4a55354c`. It propagates bounded TWSE/TPEx EOD batch and
row-validation diagnostics through existing Unified envelopes without public schema or source-acquisition changes.
L3-A3 — Phase G research CSV structure and bounded attempt provenance — passed independent
technical review under `L3_A3_RESEARCH_SOURCE_STRUCTURE_AND_PROVENANCE_GUARD_ACCEPTANCE_REVIEW_PASS`,
is Owner-accepted under `L3_A3_RESEARCH_SOURCE_STRUCTURE_AND_PROVENANCE_GUARD_OWNER_ACCEPTED_FOR_MERGE`,
and merged through PR #361 at `ddd023f11a23420c096a5b20022848cfcf900db9`. It hardens P04-P07
row-width/header validation and preserves primary CSV failure codes through the existing governed
JSON fallback; public schemas remain unchanged.

L3-A4 — H1 composite deterministic negative-fixture matrix — is complete and
has passed independent technical review under
`L3_A4_H1_COMPOSITE_NEGATIVE_FIXTURE_MATRIX_ACCEPTANCE_REVIEW_PASS`. It covers
the current fixed P08/P09/P10 composite and R1 source-local versus unexpected
exception boundary without changing production runtime. Reviewer verification
reconciled the direct missing-required-field matrix so P08/P09/P10 are each
covered. It is Owner-accepted under
`L3_A4_H1_COMPOSITE_NEGATIVE_FIXTURE_MATRIX_OWNER_ACCEPTED_FOR_MERGE` and merged through PR #363 at
`ff330f94049adce93c72a9179b4d7b44d297fb2b`. L3-A5 passed independent technical review under `L3_A5_SOURCE_LIFECYCLE_THROTTLING_AND_PUBLICATION_DRIFT_CONTRACT_ACCEPTANCE_REVIEW_PASS`, is Owner-accepted under `L3_A5_SOURCE_LIFECYCLE_THROTTLING_AND_PUBLICATION_DRIFT_CONTRACT_OWNER_ACCEPTED_FOR_MERGE`, and merged through PR #365 at `d2b3be8bafa3ad0eebeec5ffbece1fc6a759b3bd`. G05 deterministic contract and A6 bounded live recertification are complete. A6 is Owner-accepted and merged with technical disposition PARTIAL; 17 sources were transport-degraded, six returned HTTP 200, and zero deterministic contract drift was proven. The one-shot authority is consumed and a second run is prohibited. A7 technical exit review passed under `PHASE_L_L3_EXIT_REVIEW_PASS`; L3 is CLOSED under `PHASE_L_L3_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`. L4-A0 through A4 are Owner-accepted and merged; A4 merged through PR #373 at `a2dfd7ff7c062257a7c7c8f193fced4f9c707a29`; L4-A5 is Owner-accepted and merged at c8c23e2; L4-A6 is OWNER-ACCEPTED AND MERGED under `L4_A6_RESOURCE_LOAD_CONCURRENCY_ACCEPTANCE_OWNER_ACCEPTED_FOR_MERGE`, with technical disposition `L4_A6_RESOURCE_LOAD_CONCURRENCY_ACCEPTANCE_PASS` (PR #375; merge commit `9a3a274df1f2602dced30633ea5fa119bc39d0e6`); L4-A7 technical exit review passed under `PHASE_L_L4_EXIT_REVIEW_PASS`; L4 is CLOSED under `PHASE_L_L4_OWNER_ACCEPTED_FINAL_CLOSURE_PASS` after A7 merge through PR #378 at `e184e2b5abfabc4656943d9734e4dc68230a8bbd`; L5 is STARTED; L5-A0 is Owner-accepted and merged via PR #380 at `241a5249987c008a28d959677704eee483a1c216`; L5-A1 Owner-accepted and merged under `L5_A1_MINIMUM_EVIDENCE_FAMILY_EXTENSION_CONTRACT_OWNER_ACCEPTED_FOR_MERGE` via PR #382 at `8ff92ca79af821a8641967184a26ee37db69d326`; L5-A2+ and L6-L7 remain NOT AUTHORIZED. See
`docs/governance/phase_l/PHASE_L_L3_A4_H1_COMPOSITE_NEGATIVE_FIXTURE_MATRIX_2026-10-15.md`.
See `docs/governance/phase_l/PHASE_L_L3_A5_SOURCE_LIFECYCLE_THROTTLING_AND_PUBLICATION_DRIFT_CONTRACT_2026-10-15.md`.
See also
`docs/governance/phase_l/PHASE_L_L3_A3_RESEARCH_SOURCE_STRUCTURE_AND_PROVENANCE_GUARD_2026-10-15.md`.
Frozen L0 implementation sequencing places Source Drift Hardening in L3; old Roadmap subject
numbering is retained.

L1-A0 current runtime inventory is complete, including A0R removal of historical A6
accounting from current H2/H3 product paths. L1-A1 minimum lifecycle/status/doctor passed
`L1_A1_ACCEPTANCE_REVIEW_PASS`, was Owner-accepted/merge-authorized under
`L1_A1_OWNER_ACCEPTED_FOR_MERGE`, and is merged in main through PR #335.

The post-A1 **Operational Correlation Foundation** passed
`L1_OPERATIONAL_CORRELATION_FOUNDATION_ACCEPTANCE_REVIEW_PASS`, was Owner-accepted under
`L1_OPERATIONAL_CORRELATION_FOUNDATION_OWNER_ACCEPTED_FOR_MERGE`, and is merged through
PR #336 at `e16303935fef75a38159c5cebfd7b74c37fd33f3`. It provides dedicated operational
`trace_id` propagation across MCP, Local Service, and execute-once boundaries plus bounded
ephemeral diagnostics while keeping Audit as governed truth and preserving the exact
six-tool/public contract surfaces.

The subsequent **Adapter Execution Timing** tranche passed technical review under
`L1_ADAPTER_EXECUTION_TIMING_ACCEPTANCE_REVIEW_PASS`, was Owner-accepted under
`L1_ADAPTER_EXECUTION_TIMING_OWNER_ACCEPTED_FOR_MERGE`, and is merged through PR #337 at
`ea0f4683e662b8d3f89c032ea94dd1ab139cebe2`. It measures monotonic elapsed time only at the
common controlled adapter/batch-adapter callable boundary and emits bounded operational events
without modifying adapter results, canonical artifacts, source transports, routing, or
authorization semantics.

The **Bounded Resource Snapshots** tranche passed technical review under
`L1_BOUNDED_RESOURCE_SNAPSHOTS_ACCEPTANCE_REVIEW_PASS`, was Owner-accepted under
`L1_BOUNDED_RESOURCE_SNAPSHOTS_OWNER_ACCEPTED_FOR_MERGE`, and is merged through PR #338 at
`42ca42d8bbe12b591a266e1ea6637a70477a6e22`. It adds instantaneous best-effort
managed-service memory and application/runtime disk-free observations plus Local Service
process-memory event metrics, without background sampling, threshold policy, capacity
enforcement, or governed-artifact changes.

The next bounded selection chose **Source Acquisition Timing Coverage**, again without assigning
an A2 name. Its implementation has passed technical review under
`L1_SOURCE_ACQUISITION_TIMING_ACCEPTANCE_REVIEW_PASS`, was Owner-accepted under
`L1_SOURCE_ACQUISITION_TIMING_OWNER_ACCEPTED_FOR_MERGE`, and is merged through PR #339 at
`b3d6722d174f91da3e9c7cba4cf11e2f1306102b`. The tranche adds bounded monotonic source-call
timing across current production acquisition seams while preserving existing source
transport/error semantics and the historical frozen I1 live-tested implementation. See
`docs/governance/phase_l/PHASE_L_L1_SOURCE_ACQUISITION_TIMING_2026-10-14.md`.

The formal L1 Exit Review passes technically under `PHASE_L_L1_EXIT_REVIEW_PASS` and is
Owner-closed under `PHASE_L_L1_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`. L1 is **CLOSED**. L2 is also
**CLOSED** under `PHASE_L_L2_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`; A0/A1 are complete/frozen,
A2-A6 are merged/closed, and the A7 integrated exit review passed under
`PHASE_L_L2_EXIT_REVIEW_PASS`. PR #353 merged the final L2 closure at
`b84ba8a4ac4819d115de33e55cf9adf2a5801e00`. See the Phase L recovery index and L2 exit record
under `docs/governance/phase_l/`. L3-A0 inventory is Owner-accepted and merged through PR #355
at `1983c1d5363fe3253a3c5e556508ba5138163337`; L3-A1 is Owner-accepted and merged through PR #357
at `b2e1908fb5d2e584b38bc354f88df6e121b7b13b`; L3-A2 is Owner-accepted under
`L3_A2_EOD_DIAGNOSTIC_PROPAGATION_GUARD_OWNER_ACCEPTED_FOR_MERGE` and merged through PR #359
at `e521a2fcc73ecd40e819a0d51342abcd4a55354c` after independent technical review PASS.
L3-A3 passed independent technical review, is Owner-accepted under
`L3_A3_RESEARCH_SOURCE_STRUCTURE_AND_PROVENANCE_GUARD_OWNER_ACCEPTED_FOR_MERGE`, and merged through
PR #361 at `ddd023f11a23420c096a5b20022848cfcf900db9`. A4 passed independent technical review under
`L3_A4_H1_COMPOSITE_NEGATIVE_FIXTURE_MATRIX_ACCEPTANCE_REVIEW_PASS`, is Owner-accepted under
`L3_A4_H1_COMPOSITE_NEGATIVE_FIXTURE_MATRIX_OWNER_ACCEPTED_FOR_MERGE`, and merged through PR #363 at
`ff330f94049adce93c72a9179b4d7b44d297fb2b`. L3-A5 passed independent technical review under `L3_A5_SOURCE_LIFECYCLE_THROTTLING_AND_PUBLICATION_DRIFT_CONTRACT_ACCEPTANCE_REVIEW_PASS`, is Owner-accepted under `L3_A5_SOURCE_LIFECYCLE_THROTTLING_AND_PUBLICATION_DRIFT_CONTRACT_OWNER_ACCEPTED_FOR_MERGE`, and merged through PR #365 at `d2b3be8bafa3ad0eebeec5ffbece1fc6a759b3bd`. G05 live recertification is recorded in A6. A6 is Owner-accepted and merged with technical disposition PARTIAL. A7 technical exit review is `PHASE_L_L3_EXIT_REVIEW_PASS`; L3 is CLOSED under `PHASE_L_L3_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`; L4-A0 through A4 are Owner-accepted and merged; A4 merged through PR #373 at `a2dfd7ff7c062257a7c7c8f193fced4f9c707a29`; L4-A5 is Owner-accepted and merged at c8c23e2; L4-A6 is OWNER-ACCEPTED AND MERGED under `L4_A6_RESOURCE_LOAD_CONCURRENCY_ACCEPTANCE_OWNER_ACCEPTED_FOR_MERGE`, with technical disposition `L4_A6_RESOURCE_LOAD_CONCURRENCY_ACCEPTANCE_PASS` (PR #375; merge commit `9a3a274df1f2602dced30633ea5fa119bc39d0e6`); L4-A7 technical exit review passed under `PHASE_L_L4_EXIT_REVIEW_PASS`; L4 is CLOSED under `PHASE_L_L4_OWNER_ACCEPTED_FINAL_CLOSURE_PASS` after A7 merge through PR #378 at `e184e2b5abfabc4656943d9734e4dc68230a8bbd`; L5 is STARTED; L5-A0 is Owner-accepted and merged via PR #380 at `241a5249987c008a28d959677704eee483a1c216`; L5-A1 Owner-accepted and merged under `L5_A1_MINIMUM_EVIDENCE_FAMILY_EXTENSION_CONTRACT_OWNER_ACCEPTED_FOR_MERGE` via PR #382 at `8ff92ca79af821a8641967184a26ee37db69d326`; L5-A2+ and L6-L7 remain NOT AUTHORIZED.

## Current I3 production boundary (2026-10-05)

`cash_institutional_flow_context` A0 source preflight is `GO_PASS`, A1 is
`FROZEN_PASS`, A2-R1 is `PASS`, and A3 bounded-live adapter acceptance is
`OWNER_ACCEPTED_INDEPENDENTLY_ACCEPTED_BOUNDED_LIVE_PASS`. Attempts 1–3 remain
historical HOLD outcomes; Attempt 4 is the accepted PASS. Its live authority is
consumed, and no further A3 acquisition or Attempt 5 is authorized or required.

I3-A4 is **OWNER_ACCEPTED_INDEPENDENTLY_ACCEPTED_PRODUCTION_ACTIVATION_PASS**
and closed under final Owner acceptance. The default runtime has two
market-specific I3 executor registrations (TWSE/TPEX), one logical same-market
route, two official source authorities, governed pre-authorization TWSE date
binding, Unified V3 support, and production evidence V2. This tranche performed
no market acquisition; additional live acceptance was not required. PR #301
merged as `39e162fa9f0b321b23300b20bfac8ce096646b63`. The Phase I final exit
review is `PHASE_I_OWNER_ACCEPTANCE_CANDIDATE_EXIT_PASS`; Roadmap Phase I is
complete. Phase J is not authorized; MCP remains six tools.

Owner acceptance evidence:

`docs/governance/phase_i/PHASE_I_I3_A3_OWNER_FINAL_ACCEPTANCE_CLOSURE_2026-10-04.json`

Activation implementation ledger:

`docs/governance/phase_i/PHASE_I_I3_A4_BOUNDED_PRODUCTION_ACTIVATION_2026-10-05.json`

Final Owner acceptance closure:

`docs/governance/phase_i/PHASE_I_I3_A4_FINAL_OWNER_ACCEPTANCE_AND_CLOSURE_2026-10-05.json`

Phase I final exit review and closure:

`docs/governance/phase_i/PHASE_I_FINAL_EXIT_REVIEW_2026-10-05.json`

`docs/governance/phase_i/PHASE_I_FINAL_CLOSURE_2026-10-05.json`

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
- I3-A3 and I3-A4 are Owner-accepted. I3 production is active; see the current
  I3 production boundary above. Phase J is not started and broader Phase I
  remains incomplete.

Activation evidence:

`docs/governance/phase_i/PHASE_I_I2_A4_PRODUCTION_ROUTE_ACTIVATION_CANDIDATE_2026-10-01.json`

`docs/governance/phase_i/PHASE_I_I2_A4_PRODUCTION_ROUTE_ACTIVATION_ACCEPTANCE_LEDGER_2026-10-01.json`

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
- one Owner-accepted bounded TWSE H3 route:
  `H3-TWSE-DEFAULT-BOUNDED` for `recent_performance`;
- selected-product H-ACC-7L live E2E;
- H-ACT-V3 promotion to preferred V3 runtime authority;
- actual V3-preferred -> V2-preferred rollback rehearsal.

Current Phase H source truth:

- active Phase H sources: exactly 2 — `H1-TPEX-ATTENTION-OPENAPI` and
  `H3-TWSE-DEFAULT-BOUNDED`;
- TPEx attention route: executable;
- broader H1 types remain uncovered/inactive;
- H2 corporate-action activation: not started/inactive;
- H3 TWSE `recent_performance` route: active for the selected bounded route;
  TPEx H3 remains blocked/non-executable;
- provider automation permission remains
  `NOT_ESTABLISHED_TERMS_CONFLICTED`; Owner-controlled use is not provider
  approval;
- complete H1 coverage must not be claimed.

H-ACT-H3 final activation closure is recorded in
`docs/governance/phase_h/PHASE_H_H_ACT_H3_TWSE_RECENT_PERFORMANCE_ACCEPTANCE_LEDGER.json`.
The route-level `H0H-LIVE-003` and `H0H-ROLL-004` gates are accepted. Attempt
#2E is the accepted bounded-live evidence; its original runner nonzero
exit is retained as a historical acceptance-harness false negative and no new
live run is required. Separately, the Phase I I1 production-capable implementation
candidate and its bounded live acceptance are accepted. On the existing PR #295
branch, the selected production route is Owner-accepted after deterministic
rollback rehearsal; the route is active in the accepted runtime authority.
The I1 bounded live acceptance ledger is
`docs/governance/phase_i/PHASE_I_I1_BOUNDED_LIVE_ACCEPTANCE_LEDGER_2026-09-30.json`.
Final production-route activation is Owner-accepted and recorded in
`docs/governance/phase_i/PHASE_I_I1_PRODUCTION_ROUTE_ACTIVATION_ACCEPTANCE_LEDGER_2026-09-30.json`.

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
- **Phase I I1:** the production-capable implementation, bounded live
  acceptance, and production-route activation are `ACCEPTED / PASS` under
  separate Owner decisions. `market_state_context` is runtime executable via
  the resolved `phase_i_i1_market_state_executor` route for TWSE and TPEx,
  backed by exactly three active I1 sources and two normal production registry
  routes. The route preserves TWSE partial/date-mismatch semantics, exact
  `股票` breadth selection, source-native units, explicit approval, and no
  polling/history/background behavior. Evidence is loaded only when explicitly
  requested and authorized. I2-A4 is Owner-accepted and active. I3-A3 is
  Owner-accepted bounded-live adapter evidence. I3-A4 is now Owner-accepted
  and active with two sources, one logical route, and two runtime registrations;
  The Phase I final exit review passed; optional candidates remain deferred.
  Phase J is complete under the 2026-10-12 closure authority reconciliation;
  Phase K is complete under `PHASE_K_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`. K2-A completed all eight deterministic assets with no preparation gaps; K2-B completed the three-host pilot with Hermes Agent and ChatGPT `NATIVE_PASS`, Antigravity CLI `PARTIAL_HOST_LIMITATION` / `HOST_LIMITATION`, host evaluation count three, zero product compatibility defects, and zero fresh market/source requests.

I1 bounded-live timing semantics are recorded without changing the accepted
evidence: the execution/acquisition reference timestamp is
`2026-09-30T01:56:37Z`; per-source transport retrieval timestamps are recorded
individually in the bounded-live telemetry; normalized evidence `retrieved_at`
uses the governed execution/acquisition reference timestamp for the I1 v1
contract; transport telemetry `retrieved_at` is each individual HTTP retrieval
observation time.

Phase I I2-A0 reached `PASS_GO` from the single Owner-executed bounded TAIFEX
probe recorded in
`docs/governance/phase_i/PHASE_I_I2_A0_TX_REGULAR_SESSION_GO_NO_GO_PREFLIGHT_2026-09-30.json`.
I2-A1 `index_futures_context` source/evidence contract is frozen `FROZEN_PASS`
in
`docs/governance/phase_i/PHASE_I_I2_TX_REGULAR_SESSION_SOURCE_EVIDENCE_CONTRACT_2026-09-30_FROZEN.json`.
Phase I I2-A2 dormant offline implementation is Owner-accepted under
`docs/governance/phase_i/PHASE_I_I2_A2_DORMANT_OFFLINE_IMPLEMENTATION_ACCEPTANCE_LEDGER_2026-10-01.json`.
I2 runtime is production executable after Owner acceptance: it has one active
TAIFEX source, one normal TWSE production route, selected executor
`phase_i_i2_index_futures_context_executor`, and one default-registry executor route. I1 remains
accepted and active with three sources. A2 used synthetic fixtures only and made
no market-source requests. I2-A3 bounded live acceptance is Owner-accepted `PASS` under
`USER_CHAT_2026-10-01_PHASE_I_I2_A3_OWNER_ACCEPTANCE_AND_MERGE_CLOSURE`, with live evidence recorded in
`docs/governance/phase_i/PHASE_I_I2_A3_BOUNDED_LIVE_ACCEPTANCE_LEDGER_2026-10-01.json` and final merge authorization recorded in
`docs/governance/phase_i/PHASE_I_I2_A3_OWNER_ACCEPTANCE_AND_MERGE_CLOSURE_2026-10-01.json`.
One TAIFEX GET supplied both TWSE:1101 and TWSE:1102, with zero retries and no
TWSE/TPEx requests. Result V3, Audit V3, replay, and citation/artifact lineage
passed; raw payload persistence is NONE. A3 accepted live evidence remains immutable historical proof. I2-A4 production
activation is Owner-accepted under
`USER_CHAT_2026-10-01_PHASE_I_I2_A4_FINAL_PRODUCTION_ACTIVATION_ACCEPTANCE_AND_MERGE_CLOSURE`.
The normal route is approval-gated, TWSE company/common-share only, same-source,
and bounded to at most one TAIFEX acquisition per governed execution. I3-A3 is
Owner-accepted under its separate ledger. I3 production is active and Owner-
accepted under the 2026-10-05 final closure ledger. Phase I is complete under
the final exit review; MCP remains exactly six tools. The earlier
unused I2 live authority is superseded without use.

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
python scripts/validate_phase_i_i1_contracts.py
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
