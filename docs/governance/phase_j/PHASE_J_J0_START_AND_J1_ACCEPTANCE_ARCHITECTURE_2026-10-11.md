# Phase J J0 start and J1 acceptance architecture

**Disposition:** `PHASE_J_J0_J1_GOVERNED_SCENARIO_REGISTRY_AND_COVERAGE_MATRIX_PASS`

Phase J is now **STARTED** under entry review `5479545125` and the Owner start authorization SHA-256 `46cb965043659cbc82eced142b3d7c12eef119b4942124513fabb6305e894198`. J0 is complete. The J1 scenario registry and coverage matrix are frozen acceptance candidates for exact-head independent review; Phase J is not complete.

## Authority and state reconciliation

The authorized starting authority was HEAD `2455fd0875bc09d6bc5926a6267351aadb38beb1`, tree `1c42fd165bbbbd32249b9a43fc2b813182b31ca3`, and `origin/main` `6daf6e2dcc6fd34e00e7e3831c25e98bb4d2399a`. PR #326 remains open, Draft, and unmerged. J-B04 closure review `5479527453` cleared J-B04 after A6-R2; J-B03 is closed; J-B01 and J-B02 remain non-blocking.

The 2026-10-05 readiness preflight remains immutable. Its 27 `J1-xx` IDs, scenario meaning, and product relevance classes were inherited exactly. Its `Phase J NOT_STARTED` and J-B03/J-B04 blocker fields describe the earlier point in time. Current readiness is recorded separately in the registry using Phase I closure, J-B03 closure, J-B04/A6-R2 evidence, and the exact-head start review.

## Registry and matrix

- Registry: [`PHASE_J_J0_J1_GOVERNED_SCENARIO_REGISTRY_V1.json`](PHASE_J_J0_J1_GOVERNED_SCENARIO_REGISTRY_V1.json), SHA-256 `279f9bca5f3e1373315f8bfa297dae6fbb55586e8e0737d0a06bb0febb69cedd`.
- Coverage matrix: [`PHASE_J_J0_J1_COVERAGE_MATRIX_V1.json`](PHASE_J_J0_J1_COVERAGE_MATRIX_V1.json), SHA-256 `34df5972122421ec6b7a90e0281928f4f516122cce2709db478058bb7489ace8`.
- Both contain 27 scenarios with identical stable IDs. All 27 trace to Roadmap J.1 and the historical readiness source.
- Product relevance counts: 16 `MUST_HAVE_FOR_CONVERSATIONAL_J`, 1 `ACCEPTANCE_HARNESS_ONLY`, 5 `OPTIONAL_EVIDENCE_NOT_J_BLOCKING`, and 5 `SAFE_FAIL_CLOSED_IS_SUFFICIENT`.
- Layer-cell counts: 37 `COVERED_EXISTING`, 34 `COVERED_J0_J1`, 127 `PLANNED`, 15 `REQUIRES_LIVE_AUTH`, 27 `REQUIRES_REAL_AGENT_AUTH`, and 3 `NOT_APPLICABLE`.
- Seventeen scenarios have new synthetic contract-fixture and deterministic-unit coverage; all 27 have inherited network-free integration evidence. Nine have matching historical bounded-live evidence. Fifteen need future live authorization. All 27 real-agent cells need separate authorization.
- Service API, Workbench, and MCP scenario-specific cross-layer runs remain planned. Existing layer baselines bind service validate/preview/authorize/execute/result/audit/handoff, Workbench projection, six MCP tools, and isolated fresh-install fail-closed behavior to concrete tests.

The synthetic fixtures are explicitly network-free acceptance projections. They are not market-source payloads or live captures. They exercise normal success, no-evidence, unresolved correction linkage, unsupported financial statements, bounded/partial H1 status, uncovered suspension/resumption, H2 subtype limits, H4 blocked interpretation, optional Phase I context, partial result, missing, source failure, identity ambiguity, unsupported identity, authorization refusal, resource bounds, Result/Audit identity binding, citations/lineage, and forbidden handoff claims.

## Golden semantics and product boundary

Acceptance is semantic, not golden prose. It checks identity, source, period, timing/currentness, missing/partial/failure distinction, coverage, authorization, resource bounds, citations/lineage, interpretation guards, and no-trading boundaries. It preserves that execution success does not imply permission to interpret an ordinary return. H3 owns its actual comparison window. Phase-I context remains explicitly requested and descriptive. Unsupported financial statements and unproven disclosure corrections remain fail-closed. H1 and H2 gaps remain explicit; no full-family coverage is claimed.

Request, Result, and Audit remain V3. MCP remains exactly six tools. Production runtime, public schemas, sources, routes, Security Master, and product capabilities were not changed. No market/source request, Security Master acquisition, browser, or real-agent execution occurred. The Roadmap Phase J checkbox remains unchecked because `STARTED` is not `COMPLETED`.

## Validation

The registry validator passed, as did J0/J1 focused tests (17 fixture cases; 7 tests), the readiness, J-B03, J-B04/A6-R2, A6 historical terminal, A6-R1, Phase I, and Phase H V3 validators, compileall, strict duplicate-key JSON scan (1,066 files), and `git diff --check`.

Two assertions in the older A6-P1 prerequisite test still expect H2 to be inactive. They fail against the current independently reviewed A6-R2 bounded H2 activation. Those frozen historical assertions were not edited; their historical validators pass. The focused cross-layer run was repeated with only those two outdated assertions deselected: 313 passed, 1 skipped.

Clean-clone default-CI used the same CPython 3.12.14 environment, dependency set, UTC timezone, hash seed, external-network deny guard, and empty isolated Security Master state for both exact commits. Base and candidate each collected 1,288 tests: 1,249 passed, 30 failed, 4 skipped, 5 deselected. Failed-node sets were equal; candidate-only failures = 0.

The implementation commit is `08ddd9f835a0470829d99898888ef18852d567f7` (tree `c81998d07b8fe4b13124ff95a7aac10940b8cea8`). Only acceptance/governance files were added; no production changes followed validation. The evidence commit ID is reported in the publication summary to avoid self-reference.

## Next step recommendation

Recommendation only: J2 can execute deterministic cross-layer scenarios across the selected existing Service, Workbench, MCP, and fresh-install layers. J3 and J4 should select bounded-live and real-agent cases only after separate Owner authorizations. No such execution or Phase K start is part of this tranche.
