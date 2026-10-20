# Phase L5-A2-R1 — Canonical Front-Door Status Reconciliation (2026-10-19)

## Authority and preserved A2 candidate

This R1 is a governance/current-state metadata repair authorized under `USER_CHAT_2026-10-20_PHASE_L_L5_A2_R1_CANONICAL_FRONT_DOOR_STATUS_RECONCILIATION_AUTHORIZATION`.

- A2 candidate: `193ca05261e002eac01c477931d07015d66acd1e`
- A2 tree: `311601d879e87fa1c2bb3d1622ade9f0ac7faab0`
- A2 disposition: `L5_A2_EXPLICIT_REGISTRATION_CONFORMANCE_HARDENING_PASS`
- Original A2 manifest: `b1dd1c009426e9470180e9962430284062538228e8ef940c6d2a71481c48bfea` (24 artifacts)

The original A2 evidence, including its `frontdoor_status_reconciliation.json`, remains unchanged. R1 independently verified all 24 manifest members against the A2 candidate commit and recomputed the original manifest canonical SHA-256 without modification.

## Reconciliation

The original A2 front-door reconciliation classified two later rollups as historical. Independent review determined those two rollups still function as current/recovery authority. R1 corrects only that metadata classification and current-state text in `ROADMAP.md` and `docs/governance/phase_l/PHASE_L_CURRENT_STATUS_AND_RECOVERY_INDEX_2026-10-14.md`.

The corrected state says L5-A2 technical conformance hardening is complete with Owner acceptance pending, while L5-A3+ and L6-L7 remain unauthorized. The other two canonical front doors already stated the correct current status and were not changed.

A2 validator changed = NO. A2 test semantics changed = NO. Registration reconciliation changed = NO. A1 contract changed = NO. Runtime/product changes = NO.

## Result and boundary

The post-edit scan finds zero live/recovery A2-not-authorized rollups and zero current-state contradictions. The two targeted current/recovery rollups are the only changed existing files. `git diff --check` passes. No technical validators, default-ci, or focused tests were rerun because this tranche changes only current-state metadata.

R1 disposition: `L5_A2_FRONT_DOOR_STATUS_RECONCILIATION_PASS`.

Primary A2 disposition remains `L5_A2_EXPLICIT_REGISTRATION_CONFORMANCE_HARDENING_PASS`. This does not accept A2 on the Owner's behalf and does not authorize L5-A3.
