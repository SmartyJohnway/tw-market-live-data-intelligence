# Governance Index

This directory contains repository governance and accepted gate evidence.

## Current governance front door

The repository-level governance authority is intentionally small:

- [PROJECT.md](../../PROJECT.md) — current project/product truth
- [ROADMAP.md](../../ROADMAP.md) — durable Roadmap V3.2
- [HANDOFF.md](../../HANDOFF.md) — current operational state
- [AGENTS.md](../../AGENTS.md) — repository working rules

## Current runtime governance

Current executable truth is governed by:

- [Capability Catalog V3](../data_capabilities/unified_market_evidence_capability_catalog.v3.json)
- [Routing Matrix V3](../data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json)
- executor registry/configuration
- current implementation and tests

## Phase H accepted governance

Key current/historical Phase H evidence:

- [H-ACT-H1 TPEx attention acceptance](phase_h/PHASE_H_H_ACT_H1_TPEX_ATTENTION_ACCEPTANCE_LEDGER.json)
- [H-ACC-7L selected-product live E2E](phase_h/PHASE_H_H_ACC_7L_SELECTED_PRODUCT_LIVE_E2E_LEDGER.json)
- [H-ACT-V3 promotion preflight](phase_h/PHASE_H_H_ACT_V3_PROMOTION_PREFLIGHT_AND_AUTHORITY_IMPACT_INVENTORY.json)
- [H-ACT-V3 promotion acceptance](phase_h/PHASE_H_H_ACT_V3_PROMOTION_ACCEPTANCE_LEDGER.json)
- [H0-H implementation gate matrix](phase_h/PHASE_H_H0_H_IMPLEMENTATION_GATE_MATRIX.json)

Frozen contracts/manifests under `phase_h/` remain immutable evidence of their
accepted gate. They must not be rewritten merely because the current preferred
runtime later changed.

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
