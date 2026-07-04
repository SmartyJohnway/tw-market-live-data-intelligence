# M6I Test Suite Consolidation and CI Slimming

## Scope and contract alignment

M6I is a targeted test-suite consolidation, not feature development, release hardening, source expansion, or trading functionality. The consolidation preserves the M6H taxonomy and the existing source/data semantics: M5F remains canonical; M5K/M5L remain bounded observation; M5Q remains source health; M5N remains the Conversation Package; observation is not canonical; `reference_only` is not current price; `stale_or_closed_session` remains degraded; strict TLS remains default; compatibility and unsafe TLS remain explicit opt-ins; no silent TLS fallback, trading output, polling, scheduler, startup network, or full-market scan was introduced.

## Counts

- Before direct test count: 673 direct `test_*` functions, using the M6H post-consolidation baseline.
- After direct test count: 630 direct `test_*` functions.
- Net reduction: 43 direct test functions.
- Pytest collected/runtime count after consolidation: 712 collected; 711 selected by `-m "not network"`; 710 passed, 1 skipped, 1 deselected.

## Files changed

- `tests/unit/test_controlled_refresh_staging_validator.py`
- `tests/unit/test_m5b_failure_injection.py`
- `tests/unit/test_build_m5b_staging_candidate.py`
- `tests/unit/test_m5c_staging_promotion.py`
- `tests/test_generate_latest_market_snapshot.py`
- `tests/test_generate_chatgpt_briefing.py`
- `tests/test_generate_ai_context_pack.py`
- `docs/reviews/m6h_test_inventory.csv`
- `docs/reviews/M6I_TEST_SUITE_CONSOLIDATION_AND_CI_SLIMMING.md`

## Helpers added

No shared helper module was added. The safe reduction was achievable with local parametrization and consolidation of repeated static/schema assertions, so adding unused abstraction layers would have been ornamental.

## Tests merged or removed with replacement mapping

