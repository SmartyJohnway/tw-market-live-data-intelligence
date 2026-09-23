# TG-1 Test Authority & Historical Evidence Disposition Ledger

Baseline main: `b42c73057a16ea39d73ed7efd8c96096ee49e131`

> **Proposal only.** TG-1 changes no test profile, production runtime, source activation, frozen schema, or Phase I implementation.

## Summary

- default-CI files reviewed: **156**
- pending manual review: **0** (fail-safe rules keep unproven removals in default CI)

### Proposed dispositions

| Disposition | Files |
|---|---:|
| `KEEP_DEFAULT_COMPATIBILITY` | 38 |
| `KEEP_DEFAULT_CONTRACT` | 4 |
| `KEEP_DEFAULT_CURRENT` | 45 |
| `KEEP_DEFAULT_REWRITE_BRITTLE` | 4 |
| `MOVE_FULL_CURRENT_NONDEFAULT` | 45 |
| `MOVE_HISTORICAL_AFTER_TG3` | 16 |
| `MOVE_RELEASE_PRECHECK` | 2 |
| `SPLIT_MIXED_CURRENT_HISTORICAL` | 2 |

### Proposed target profiles

| Target | Files |
|---|---:|
| `default-ci-current + historical-acceptance` | 2 |
| `default-ci-current` | 91 |
| `full-current-non-network` | 45 |
| `historical-acceptance` | 16 |
| `release-preflight` | 2 |

## Interpretation

- `KEEP_*`: retain every-PR protection; some assertions still need cleanup.
- `MOVE_FULL_CURRENT_NONDEFAULT`: keep in broad deterministic regression, but propose removing superseded surfaces from every-PR authority only after shadow CI.
- `MOVE_HISTORICAL_AFTER_TG3`: blocked until immutable historical integrity/reproduction protection exists.
- `SPLIT_MIXED_CURRENT_HISTORICAL`: split before any profile change.
- No disposition authorizes deleting a test.

## High-risk reviewed examples

- `test_m8_through_m8b_consolidated_acceptance.py`: historical acceptance currently locks old `next_task`, README and docs-index content; move only after TG-3.
- `test_validate_v1_public_contracts.py`: keep release truth in default CI, but replace prose regex with structured authority.
- `test_phase_g_pr_d_closure.py`: split immutable historical closure checks from current V3 authority checks.
- `test_phase_h_imp_7d_deterministic_e2e.py`: keep default; it still protects the current V3 chain despite milestone naming.
- `test_m8r_06_04_mode_c.py`: split historical-marked cases from current Mode C regressions.

## Per-file proposal

