# Phase J J2 deterministic cross-layer scenario execution

**Disposition: `PHASE_J_J2_HARD_BLOCK_EXISTING_SURFACE_GAP`.** The J2 overlay and validator are internally consistent, but the existing Workbench surface has no browserless seam that executes scenario-specific semantic state/render behavior. The tranche therefore does not claim full cross-layer acceptance. No production surface or public contract was changed to close that gap.

## Authority and scope

J2 began at `230606eb0b51b2004dbeac72f8c2908abe0372d3` (tree `225a964207cc4a9edded1e2928a7cac1ba303d4a`), with `origin/main` at `6daf6e2dcc6fd34e00e7e3831c25e98bb4d2399a`. The accepted J1 review is `5481271339`; Owner authorization SHA-256 is `6657ce311e1d360cf3ab9af6f8f1d4ca78b68cb84d7dfa750cb1254b30ca10a2`.

The accepted J1 registry and matrix were not modified. Their SHA-256 values remain `b26712d1389b904ff003b22aa135caac43ab8f6fc7b32dad571b70438248c864` and `5d07ab2618e6bfa6c79f796df28cd69df5c105fb8f60396c293675737febcd45`. J2 evaluated the authorized 17 scenarios: J1-01, J1-07, J1-08, J1-10, J1-11, J1-12, J1-13, J1-14, J1-16, J1-18, J1-20, J1-22, J1-23, J1-24, J1-25, J1-26, and J1-27.

## What the tests established

Three fixture-backed production paths exercised existing orchestration and produced real Result V3, Audit V3, and handoff artifacts for J1-11, J1-20, and J1-23. The Local Service routes and actual MCP `market_read_result` / `market_export_ai_handoff` handlers read the same control package and preserved its result identity without another execution. J1-10 exercised actual pre-execution refusal in Local Service and MCP input validation; it did not create a successful control package.

The tests also fetched the Workbench page and its JavaScript asset. That only proves the page is served; it does not prove Workbench rendered each scenario’s semantic state. The repository has no existing browserless Workbench interaction seam, and J2 was not authorized to add a browser dependency or production backdoor. Workbench scenario coverage therefore remains planned for all 27 rows. Thirteen target scenarios are classified `EXISTING_SURFACE_GAP`; the four with exercised service/MCP behavior still lack Workbench semantic acceptance. The effective outcome is a hard block, not a pass.

The execution ledger records all 17 adjudications, the exact test node IDs, fixture references, package/result/audit/handoff identity, blocked layers, and zero network dispatches. J1-25’s existing isolated fresh-install assertion was revalidated; no fresh-install coverage cell was promoted. The seven previously accepted integration claims remain unchanged.

## Coverage overlay

The additive J2 delta promotes eight cells from `PLANNED` to `COVERED_EXISTING`: `service_api` and `mcp` for J1-10, J1-11, J1-20, and J1-23. No integration, Workbench, or fresh-install cells were promoted. The baseline matrix remains the historical J1 close record; the effective candidate is mechanically derived by applying the J2 delta.

| Layer | J1 baseline | J2 effective candidate |
|---|---:|---:|
| Integration | 7 covered, 20 planned | 7 covered, 20 planned |
| Service API | 27 planned | 4 covered, 23 planned |
| Workbench | 27 planned | 27 planned |
| MCP | 27 planned | 4 covered, 23 planned |
| Fresh install | 1 covered, 26 planned | 1 covered, 26 planned |
| Bounded live | 8 historical covered, 16 require authorization, 3 N/A | unchanged |
| Real agent | 27 require authorization | unchanged |

Across all 243 scenario-layer cells, the baseline has 16 `COVERED_EXISTING`, 34 `COVERED_J0_J1`, 147 `PLANNED`, 16 `REQUIRES_LIVE_AUTH`, 27 `REQUIRES_REAL_AGENT_AUTH`, 3 `NOT_APPLICABLE`, 0 `EXPECTED_FAIL_CLOSED`, and 0 `BLOCKED`. The effective candidate has 24, 34, 139, 16, 27, 3, 0, and 0 respectively. No status or layer was added.

The coverage delta is [PHASE_J_J2_DETERMINISTIC_CROSS_LAYER_COVERAGE_DELTA_V1.json](PHASE_J_J2_DETERMINISTIC_CROSS_LAYER_COVERAGE_DELTA_V1.json), SHA-256 `03160d7103f6f28944903f6982ecab5ee5709516e9dbc51d5d98614987fe0fdc`. The derived matrix candidate is [PHASE_J_J2_EFFECTIVE_COVERAGE_MATRIX_V1.json](PHASE_J_J2_EFFECTIVE_COVERAGE_MATRIX_V1.json), SHA-256 `252fb9b36fe7920f51ffde763a51565b3d4a8170ed297c6b564edd161ff55982`. The execution ledger is [PHASE_J_J2_DETERMINISTIC_CROSS_LAYER_EXECUTION_LEDGER_V1.json](PHASE_J_J2_DETERMINISTIC_CROSS_LAYER_EXECUTION_LEDGER_V1.json), SHA-256 `6b32f88e9f659d54f0d1b07a1b7c048ab78205ae0a65eb4aae04595a26993cc0`.

## Validation

Focused J2, J1 registry, and J1-25 fresh-install tests passed: 20 passed. The affected J2/Workbench/Mode C regression batch passed 35 tests, skipped 1, and narrowly deselected two historical V1 Mode C tamper assertions whose generated outputs are absent from the clean baseline. Their exact node IDs and reason are recorded in the JSON.

The J2 overlay validator passed structural checks and reported the terminal surface-gap disposition. J1 registry, J-B03 closure, exact-historical-head J-B04 A6-R2, A6 terminal, A6-R1, Phase I final closure, and Phase H V3 validators passed. `compileall`, strict duplicate-key JSON validation, and `git diff --check` passed.

Clean-archive `default-ci` used CPython 3.12.14, the same dependency environment and isolated Security Master root, `TZ=Etc/UTC`, `PYTHONHASHSEED=0`, and network denial. Base and candidate each collected 1,288, passed 1,278, failed 2, skipped 3, and deselected 5. The same pre-existing failures occurred on both: `test_api_reuses_one_successful_process_activation` and `test_current_portable_catalog_is_exact_generated_v3_projection`. Candidate-only failure nodes: 0.

## Boundaries and state

Market/source GET, HEAD, and POST were all zero. Browser and Firecrawl use, Security Master acquisition/mutation, bounded-live execution, and real-agent execution were all zero. The host ACTIVE selector remained at SHA-256 `25b24e55b188fc2fa08efbe227d98c5890b31f179168665bab8f1f413a55f0fc`. Production runtime files, public schemas, routes, and capabilities changed by zero; MCP remains six tools.

Phase J remains `STARTED`; J0 is `COMPLETE`; J1 remains the independently accepted baseline; J2 is a frozen hard-blocked candidate pending independent review. J-B01/J-B02 remain non-blocking, J-B03/J-B04 remain closed, bounded-live and real-agent authorization remain `NOT_GRANTED`, and Phase K remains `NOT_STARTED`. PR #326 remains open, Draft, and unmerged.