| Area | Previous tests | Replacement | Direct-count reduction | Coverage replacement | Why deletion/merge is safe |
|---|---|---|---:|---|---|
| Controlled refresh validator invalid payload mutations | Separate one-line tests for missing fields, forbidden write flags, forbidden trading flag, and disallowed target-universe modes/case variants | `test_invalid_payload_mutations_fail` parameter table | 11 | Every mutation still runs as an individual parametrized pytest case and still asserts validator failure. | Same validator function, same payload fixture, same expected fail-closed outcome. |
| Controlled refresh validator builder error cases | Separate tests for invalid freshness, invalid delay, invalid source id, forbidden nested hold, and realtime guarantee | `test_invalid_payload_builder_cases_record_validation_errors` parameter table | 4 | Each builder case still runs as an individual parametrized pytest case and asserts recorded validation errors. | Same builder path and same forbidden-field/freshness risks. |
| Controlled refresh allowed target-universe cases | Separate bounded/space-padded/None mode tests | `test_allowed_target_universe_cases_pass` parameter table | 2 | Each allowed case remains a separate parametrized case and asserts no errors. | Same validator path and same bounded-only semantics. |
| M5B execution scope guards | Separate source mismatch, target mismatch, duplicate target, wildcard, traversal output, and absolute output tests | `test_execution_scope_rejects_invalid_source_targets_and_output_paths` parameter table | 5 | Each invalid source/target/path case still runs as an individual parametrized pytest case and asserts the exact error code. | Preserves authorization scope and output-path fail-closed coverage. |
| M5B forbidden normalized fields | Separate trading field and realtime guarantee tests | `test_forbidden_normalized_field_guards_fail_contract` parameter table | 1 | Both cases still assert exact error objects and `execution_failed`. | Preserves no-trading and no-realtime-guarantee guards. |
| M5B staging candidate unsafe rows | Separate unauthorized symbol and forbidden recommendation tests | `test_build_staging_candidate_rejects_unsafe_rows` parameter table | 1 | Both cases still raise with the expected failure class. | Preserves bounded targets and no trading semantics. |
| M5B manifest verification | Separate tamper and missing-artifact tests | `test_manifest_verifier_detects_tamper_and_missing_artifact` parameter table | 1 | Both cases still assert exact manifest error codes. | Preserves evidence integrity checks. |
| M5B refinalization | Separate manifest-final-false and malformed-manifest tests | `test_existing_manifest_rejects_refinalization` parameter table | 1 | Both existing-manifest variants still reject refinalization. | Preserves immutable finalized artifact semantics. |
| M5C rollback forbidden roots | Two loop tests for forbidden tmp roots | `test_rollback_rejects_forbidden_tmp_roots` parameter table | 1 | All previously listed forbidden roots remain individual parametrized pytest cases. | Preserves governance path guard behavior with less duplication. |
| Latest market snapshot schemas | Separate top-level, symbol, bid/ask, failed symbol, failed source, and source-health key tests | `test_snapshot_symbol_failure_and_source_health_schema_contracts` | 5 | All required key sets and core bounded-watchlist assertions remain in one schema-contract test. | These were repeated static schema enumerations against the same constructed snapshot/symbol. |
| Latest market snapshot full-market guard | Dedicated watchlist-scope not-full-market test | Covered by `test_snapshot_symbol_failure_and_source_health_schema_contracts` | 1 | The consolidated schema test still asserts `full_market_scan is False`. | Exact same assertion was duplicated. |
| ChatGPT briefing static contract | Separate heading, scope, counts, source authority, freshness, AI boundaries, safe questions, and prohibited-language tests | `test_generated_briefing_static_contract` | 7 | All strings and forbidden safe-question assertions remain in one static markdown contract test. | These were repeated scans over the same rendered briefing. |
| ChatGPT failed tables | Separate failed-source and failed-target table tests | `test_failed_sources_and_targets_table_rendering` | 1 | Both table renderers still assert exact markdown rows. | Same fixture and same rendering risk. |
| ChatGPT raw collection rendering | Separate raw-list and raw-dict tests | `test_no_raw_python_collection_repr` | 1 | Both raw Python collection signatures remain asserted absent. | Same rendered briefing output. |
| AI context pack duplicate failed-observation count | Duplicate direct test name for failed observation count | Later, broader `test_watchlist_observation_summary_preserves_failed_observation_count` retained | 1 | Failed observation count plus observation counts/type/severity/category coverage remain. | Earlier duplicate was strictly subsumed by the broader test. |

## Risks preserved

- M5F canonical validation was not touched.
- Watchlist validation and invalid watchlist fail-closed coverage were not weakened.
- Raw payload leakage guards were not removed.
- No trading semantics remain protected by M5B forbidden field assertions, ChatGPT briefing boundaries, and authoritative scanners.
- Forbidden behavior scanner and governance path guard were not weakened.
- SSL strict/default/env/query precedence, FastAPI invalid `ssl_policy`, and MCP invalid `ssl_policy` tests were not changed.
- M6E operator acceptance tests were not deleted or weakened.
- M6G browser/operator E2E tests and evidence semantics were not deleted or weakened.
- M5K observation semantics, M5Q source-health semantics, and M5N conversation context semantics were not changed.

## Risks intentionally not touched

- No M5F schema tests were consolidated.
- No watchlist fail-closed tests were consolidated.
- No SSL policy precedence matrix tests were consolidated in this PR.
- No FastAPI/MCP invalid `ssl_policy` fail-closed tests were consolidated in this PR.
- No M6E/M6G acceptance or browser evidence tests were removed.
- No source adapter, live observation, or bounded-live behavior was changed.

## Remaining future consolidation candidates

- Broader static frontend contract consolidation using a shared helper if future duplication grows again.
- Report schema key enumeration helpers for repeated artifact report contracts.
- Artifact path allowlist helper for repeated path governance tests.
- A carefully reviewed SSL policy matrix helper, while preserving strict/default/env/query precedence and FastAPI/MCP fail-closed coverage.
- Additional historical milestone static tests that are exact duplicates of stable shared contracts.

## Why no mass deletion occurred