| Test file | Disposition | Target | Preconditions |
|---|---|---|---|
| `tests/unit/test_m8r_03e_r2_filesystem_containment.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/unit/test_m8r_filesystem_containment.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/unit/test_m5k_workflow.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_m5n_watchlist_workflow.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_m6d_ssl_policy.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_server.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_mcp_server.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_governance_forbidden_path_guard.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/unit/test_forbidden_behavior_scanner.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/unit/test_no_frontend_public_write_guard.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/unit/test_no_trading_signal_ui_guard.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/unit/test_m6d_operator_and_local_networking.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_run_test_profile.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/unit/test_m5f_canonical_market_context_package.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_m5fgh_consumer_consistency.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_m5fgh_fastapi_context.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_m5fgh_frontend_static.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_m5i_explicit_bounded_refresh.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_m5ij_forbidden_path_policy.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/unit/test_m5op_frontend_operator_workflow.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_m6a_observation_ux.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_m6b_contract_hardening.py` | `KEEP_DEFAULT_CONTRACT` | `default-ci-current` | none |
| `tests/test_m5q_source_health.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/test_m6e_operator_acceptance.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_frontend_readonly_static_contracts.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_frontend_readonly_contract_static.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_frontend_readonly_context_package.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_frontend_accessibility_static.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_frontend_observability_static.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_twse_mis_normalization_v2.py` | `KEEP_DEFAULT_COMPATIBILITY` | `default-ci-current` | none |
| `tests/unit/test_twse_openapi_normalization_v1.py` | `KEEP_DEFAULT_COMPATIBILITY` | `default-ci-current` | none |
| `tests/unit/test_tpex_openapi_normalization_v1.py` | `KEEP_DEFAULT_COMPATIBILITY` | `default-ci-current` | none |
| `tests/unit/test_yahoo_normalized_chart_v1.py` | `KEEP_DEFAULT_COMPATIBILITY` | `default-ci-current` | none |
| `tests/unit/test_source_contract_schema.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/unit/test_source_authority_registry.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/unit/test_source_family_coverage_matrix.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/unit/test_m7e_market_clock_session_state_schema.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/unit/test_m7e_market_clock_session_state_builder.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/unit/test_m7e_twse_holiday_schedule_classifier.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/unit/test_m7e_market_clock_session_state_controlled_promotion.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/unit/test_m7e_market_clock_session_state_context_integration.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/unit/test_m7e_market_clock_session_state_markdown.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/unit/test_m7e_market_clock_session_state_inventory.py` | `KEEP_DEFAULT_REWRITE_BRITTLE` | `default-ci-current` | replacement assertion before brittle assertion removal |
| `tests/unit/test_m7e_market_clock_session_state_final_acceptance.py` | `MOVE_HISTORICAL_AFTER_TG3` | `historical-acceptance` | TG-3 historical integrity; TG-4 shadow CI |
| `tests/unit/test_m7e_twse_trading_calendar_authority.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/unit/test_m7e_twse_trading_calendar_artifact.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/unit/test_m7e_twse_trading_calendar_mode_contract.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/unit/test_m7f_rich_fact_browser_policy.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_m7f_rich_fact_display_catalog.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_m7f_ai_handoff_search_filters.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_m7f_field_badges_currentness_calendar.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_m7f_frontend_rich_fact_browser_base_ui.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_m7f_frontend_security_semantic_regression.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_m7f_rich_fact_browser_final_acceptance.py` | `MOVE_HISTORICAL_AFTER_TG3` | `historical-acceptance` | TG-3 historical integrity; TG-4 shadow CI |
| `tests/unit/test_m7g_safe_context_artifact_schema.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_m7g_safe_artifact_validator.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_m7g_frontend_manual_artifact_load_ui.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_m7g_inventory_policy.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_m7g_real_safe_artifact_rendering.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_m7g_provenance_currentness_source_health_panel.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_m7g_ai_handoff_from_loaded_safe_artifact.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_m7g_refresh_workflow_policy_request_package.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_m7g_refresh_request_package_builder.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_m7g_controlled_refresh_execution_gate.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_m7g_refreshed_safe_artifact_result_contract.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_m7g_controlled_refresh_frontend_execution_ui.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_m7g_refresh_workflow_security_regression.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_m7g_twse_mis_market_route_semantics.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_m7g_final_acceptance.py` | `MOVE_HISTORICAL_AFTER_TG3` | `historical-acceptance` | TG-3 historical integrity; TG-4 shadow CI |
| `tests/unit/test_m8_source_governance_foundation.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_m8_source_freshness_evaluator.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_m8_multi_source_context_builder.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_m8_controlled_conversation_context_integration.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_m8_compatibility_hardening.py` | `MOVE_FULL_CURRENT_NONDEFAULT` | `full-current-non-network` | confirm no unique current safety gap; TG-4 shadow CI |
| `tests/unit/test_m8_00_final_acceptance.py` | `MOVE_HISTORICAL_AFTER_TG3` | `historical-acceptance` | TG-3 historical integrity; TG-4 shadow CI |
| `tests/unit/test_m8a_official_eod_contract_preflight.py` | `MOVE_HISTORICAL_AFTER_TG3` | `historical-acceptance` | TG-3 historical integrity; TG-4 shadow CI |
| `tests/unit/test_m8a_official_eod_observation.py` | `KEEP_DEFAULT_COMPATIBILITY` | `default-ci-current` | none |
| `tests/unit/test_m8a_twse_official_eod_adapter.py` | `KEEP_DEFAULT_COMPATIBILITY` | `default-ci-current` | none |
| `tests/unit/test_m8a_tpex_official_eod_adapter.py` | `KEEP_DEFAULT_COMPATIBILITY` | `default-ci-current` | none |
| `tests/unit/test_m8a_official_eod_instrument_classification.py` | `KEEP_DEFAULT_COMPATIBILITY` | `default-ci-current` | none |
| `tests/unit/test_m8a_official_eod_failure_contract.py` | `KEEP_DEFAULT_COMPATIBILITY` | `default-ci-current` | none |
| `tests/unit/test_m8a_ncdr_dgpa_closure_cap.py` | `KEEP_DEFAULT_COMPATIBILITY` | `default-ci-current` | none |
| `tests/unit/test_m8a_market_day_currentness_resolver.py` | `KEEP_DEFAULT_COMPATIBILITY` | `default-ci-current` | none |
| `tests/unit/test_m8a_controlled_official_eod_execution.py` | `KEEP_DEFAULT_COMPATIBILITY` | `default-ci-current` | none |
| `tests/unit/test_m8a_official_eod_context_integration.py` | `KEEP_DEFAULT_COMPATIBILITY` | `default-ci-current` | none |
| `tests/unit/test_m8a_official_eod_conversation_projection.py` | `KEEP_DEFAULT_COMPATIBILITY` | `default-ci-current` | none |
| `tests/unit/test_m8a_final_acceptance.py` | `MOVE_HISTORICAL_AFTER_TG3` | `historical-acceptance` | TG-3 historical integrity; TG-4 shadow CI |
| `tests/unit/test_m8b_taifex_openapi_contract_preflight.py` | `MOVE_HISTORICAL_AFTER_TG3` | `historical-acceptance` | TG-3 historical integrity; TG-4 shadow CI |
| `tests/unit/test_m8b_taifex_derivatives_observation.py` | `KEEP_DEFAULT_COMPATIBILITY` | `default-ci-current` | none |
| `tests/unit/test_m8b_taifex_openapi_futures_adapter.py` | `KEEP_DEFAULT_COMPATIBILITY` | `default-ci-current` | none |
| `tests/unit/test_m8b_taifex_openapi_options_adapter.py` | `KEEP_DEFAULT_COMPATIBILITY` | `default-ci-current` | none |
| `tests/unit/test_m8b_taifex_openapi_final_settlement_adapter.py` | `KEEP_DEFAULT_COMPATIBILITY` | `default-ci-current` | none |
| `tests/unit/test_m8b_taifex_openapi_large_trader_oi_adapter.py` | `KEEP_DEFAULT_COMPATIBILITY` | `default-ci-current` | none |
| `tests/unit/test_m8b_taifex_openapi_put_call_ratio_adapter.py` | `KEEP_DEFAULT_COMPATIBILITY` | `default-ci-current` | none |
| `tests/unit/test_m8b_taifex_openapi_block_trade_adapter.py` | `KEEP_DEFAULT_COMPATIBILITY` | `default-ci-current` | none |
| `tests/unit/test_m8b_taifex_openapi_execution.py` | `KEEP_DEFAULT_COMPATIBILITY` | `default-ci-current` | none |
| `tests/unit/test_m8b_taifex_openapi_context_integration.py` | `KEEP_DEFAULT_COMPATIBILITY` | `default-ci-current` | none |
| `tests/unit/test_m8b_taifex_openapi_conversation_projection.py` | `KEEP_DEFAULT_COMPATIBILITY` | `default-ci-current` | none |
| `tests/unit/test_m8b_final_acceptance.py` | `MOVE_HISTORICAL_AFTER_TG3` | `historical-acceptance` | TG-3 historical integrity; TG-4 shadow CI |
| `tests/unit/test_m8b_taifex_openapi_currentness.py` | `KEEP_DEFAULT_COMPATIBILITY` | `default-ci-current` | none |
| `tests/unit/test_m8b_taifex_openapi_schema_and_validation.py` | `KEEP_DEFAULT_COMPATIBILITY` | `default-ci-current` | none |
| `tests/unit/test_m8b_taifex_openapi_projection_families.py` | `KEEP_DEFAULT_COMPATIBILITY` | `default-ci-current` | none |
| `tests/unit/test_m8_through_m8b_consolidated_acceptance.py` | `MOVE_HISTORICAL_AFTER_TG3` | `historical-acceptance` | TG-3 historical integrity; TG-4 shadow CI |
| `tests/unit/test_m8c_00_final_acceptance.py` | `MOVE_HISTORICAL_AFTER_TG3` | `historical-acceptance` | TG-3 historical integrity; TG-4 shadow CI |
| `tests/unit/test_m8c_taifex_mis_contract_preflight.py` | `MOVE_HISTORICAL_AFTER_TG3` | `historical-acceptance` | TG-3 historical integrity; TG-4 shadow CI |
| `tests/unit/test_m8c_taifex_mis_currentness_preflight.py` | `MOVE_HISTORICAL_AFTER_TG3` | `historical-acceptance` | TG-3 historical integrity; TG-4 shadow CI |
| `tests/unit/test_m8c_taifex_mis_identity_contract.py` | `KEEP_DEFAULT_COMPATIBILITY` | `default-ci-current` | none |
| `tests/unit/test_m8c_taifex_mis_probe_parsers.py` | `KEEP_DEFAULT_COMPATIBILITY` | `default-ci-current` | none |
| `tests/unit/test_m8c_01_taifex_mis_runtime.py` | `KEEP_DEFAULT_COMPATIBILITY` | `default-ci-current` | none |
| `tests/unit/test_m8c_02_taifex_mis_context_integration.py` | `KEEP_DEFAULT_COMPATIBILITY` | `default-ci-current` | none |
| `tests/unit/test_m8r_06_01c1b_compact_runtime_identity_index.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/unit/test_m8r_06_01c2_mode_a_pointer_activation.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/unit/test_m8r_08f_r0_rotation_candidate_contract.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/unit/test_m8r_06_02_mode_b1_preview.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/unit/test_m8r_06_human_browser_authorize_state.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/unit/test_m8r_06_ai_handoff_repair_02.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/unit/test_m8r_05b_03_operation_result.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/unit/test_m8r_05b_03_aggregation.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/integration/test_m8r_05b_03_multi_artifact_contract.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/unit/test_m8r_06_03_execute_once.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/unit/test_m8r_06_03_localhost_vertical.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/unit/test_m8r_06_03_mode_b2_authorization.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/unit/test_m8r_06_03_production_adapter.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/unit/test_m8r_06_03_batch_runtime.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/unit/test_m8r_06_04_mode_c.py` | `SPLIT_MIXED_CURRENT_HISTORICAL` | `default-ci-current + historical-acceptance` | split current/historical cases; TG-4 shadow CI |
| `tests/unit/m8r_05c/test_m8r_05c_integration.py` | `MOVE_HISTORICAL_AFTER_TG3` | `historical-acceptance` | TG-3 historical integrity; TG-4 shadow CI |
| `tests/unit/test_m8r_05c_determinism.py` | `MOVE_HISTORICAL_AFTER_TG3` | `historical-acceptance` | TG-3 historical integrity; TG-4 shadow CI |
| `tests/unit/test_m8r_05c_lineage.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/unit/test_m8r_05c_containment.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/integration/test_unified_workbench_api.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/unit/test_product_version.py` | `KEEP_DEFAULT_CONTRACT` | `default-ci-current` | none |
| `tests/unit/test_validate_product_version_consistency.py` | `KEEP_DEFAULT_CONTRACT` | `default-ci-current` | none |
| `tests/unit/test_validate_v1_public_contracts.py` | `KEEP_DEFAULT_REWRITE_BRITTLE` | `default-ci-current` | replacement assertion before brittle assertion removal |
| `tests/unit/test_build_v1_release_manifest.py` | `MOVE_RELEASE_PRECHECK` | `release-preflight` | TG-4 shadow CI |
| `tests/unit/test_validate_release_hygiene.py` | `KEEP_DEFAULT_CONTRACT` | `default-ci-current` | none |
| `tests/unit/test_browser_e2e_requirements.py` | `MOVE_RELEASE_PRECHECK` | `release-preflight` | TG-4 shadow CI |
| `tests/unit/test_m8r_08c_r1_launcher_readiness.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/unit/test_phase_g_request_v2_and_catalog.py` | `KEEP_DEFAULT_COMPATIBILITY` | `default-ci-current` | none |
| `tests/unit/test_phase_g_routing_and_planner.py` | `KEEP_DEFAULT_COMPATIBILITY` | `default-ci-current` | none |
| `tests/unit/test_phase_g_material_disclosures.py` | `KEEP_DEFAULT_COMPATIBILITY` | `default-ci-current` | none |
| `tests/unit/test_phase_g_monthly_revenue.py` | `KEEP_DEFAULT_COMPATIBILITY` | `default-ci-current` | none |
| `tests/unit/test_phase_g_result_v2_projection.py` | `KEEP_DEFAULT_COMPATIBILITY` | `default-ci-current` | none |
| `tests/unit/test_phase_g_mode_c_v2.py` | `KEEP_DEFAULT_COMPATIBILITY` | `default-ci-current` | none |
| `tests/unit/test_phase_g_runtime_activation.py` | `KEEP_DEFAULT_COMPATIBILITY` | `default-ci-current` | none |
| `tests/unit/test_phase_g_p0_acceptance_ledger.py` | `MOVE_HISTORICAL_AFTER_TG3` | `historical-acceptance` | TG-3 historical integrity; TG-4 shadow CI |
| `tests/unit/test_phase_g_pr_d_live_acceptance.py` | `MOVE_HISTORICAL_AFTER_TG3` | `historical-acceptance` | TG-3 historical integrity; TG-4 shadow CI |
| `tests/unit/test_phase_g_pr_d_public_surfaces.py` | `KEEP_DEFAULT_REWRITE_BRITTLE` | `default-ci-current` | replacement assertion before brittle assertion removal |
| `tests/unit/test_phase_g_pr_d_closure.py` | `SPLIT_MIXED_CURRENT_HISTORICAL` | `default-ci-current + historical-acceptance` | split current/historical cases; TG-4 shadow CI |
| `tests/unit/test_phase_h_v3_contract_freeze.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/unit/test_phase_h_imp_0_passive_v3_compatibility.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/unit/test_phase_h_imp_1_h4_deterministic_safety.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/unit/test_phase_h_imp_2_h1_dormant_adapters.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/unit/test_phase_h_imp_3_h2_dormant_adapters.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/unit/test_phase_h_imp_6_v3_projection_handoff.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |
| `tests/integration/test_phase_h_imp_7d_deterministic_e2e.py` | `KEEP_DEFAULT_REWRITE_BRITTLE` | `default-ci-current` | replacement assertion before brittle assertion removal |
| `tests/unit/test_phase_h_act_h1_tpex_attention_activation.py` | `KEEP_DEFAULT_CURRENT` | `default-ci-current` | none |

## TG-1 exit / next gate

TG-1 establishes disposition proposals only. TG-2/TG-3 may add semantic markers and historical-integrity protection, but **must not cut over default CI**. TG-4 shadow CI must pass before any TG-5 default-CI authority change.
