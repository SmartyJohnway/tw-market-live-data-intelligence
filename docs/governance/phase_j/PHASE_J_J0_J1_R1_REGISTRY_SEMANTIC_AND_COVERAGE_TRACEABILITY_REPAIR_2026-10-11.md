# Phase J J0/J1-R1 Registry Semantic and Coverage Traceability Repair

**Disposition:** `PHASE_J_J0_J1_R1_REGISTRY_SEMANTIC_AND_COVERAGE_TRACEABILITY_REPAIR_PASS`

## Authority and scope

R1 started from HEAD `26cbe87dc73aab1fdff15bdad9efb828e0b9ca57`, tree `0f08c5cc7478b904fa3084c17373a2c5224c0a24`, and `origin/main` `6daf6e2dcc6fd34e00e7e3831c25e98bb4d2399a`. PR #326 remained open, Draft, and unmerged. Independent review `5480046031` held the J1 candidate for a network-free repair. The Owner authorization SHA-256 is `fc89876349d947e51747a5369e06fa5c074e527f3a6a8e3a1d698b9ae3f72045`.

Phase J remains **STARTED**, J0 remains **COMPLETE**, and the J1 registry and matrix remain R1 frozen-acceptance candidates pending independent review. J-B01 and J-B02 remain non-blocking; J-B03 remains closed; J-B04 remains closed/cleared; Phase K remains not started.

The repair changed only the governed registry, coverage matrix, their network-free validator, and registry tests. Production runtime, public V3 contracts, capability routes, Security Master, and MCP tools were not changed. The exact six MCP tools remain in place.

## Current and historical scenario meaning

Every scenario now separates its current `purpose`/`current_purpose` and structured `current_semantic_state` from `historical_readiness_summary`. Historical summaries retain both the prior readiness-preflight reason and the prior candidate purpose, sourced to `PHASE_J_GHI_INTEGRATED_READINESS_PREFLIGHT_2026-10-05.json`.

J1-11 now reflects the accepted representative TPEx H1 composite route for attention and disposition while preserving the uncovered changed-trading-method, suspension, and resumption families. J1-12 remains unsupported for suspension/resumption. J1-14 explicitly records the bounded `phase_h_h2_twse_exright_pre_executor` route using TWSE `TWT48U_ALL`; it does not claim complete corporate-action coverage. J1-13 and J1-15 remain unsupported subtype cases, and J1-16 preserves the H4 incomplete-coverage interpretation guard. I2 remains optional and explicitly requested.

The validator checks structured readiness/capability state, accepted route scope, uncovered families, full-family claims, and interpretation guards. It also verifies the historical preflight meaning remains present and separate.

## Authority binding

The previous J1-11/J1-12 superseding references incorrectly labeled J-B04 review `5479527453` as the J-B03 review. R1 binds those scenarios to the canonical J-B03 C0 closure governance record, which records decision `J_B03_CLOSED_BOUNDED_CONVERSATIONAL_CORRECTNESS_SATISFIED` and the bounded H1 composite executor. No distinct GitHub J-B03 review ID is recorded, so none is asserted.

J1-13 through J1-16 continue to bind to the J-B04 A6-R2 governance record and review `5479527453`. The validator enforces gate-role correctness and checks the referenced J-B03 closure content.

## Integration coverage traceability

Before R1, all 27 scenario-level integration cells were marked `COVERED_EXISTING`. R1 retained seven claims with scenario-specific integration or accepted E2E evidence and downgraded twenty unsupported claims to `PLANNED`.

Retained integration scenarios are J1-03 (multi-target mixed outcomes), J1-11 (representative H1 composite attention/disposition), J1-16 (H4 coverage-incomplete guard), J1-17 (accepted 20-day H3 TWSE execution), J1-18 (explicit TAIFEX context through the governed I2 runner), J1-20 (partial result through Result/Audit/handoff), and J1-23 (source failure through Result/Audit/handoff).

Each retained integration cell has a typed evidence reference and a scenario-match note. Catalogs, routing matrices, contracts, unit tests, and generic closure prose cannot qualify an integration cell by themselves. The global service API, Workbench, MCP, fresh-install, and integration baselines remain explicitly separate from scenario-level coverage. The matrix validator also requires layer-appropriate evidence kinds for every covered cell.

Updated aggregate matrix counts are:

- `COVERED_EXISTING`: 16
- `COVERED_J0_J1`: 34
- `PLANNED`: 147
- `REQUIRES_LIVE_AUTH`: 16
- `REQUIRES_REAL_AGENT_AUTH`: 27
- `NOT_APPLICABLE`: 3

The integration layer has 7 `COVERED_EXISTING` and 20 `PLANNED` scenario cells. The 27 inherited scenario IDs and four relevance classes are unchanged.

## Validation

The registry validator passed. The focused network-denied J0/J1 and adjacent acceptance suites reported 262 passed, 0 failed, 1 skipped, with only the two exact obsolete A6-P1 historical assertions deselected: `test_h2_remains_plan_only_inactive_and_unselected` and `test_inventory_and_authority_helpers_are_network_free`. The dedicated registry suite reported 15 passed.

Historical readiness, J-B03 closure, A6 terminal evidence, A6-R1, Phase I final-exit, and Phase H V3 validators passed. The A6-R2 terminal validator passed at its exact historical evidence commit `2455fd0875bc09d6bc5926a6267351aadb38beb1`, using the preserved local session and runtime artifacts; historical evidence was not rewritten.

Clean-archive default-CI compared base `26cbe87dc73aab1fdff15bdad9efb828e0b9ca57` with implementation candidate `e0c47d441cf5bb2cd0eb2dbf20fd12c6ba6df70e`, under the same CPython 3.12.14 environment, `TZ=Etc/UTC`, `PYTHONHASHSEED=0`, network denial, and isolated Security Master root. Both runs collected 1,288 tests: 1,249 passed, 30 failed, 4 skipped, 5 deselected. The 30 failed node IDs were identical; candidate-only failures were zero. The reports are retained locally at `/tmp/phase-j-j0j1-r1-base-default-ci.json` and `/tmp/phase-j-j0j1-r1-candidate-default-ci.json`.

Compileall and `git diff --check` passed. A strict duplicate-key JSON scan is recorded in the accompanying machine-readable evidence.

## Activity and boundaries

Market/source requests were GET/HEAD/POST `0/0/0`. Security Master acquisition and mutation were zero. Browser and Firecrawl use were zero. No bounded-live or real-agent scenario was executed. Bounded-live and real-agent authorizations remain `NOT_GRANTED`.

## Implementation boundary

The implementation commit is `e0c47d441cf5bb2cd0eb2dbf20fd12c6ba6df70e`, tree `8c4314fb460ad628828b32d96b592335981fee85`, subject `fix(phase-j): repair scenario semantics and coverage traceability`. No production files changed after validation. This R1 evidence is additive; prior readiness, J-B03/J-B04, A6, A6-R1, A6-R2, Phase I, and Phase J start records remain unchanged.