The suite protects several safety-critical boundaries: canonical/observation separation, fail-closed behavior, bounded watchlists, no trading semantics, governance path safety, raw payload leakage, and TLS policy precedence. M6I therefore only merged tests when the exact assertion risk was retained in a parametrized or consolidated replacement. Tests with unique workflow, operator acceptance, browser, source-health, conversation-package, or TLS fail-closed value were intentionally left in place.

## Commit 2 — risk ownership consolidation

Commit 2 shifts M6I from direct function-count consolidation to runtime case-count consolidation. The ownership source for this pass is [`m6i_risk_coverage_matrix.csv`](m6i_risk_coverage_matrix.csv). No product code, source adapter, M5F artifact, observation behavior, source-health behavior, Conversation Package behavior, TLS precedence, M6E coverage, or M6G coverage was changed.

### Commit 2 counts

- Before collected count: 712 collected, 711 selected by `pytest -m "not network" -v`, 710 passed, 1 skipped, 1 deselected.
- After collected count: 670 collected, 669 selected by `pytest -m "not network" -v`, 668 passed, 1 skipped, 1 deselected.
- Net collected reduction: 42 collected pytest cases.
- Before direct function count: 630 direct `test_*` functions.
- After direct function count: 630 direct `test_*` functions.
- Net direct function reduction: 0 direct test functions.

### Files changed in Commit 2

- `docs/reviews/m6i_risk_coverage_matrix.csv`
- `docs/reviews/M6I_TEST_SUITE_CONSOLIDATION_AND_CI_SLIMMING.md`
- `docs/reviews/m6h_test_inventory.csv`
- `tests/unit/test_controlled_refresh_staging_validator.py`
- `tests/unit/test_m5b_failure_injection.py`
- `tests/unit/test_build_m5b_staging_candidate.py`
- `tests/unit/test_m5c_staging_promotion.py`
- `tests/unit/test_m5e_controlled_frontend_publication.py`

### Commit 2 tests retired or consolidated

No file was deleted and no safety-critical owner was demoted behind a marker. Commit 2 retired duplicate runtime cases by replacing parametrized historical breadth with one collected owner-style test that loops over equivalent duplicate cases internally. This preserves assertions while reducing pytest collection overhead.

