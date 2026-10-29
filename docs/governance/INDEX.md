# Governance Index

This directory contains accepted governance, frozen contracts, closure records,
and audit evidence. This page is navigation for **current governance state**;
individual dated records retain the truth of their own gate and are not rewritten
merely because later phases closed.

## Current governance state

As of 2026-10-28:

```text
Stable product                 v1.5.0
Frozen source commit           acaf726a5b59baee4c5a30521ea5a5d5ec0cec76
Frozen source tree             d44f66dc154c21326ac8b105d2f15fd793f6071b
Phase I                        COMPLETE
Phase J                        COMPLETE
Phase K                        COMPLETE
Phase L                        CLOSED
L7 canonical exits             29 / 29 PASS
GitHub v1.5.0 publication      PASS
Phase M                        NOT_AUTHORIZED
```

Phase L final closure and A7 publication occurred after the frozen v1.5.0 source
was established, so post-release current docs reconcile those accepted facts
without modifying the frozen release commit/tree. The Post-Phase-L frontdoor
maintenance tranche was subsequently merged through PR #423 to `main` at
`b86ae52a2f43f53fd854e9d84cfde1c80050dcc9`.

The current authorized post-release workstream is **Post-v1.5 Productization &
Stabilization**. Only **P0 — Current-state Reconciliation** is active here; P1–P5
remain planned follow-on tranches and Phase M remains NOT_AUTHORIZED.

See the Post-Phase-L F0 record:

- [Post-Phase-L F0 Frontdoor Information Architecture](post_phase_l/POST_PHASE_L_F0_FRONTDOOR_INFORMATION_ARCHITECTURE_2026-10-28.md)

## Repository governance front doors

- [PROJECT.md](../../PROJECT.md) — current project/product authority
- [HANDOFF.md](../../HANDOFF.md) — current operational stopping point
- [ROADMAP.md](../../ROADMAP.md) — durable Roadmap V3.2 scope
- [AGENTS.md](../../AGENTS.md) — repository / AI working rules
- [Documentation Index](../INDEX.md) — user/developer navigation

## Major governance areas

### Phase H

Accepted interpretation/runtime evidence is under [`phase_h/`](phase_h/),
including H1/H3 bounded route activation, selected-product live E2E, and V3
promotion. Frozen records remain historical authority for their exact gate.

### Phase I

Accepted I1/I2/I3 source contracts, bounded-live evidence, production activation,
exit review and closure are under [`phase_i/`](phase_i/). Phase I is complete;
current executability still comes from current Catalog / Routing / executor truth.

### Phase J

Integrated research acceptance and final closure are under
[`phase_j/`](phase_j/). Historical harness/tool-policy limitations remain evidence;
they do not automatically become current product defects.

### Phase K

Multi-agent compatibility governance and host-evaluation closure are under
[`phase_k/`](phase_k/). Phase K completed with two native host passes, one bounded
host limitation and zero product compatibility defects.

### Phase L

Production hardening / release governance is under [`phase_l/`](phase_l/).
L0 was frozen; L1-L7 ultimately closed. L7 culminated in exact-source
recertification, stable source/artifact freeze, GitHub v1.5.0 publication and
Owner final Phase L closure.

Phase M is not started and remains **NOT_AUTHORIZED**.

## Post-Phase-L documentation governance

The completed Post-Phase-L documentation-maintenance tranche is tracked under
[`post_phase_l/`](post_phase_l/). Its purpose was to reconcile public/user/engineering
frontdoors after the frozen v1.5.0 release without changing runtime behavior,
release assets, Registry metadata, or Phase M authority.

- [F0 frontdoor information architecture](post_phase_l/POST_PHASE_L_F0_FRONTDOOR_INFORMATION_ARCHITECTURE_2026-10-28.md)
- [F5 documentation-only validation](post_phase_l/POST_PHASE_L_F5_DOCUMENTATION_ONLY_VALIDATION_2026-10-28.md)
- [F5-R1 independent-review corrections](post_phase_l/POST_PHASE_L_F5_R1_INDEPENDENT_REVIEW_CORRECTIONS_2026-10-28.md)

The pre-F3 versions of the seven engineering-frontdoor files were preserved
byte-for-byte before consolidation. See:

- [`../archive/frontdoor/2026-10-28-pre-f3/`](../archive/frontdoor/2026-10-28-pre-f3/)

## Governance policy

- [Governance policy manifest](governance_policy_manifest.json)
- [Workflow policy matrix](workflow_policy_matrix.json)

Use four documentation classes:

1. **CURRENT** — current product/runtime/navigation.
2. **FROZEN CONTRACT** — accepted contract/gate authority.
3. **HISTORICAL EVIDENCE** — earlier milestone truth.
4. **ARCHIVE** — superseded navigation/planning material retained for history.

A historical statement is not a current-status bug unless the document is still
presented as a current authority. Never mass-rewrite historical ledgers to make
them match a later state.
