# Phase L5-A3 — Semantic Projection, Lineage & Derived Output Conformance Hardening

**Authority:** `USER_CHAT_2026-10-20_PHASE_L_L5_A3_SEMANTIC_CONFORMANCE_HARDENING_AUTHORIZATION`  
**Exact base:** `b4b5dac547b0fd0becb5b7a97ac7c158af305147`  
**Base tree:** `d6cdc089086f3939ce1a13ca8f1bb469a6c19113`  
**Branch:** `phase-l/l5-a3-semantic-conformance-hardening`  
**Run:** `l5-a3-20261020T015810Z`

## A1/A2 obligations and inherited deferrals

A1 remains frozen at 36/36 dimensions, zero remaining `DECISION_REQUIRED`, no universal `family_id` registry, and unchanged T1-T12. A2 remains 39 registration surfaces, 30/30 extension surfaces accounted, 9/9 negative controls preserved, and 8/8 friction groups reconciled. A2 deferred exactly `projection`, `audit_projection`, and `handoff` to semantic conformance. A3 accounts for all three, with zero unresolved rows. The four inherited groups closed here are `HARD-schema_loader`, `HARD-lineage`, `HARD-typed_projection`, and `HARD-audit_handoff`.

## Representative families and traces

The run reuses accepted Phase G `material_disclosures` and `monthly_revenue`, Phase H `trading_status_context`, `corporate_action_context`, `recent_performance` (including H4's safety derivation), and Phase I `market_state_context`. No demonstration family was introduced. `semantic_trace_matrix.json` records contract identity, target/operation, source provenance, normalized facts, timing/currentness, coverage/status, lineage, Result, citations, Audit, and handoff data. Trace evidence is acceptance-only and is not a registry.

## Semantic findings and bounded repairs

Fixed-input Phase H projection produced identical Result/Audit outputs on repeat. Result hash, Audit identity, citation-to-target/operation/artifact mapping, and artifact inventory linkage were independently checked. Publication/report dates, observed time, typed retrieval time, bundle finalization (citation retrieval boundary), Result generation, and derived calculation time remain distinct roles. Existing states are preserved; absent binding remains `missing_needs`, while a bound source failure retains the family failure status.

Two bounded repairs restore existing semantics without changing public contracts:

1. In `scripts/m8r_05c/evidence_projector.py`, an absent Phase G binding no longer creates a synthetic `source_failed` typed object, unknown contract, or 1970 timestamp. A present failed binding still follows its existing failure contract.
2. In `scripts/m8r_05c/markdown_renderer.py`, V3 AI-ready Markdown now includes the complete existing typed structures for `market_state_context`, `index_futures_context`, and `cash_institutional_flow_context`; it does not reinterpret them.

No public Request, Result, Audit, or handoff envelope/schema/version/status changed. Mode C remains derived from canonical Result/Audit. The required `CORPORATE_ACTION_COVERAGE_INCOMPLETE` H4 caveat remains visible.

## Acceptance and deferrals

The A3 offline validator and focused mutation tests pass. Phase G research, Phase H V3 typed projection/handoff, and Phase I Result/Audit projection suites pass. All 11 required baseline validators pass. Default-ci remains 1,248 passed / 41 failed / 4 skipped / 5 deselected; the candidate failed-node set exactly equals the accepted historical 41-node set, with zero candidate-only failures. These failures remain unresolved and are not represented as passing.

Publication/Skill-guide redesign and broader publication integration are deferred to unauthorized L5-A4+. No new family/capability/source/executor/route, canonical authority, runtime discovery, plugin framework, public tool, network behavior, or dependency was introduced. Provider requests and live acquisitions were zero; production state mutations were zero; external socket attempts were not measured.

**Technical disposition:** `L5_A3_SEMANTIC_PROJECTION_LINEAGE_CONFORMANCE_HARDENING_PASS`  
**Owner acceptance:** PENDING  
**Stop boundary:** L5-A4+, L6-L7, and Phase M remain unauthorized.