| removed_or_merged_test | risk_protected | authoritative_replacement | why_safe | coverage_level_preserved |
|---|---|---|---|---|
| `test_invalid_payload_mutations_fail[...]` collected parameter cases | Missing required fields, forbidden write flags, trading flag, and full-market target universe fail closed | `tests/unit/test_validator_regression_matrix.py`; `tests/unit/test_controlled_refresh_staging_writer.py`; looped `test_invalid_payload_mutations_fail` | The same representative mutations still execute inside one collected test, while the risk matrix assigns source allowlist/full-market/forbidden field ownership to stable validator/writer tests. | Unit validator coverage preserved; runtime cases reduced. |
| `test_invalid_payload_builder_cases_record_validation_errors[...]` collected parameter cases | Invalid freshness/delay/source and nested forbidden fields record validation errors | `tests/unit/test_validator_regression_matrix.py`; looped `test_invalid_payload_builder_cases_record_validation_errors` | These were historical breadth cases for the same validation result. Representative cases remain in one collected test. | Unit builder validation coverage preserved; runtime cases reduced. |
| `test_allowed_target_universe_cases_pass[...]` collected parameter cases | Bounded target universe remains allowed and robust to spacing/None mode | `tests/unit/test_controlled_refresh_staging_writer.py`; looped `test_allowed_target_universe_cases_pass` | Bounded-only semantics remain covered by owner tests and all prior cases still execute inside one collected test. | Unit validator coverage preserved; runtime cases reduced. |
| `test_execution_scope_rejects_invalid_source_targets_and_output_paths[...]` collected parameter cases | M5B source/target/output scope fail-closed behavior | `tests/unit/test_m5b_execution_authorization.py`; looped `test_execution_scope_rejects_invalid_source_targets_and_output_paths` | The exact invalid source, target, wildcard, duplicate, traversal, and absolute-path cases still execute under one collected test. | Unit authorization/scope coverage preserved; runtime cases reduced. |
| `test_forbidden_normalized_field_guards_fail_contract[...]` collected parameter cases | M5B no-trading and no-realtime-guarantee normalized field guards | `scripts/forbidden_behavior_scanner.py`; looped `test_forbidden_normalized_field_guards_fail_contract` | The scanner is the authoritative no-trading owner, and both exact row-level regression cases remain in one collected test. | Unit row-guard coverage preserved; runtime cases reduced. |
| `test_build_staging_candidate_rejects_unsafe_rows[...]` collected parameter cases | Staging candidate rejects unauthorized symbol and forbidden recommendation | `tests/unit/test_build_m5b_staging_candidate.py`; `scripts/forbidden_behavior_scanner.py`; looped replacement | Both unsafe row cases still build isolated run dirs and assert the same exceptions. | Unit staging candidate coverage preserved; runtime cases reduced. |
| `test_manifest_verifier_detects_tamper_and_missing_artifact[...]` collected parameter cases | Manifest tamper and missing artifact detection | `tests/unit/test_build_m5b_staging_candidate.py`; looped replacement | Both manifest integrity variants still execute and assert exact error codes. | Unit manifest coverage preserved; runtime cases reduced. |
| `test_existing_manifest_rejects_refinalization[...]` collected parameter cases | Final manifest/refinalization immutability | `tests/unit/test_build_m5b_staging_candidate.py`; looped replacement | Both final-false and malformed-manifest variants still reject refinalization. | Unit immutability coverage preserved; runtime cases reduced. |
| `test_rollback_rejects_forbidden_tmp_roots[...]` collected parameter cases | Governance forbidden roots and path safety | `scripts/governance_forbidden_path_guard.py`; looped `test_rollback_rejects_forbidden_tmp_roots` | The governance guard is authoritative, and all historical M5C forbidden roots still execute inside one collected test. | Unit path coverage preserved; runtime cases reduced. |
| `test_authorization_failures[...]` collected parameter cases | M5E authorization fail-closed variants | `tests/unit/test_m5e_controlled_frontend_publication.py`; looped `test_authorization_failures` | The same wrong hash, destination, action, acknowledgement, and expiry cases still validate under isolated temp dirs. | Unit authorization coverage preserved; runtime cases reduced. |
| `test_crash_recovery_matrix[...]` collected parameter cases | M5E transaction crash recovery states | `tests/unit/test_m5e_controlled_frontend_publication.py`; looped `test_crash_recovery_matrix` | The same six crash phases still execute with isolated case directories and assert the same recovery states. | Unit transaction coverage preserved; runtime cases reduced. |

### Authoritative owners used

- M5F canonical/schema: `tests/unit/test_m5f_canonical_market_context_package.py` and the M5F validator.
- Observation and bounded watchlist: `tests/unit/test_m5k_workflow.py` with M6E/M6G operator confirmation.
- Forbidden trading semantics and raw payload leakage: `scripts/forbidden_behavior_scanner.py` plus targeted surface tests.
- Governance path safety: `scripts/governance_forbidden_path_guard.py` plus focused path regression tests.
- TLS precedence/fail-closed: `tests/unit/test_m6d_ssl_policy.py`, `tests/unit/test_server.py`, `tests/unit/test_m6d_operator_and_local_networking.py`, and M6G.
- M6E/M6G acceptance: `tests/test_m6e_operator_acceptance.py` and `tests/test_m6g_browser_operator_e2e.py`.

### Commit 2 risks intentionally not touched

- M5F canonical validation and schema validation.
- Canonical vs observation separation.
- Watchlist validation and invalid watchlist fail-closed behavior.
- SSL strict/default/env/query precedence.
- FastAPI and MCP invalid `ssl_policy` fail-closed behavior.
- M6E operator acceptance.
- M6G browser/operator E2E and prior bounded-live evidence.
- Source adapter behavior and live observation behavior.
