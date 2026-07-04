# M6J-R2 Automated Test Risk Inventory and Clustered Retirement

## Purpose

M6J-R2 adds machine-generated test-risk inventory tooling so future retirement decisions can start from repeatable evidence rather than intuition. Commit 3 executes the human-reviewed clustered retirement step on top of the accepted AST analyzer and rule-based classifier. The work remains inventory/test-suite governance only; it does not change product behavior, source adapters, observation semantics, source-health semantics, Conversation Package semantics, M5F, TLS policy, or trading boundaries.

## Method

The analyzer at `scripts/analyze_test_risk_inventory.py` statically parses `tests/` with the Python standard-library AST. It identifies test functions, decorators, pytest markers, parametrization estimates, imports, called functions, assertions, string constants, inferred risk tags, likely authoritative owners, and duplicate-risk cluster keys. It does not execute tests and does not dynamically import application code.

Risk inference uses rule-based evidence scoring. High-risk tags require multiple pieces of evidence; for example, `mcp_fail_closed` requires MCP identity plus rejection/error/status evidence, `invalid_ssl_fail_closed` requires SSL/TLS policy evidence plus invalid/unsupported evidence plus fail-closed/400/exception evidence, `frontend_public_write` requires an exact `frontend/public` path or frontend plus write/output/destination evidence, and `frontend_static_contract` requires frontend plus static/contract/html/js/token evidence.

Cluster keys use `primary_risk_id:normalized_called_target:normalized_assertion_shape`. Commit 3 adds review-priority metadata to duplicate clusters: `review_priority`, `review_score`, `member_files`, `unique_called_targets`, `unique_assertion_shapes`, and `owner_confidence`. Priority is advisory only and is not an auto-delete rule.

Static analysis is advisory. It does not prove semantic equivalence by itself. Human review is still required before retirement.

## Inventory outputs

- Script path: `scripts/analyze_test_risk_inventory.py`
- Output directory: `docs/reviews/m6j_r2_inventory/`
- Inventory CSV: `docs/reviews/m6j_r2_inventory/test_function_inventory.csv`
- Duplicate cluster CSV: `docs/reviews/m6j_r2_inventory/duplicate_risk_clusters.csv`
- Human review ledger: `docs/reviews/m6j_r2_inventory/human_cluster_review.csv`
- Summary: `docs/reviews/m6j_r2_inventory/summary.md`

## Before/After Test Portfolio

| Metric | Before retirement | After retirement | Delta |
|---|---:|---:|---:|
| Static AST test functions | 644 | 637 | -7 |
| Pytest collected tests | 726 | 719 | -7 |
| Duplicate risk clusters | 439 | 439 | 0 |
| manual_review_required clusters | 101 | 101 | 0 |
| P0 clusters | 11 | 11 | 0 |
| P1 clusters | 47 | 47 | 0 |


## Risk tag distribution after retirement

- `unknown`: 257
- `frontend_static_contract`: 79
- `frontend_public_write`: 65
- `ai_context_pack`: 57
- `conversation_context`: 56
- `research_generated_write`: 44
- `m5f_canonical`: 43
- `m5c_staging`: 43
- `m5b_staging`: 36
- `mcp_fail_closed`: 33
- `m5e_publication`: 29
- `production_prod_write`: 27
- `snapshot_schema`: 24
- `bounded_watchlist`: 21
- `governance_path`: 21
- `source_health`: 19
- `ssl_policy`: 18
- `no_trading_semantics`: 16
- `no_full_market_scan`: 13
- `fastapi_execute_confirmation`: 11
- `m6g_browser_e2e`: 11
- `briefing_render`: 9
- `raw_payload_leakage`: 9
- `m6e_acceptance`: 7
- `invalid_ssl_fail_closed`: 7
- `forbidden_behavior`: 7
- `observation_not_canonical`: 3

## Analyzer prioritization after retirement

- P0: 11
- P1: 47
- P2: 23
- P3: 358

## Largest duplicate clusters after retirement

- `mcp_fail_closed:asyncio_run:equals` — size 14; priority `P2`; action `manual_review_required`; reason: static cluster overlap needs human semantic review
- `unknown:generate_symbol_observations:contains` — size 7; priority `P0`; action `manual_review_required`; reason: static cluster overlap needs human semantic review
- `unknown:load:equals` — size 7; priority `P0`; action `manual_review_required`; reason: static cluster overlap needs human semantic review
- `unknown:any:contains+equals` — size 6; priority `P2`; action `manual_review_required`; reason: static cluster overlap needs human semantic review
- `unknown:copy_candidate:contains` — size 6; priority `P0`; action `manual_review_required`; reason: static cluster overlap needs human semantic review
- `unknown:datetime:contains+equals` — size 6; priority `P0`; action `manual_review_required`; reason: static cluster overlap needs human semantic review
- `unknown:datetime_now:contains+truthy` — size 6; priority `P3`; action `manual_review_required`; reason: static cluster overlap needs human semantic review
- `frontend_static_contract:read_text:contains` — size 5; priority `P0`; action `manual_review_required`; reason: static cluster overlap needs human semantic review

## Human Cluster Review

- Candidate clusters reviewed: 32
- P0 reviewed: 11
- P1 reviewed: 20
- Additional safety-critical duplicate cluster reviewed: 1 (`mcp_fail_closed:assertionerror:boolean_identity+equals`).

## Reviewed P0 Clusters

- `unknown:load:equals` — `false`; Same load/assertion shape, but each member validates a different schema or release artifact with different fixture semantics.
- `unknown:copy_candidate:contains` — `partial`; Shared copy_candidate setup and contains assertions, but each member mutates a different artifact field: temporary path, manifest finality, PR binding, extra files, baseline drift, or non-json artifact.
- `unknown:generate_symbol_observations:contains` — `false`; Common observation generator target, but members cover distinct observation semantics: stale/EOD, live spread, price direction, threshold proximity, volume, and failed observations.
- `frontend_static_contract:read_text:contains` — `partial`; Static text assertions overlap, but files guard different surfaces: accessibility labels, observability panels, readonly schema wording, and M5N workbench contract.
- `unknown:datetime:contains+equals` — `false`; Shared datetime assertion shape, but each member validates a different source adapter timestamp/freshness transformation.
- `unknown:read_text:contains` — `partial`; All read text and check tokens, but they protect separate docs/workflows: freshness matrix, PR checklist, pytest markers, repo-wide governance, and test segmentation.
- `conversation_context:build_frontend_readonly_context_package:contains` — `false`; Same builder target, but stale, delayed, and live-candidate caveats are distinct display semantics.
- `m5b_staging:base_result:no_assert` — `partial`; Shared helper/setup path, but members exercise distinct staging candidate failure and manifest behavior.
- `m5b_staging:datetime:equals` — `false`; Same datetime target and equality shape, but members cover before, exact authorized, pre-expiry, exact expiry, and receipt audit boundaries.
- `unknown:any:equals` — `partial`; Common any/equality pattern, but assertions check separate registry and adapter error families.
- `unknown:build_adapter_report:contains+equals` — `false`; Same adapter report target, but members cover official OpenAPI mapping, malformed summaries, failed targets, and integration shape.

## Reviewed P1 Clusters

- `briefing_render:render_chatgpt_briefing:contains` — `false`; Same renderer and contains assertions, but members cover raw collection suppression, market-session dict rendering, table escaping, and empty-list rendering.
- `conversation_context:build_frontend_readonly_context_package:boolean_identity` — `partial`; Both check boolean flags from the same builder, but one validates readonly_only positive construction while the other validates multiple false governance flags.
- `production_prod_write:load:truthy` — `false`; Shared load/truthy shape, but files validate different production-safety metadata in token, evidence, and readiness artifacts.
- `unknown:any:boolean_identity+contains+equals` — `false`; Same Yahoo probe helper shape, but members cover separate identity mismatch and batch failure cases.
- `unknown:body:truthy` — `false`; Common PR body parser target, but members cover exact match, extra nonexistent file, missing changed file warning, and duplicate entry warning.
- `unknown:get_env:contains+equals` — `false`; Same environment helper shape, but members cover prohibited sources, max target enforcement, and source rejection.
- `unknown:load:contains` — `false`; Shared JSON load plus contains assertions, but each member validates a distinct policy/fixture schema.
- `unknown:path:contains` — `partial`; Path token overlap only; members protect distinct workflow and convergence documentation contracts.
- `unknown:payload:equals` — `false`; Same payload helper shape, but members cover different validator acceptance/rejection families.
- `unknown:validate:equals` — `false`; Identical validate()==[] assertion shape across different validator modules and artifacts, so semantic equivalence is false.
- `ai_context_pack:build_ai_context_pack:contains` — `false`; Same pack builder and contains assertions, but members verify source baseline, usable live filtering, and prohibited vocabulary absence.
- `frontend_static_contract:path:contains` — `partial`; Frontend path/static overlap, but one guards M5K endpoint model while the other guards source-health panel contract.
- `m5c_staging:validate_request:contains` — `false`; Same request validator target, but one checks duplicate/noncanonical run dir and another checks binding/schema requirements.
- `unknown:_assert_probe_envelope_first_row_freshness:no_assert` — `false`; Shared helper has no direct asserts in wrapper, but each member feeds distinct TWSE MIS freshness fixtures.
- `unknown:_parse_mis_item:equals` — `false`; Same MIS parser target, but members validate price fallback, unavailable price, and numeric price preference.
- `unknown:build_summary_entry:boolean_identity+equals` — `false`; Same summary builder, but one covers successful source summary and one covers None/failure summary.
- `unknown:datetime:equals` — `false`; Same datetime equality shape, but source-specific timestamp fields and timezone preferences differ.
- `unknown:draft202012validator_check_schema:no_assert` — `false`; Same schema checker call but distinct schema documents: authorization token, evidence ledger, and source contract.
- `unknown:load_valid:contains` — `false`; Same load_valid helper, but members cover different M5A authorization fixture families.
- `unknown:malformed_write_text:boolean_identity+equals` — `false`; Both write malformed files, but expected structured outcomes differ between request and result envelopes.

## True Duplicate Clusters

- `mcp_fail_closed:assertionerror:boolean_identity+equals` — retired 7 duplicate members; authoritative owner preserved: `tests/unit/test_mcp_server.py::test_controlled_tool_without_confirmation_fails_closed_without_runner`. All eight members used the same VALID_CONTROLLED_ARGS, the same monkeypatch that raises on runner execution, the same MCP tool call, and the same four assertions; the preserved owner keeps the legacy controlled tool fail-closed/no-network/no-write guard.

## Partial Equivalence Clusters

- `unknown:copy_candidate:contains` — Shared copy_candidate setup and contains assertions, but each member mutates a different artifact field: temporary path, manifest finality, PR binding, extra files, baseline drift, or non-json artifact.
- `frontend_static_contract:read_text:contains` — Static text assertions overlap, but files guard different surfaces: accessibility labels, observability panels, readonly schema wording, and M5N workbench contract.
- `unknown:read_text:contains` — All read text and check tokens, but they protect separate docs/workflows: freshness matrix, PR checklist, pytest markers, repo-wide governance, and test segmentation.
- `m5b_staging:base_result:no_assert` — Shared helper/setup path, but members exercise distinct staging candidate failure and manifest behavior.
- `unknown:any:equals` — Common any/equality pattern, but assertions check separate registry and adapter error families.
- `conversation_context:build_frontend_readonly_context_package:boolean_identity` — Both check boolean flags from the same builder, but one validates readonly_only positive construction while the other validates multiple false governance flags.
- `unknown:path:contains` — Path token overlap only; members protect distinct workflow and convergence documentation contracts.
- `frontend_static_contract:path:contains` — Frontend path/static overlap, but one guards M5K endpoint model while the other guards source-health panel contract.

## False Duplicate Clusters

- `unknown:load:equals` — Same load/assertion shape, but each member validates a different schema or release artifact with different fixture semantics.
- `unknown:generate_symbol_observations:contains` — Common observation generator target, but members cover distinct observation semantics: stale/EOD, live spread, price direction, threshold proximity, volume, and failed observations.
- `unknown:datetime:contains+equals` — Shared datetime assertion shape, but each member validates a different source adapter timestamp/freshness transformation.
- `conversation_context:build_frontend_readonly_context_package:contains` — Same builder target, but stale, delayed, and live-candidate caveats are distinct display semantics.
- `m5b_staging:datetime:equals` — Same datetime target and equality shape, but members cover before, exact authorized, pre-expiry, exact expiry, and receipt audit boundaries.
- `unknown:build_adapter_report:contains+equals` — Same adapter report target, but members cover official OpenAPI mapping, malformed summaries, failed targets, and integration shape.
- `briefing_render:render_chatgpt_briefing:contains` — Same renderer and contains assertions, but members cover raw collection suppression, market-session dict rendering, table escaping, and empty-list rendering.
- `production_prod_write:load:truthy` — Shared load/truthy shape, but files validate different production-safety metadata in token, evidence, and readiness artifacts.
- `unknown:any:boolean_identity+contains+equals` — Same Yahoo probe helper shape, but members cover separate identity mismatch and batch failure cases.
- `unknown:body:truthy` — Common PR body parser target, but members cover exact match, extra nonexistent file, missing changed file warning, and duplicate entry warning.
- `unknown:get_env:contains+equals` — Same environment helper shape, but members cover prohibited sources, max target enforcement, and source rejection.
- `unknown:load:contains` — Shared JSON load plus contains assertions, but each member validates a distinct policy/fixture schema.
- `unknown:payload:equals` — Same payload helper shape, but members cover different validator acceptance/rejection families.
- `unknown:validate:equals` — Identical validate()==[] assertion shape across different validator modules and artifacts, so semantic equivalence is false.
- `ai_context_pack:build_ai_context_pack:contains` — Same pack builder and contains assertions, but members verify source baseline, usable live filtering, and prohibited vocabulary absence.
- `m5c_staging:validate_request:contains` — Same request validator target, but one checks duplicate/noncanonical run dir and another checks binding/schema requirements.
- `unknown:_assert_probe_envelope_first_row_freshness:no_assert` — Shared helper has no direct asserts in wrapper, but each member feeds distinct TWSE MIS freshness fixtures.
- `unknown:_parse_mis_item:equals` — Same MIS parser target, but members validate price fallback, unavailable price, and numeric price preference.
- `unknown:build_summary_entry:boolean_identity+equals` — Same summary builder, but one covers successful source summary and one covers None/failure summary.
- `unknown:datetime:equals` — Same datetime equality shape, but source-specific timestamp fields and timezone preferences differ.
- `unknown:draft202012validator_check_schema:no_assert` — Same schema checker call but distinct schema documents: authorization token, evidence ledger, and source contract.
- `unknown:load_valid:contains` — Same load_valid helper, but members cover different M5A authorization fixture families.
- `unknown:malformed_write_text:boolean_identity+equals` — Both write malformed files, but expected structured outcomes differ between request and result envelopes.

## Retirement Executed

| retired_test_or_assertion | risk_cluster_key | risk_tags | authoritative_owner | semantic_equivalence | why_safe |
|---|---|---|---|---|---|
| `tests/unit/test_mcp_server.py::test_controlled_tool_invalid_source_or_target_fails_closed_without_runner` | `mcp_fail_closed:assertionerror:boolean_identity+equals` | `mcp_fail_closed` | `tests/unit/test_mcp_server.py::test_controlled_tool_without_confirmation_fails_closed_without_runner` | true | Same arguments, same monkeypatch, same MCP call, and same four assertions; preserved owner retains fail-closed/no-network/no-write protection. |
| `tests/unit/test_mcp_server.py::test_controlled_tool_write_or_refresh_request_fails_closed_without_runner` | `mcp_fail_closed:assertionerror:boolean_identity+equals` | `mcp_fail_closed` | `tests/unit/test_mcp_server.py::test_controlled_tool_without_confirmation_fails_closed_without_runner` | true | Same arguments, same monkeypatch, same MCP call, and same four assertions; preserved owner retains fail-closed/no-network/no-write protection. |
| `tests/unit/test_mcp_server.py::test_controlled_tool_valid_confirmation_calls_only_runner_wrapper` | `mcp_fail_closed:assertionerror:boolean_identity+equals` | `mcp_fail_closed` | `tests/unit/test_mcp_server.py::test_controlled_tool_without_confirmation_fails_closed_without_runner` | true | Same arguments, same monkeypatch, same MCP call, and same four assertions; preserved owner retains fail-closed/no-network/no-write protection. |
| `tests/unit/test_mcp_server.py::test_controlled_tool_duplicate_scope_fails_closed_without_runner` | `mcp_fail_closed:assertionerror:boolean_identity+equals` | `mcp_fail_closed` | `tests/unit/test_mcp_server.py::test_controlled_tool_without_confirmation_fails_closed_without_runner` | true | Same arguments, same monkeypatch, same MCP call, and same four assertions; preserved owner retains fail-closed/no-network/no-write protection. |
| `tests/unit/test_mcp_server.py::test_controlled_tool_missing_runner_path_returns_structured_failure` | `mcp_fail_closed:assertionerror:boolean_identity+equals` | `mcp_fail_closed` | `tests/unit/test_mcp_server.py::test_controlled_tool_without_confirmation_fails_closed_without_runner` | true | Same arguments, same monkeypatch, same MCP call, and same four assertions; preserved owner retains fail-closed/no-network/no-write protection. |
| `tests/unit/test_mcp_server.py::test_controlled_tool_timeout_result_does_not_claim_no_network` | `mcp_fail_closed:assertionerror:boolean_identity+equals` | `mcp_fail_closed` | `tests/unit/test_mcp_server.py::test_controlled_tool_without_confirmation_fails_closed_without_runner` | true | Same arguments, same monkeypatch, same MCP call, and same four assertions; preserved owner retains fail-closed/no-network/no-write protection. |
| `tests/unit/test_mcp_server.py::test_controlled_tool_runner_error_after_launch_does_not_claim_no_network` | `mcp_fail_closed:assertionerror:boolean_identity+equals` | `mcp_fail_closed` | `tests/unit/test_mcp_server.py::test_controlled_tool_without_confirmation_fails_closed_without_runner` | true | Same arguments, same monkeypatch, same MCP call, and same four assertions; preserved owner retains fail-closed/no-network/no-write protection. |

## Analyzer Effectiveness Assessment

- The analyzer materially reduced manual review scope from 439 clusters to 58 P0/P1 clusters, then the top 30 eligible P0/P1 clusters plus one safety-critical exact-duplicate cluster were reviewed in detail.
- True duplicate clusters found: 1.
- Tests/assertions retired: 7 test functions, 0 assertion-only retirements.
- Authoritative owner preserved: `tests/unit/test_mcp_server.py::test_controlled_tool_without_confirmation_fails_closed_without_runner`.
- False cluster patterns found: common helper names across different schema files, common renderer/builder functions with distinct semantic fixtures, source adapter normalizers sharing timestamp/assertion shapes, static text contracts across different frontend/docs surfaces, and identical `validate()==[]` shapes for different validator modules.
- The analyzer is useful enough to retain because it found a safety-critical exact duplicate cluster and narrowed review to high-value clusters, but it still needs future improvements to distinguish fixture semantics and production targets.

## Clusters intentionally not retired

- M5F canonical, bounded observation/watchlist, source health, Conversation Package, M6E, M6G, SSL policy, FastAPI execute confirmation, raw-payload leakage, no-trading semantics, governance scanner, unique transformation, crash recovery, tamper detection, rollback, and failure-injection owners were preserved.
- Partial or false equivalence was not retired.

## Precision fixtures retained

Synthetic analyzer tests verify that isolated words such as `fail`, `contract`, or `public` do not trigger high-risk tags by themselves, while MCP invalid-request fail-closed, invalid SSL policy HTTP 400, exact `frontend/public`, frontend static contract, and reviewable cluster-key examples are tagged as intended.

## Limitations of static analysis

- Call and assertion fingerprints cannot prove that setup side effects, monkeypatches, fixtures, subprocess behavior, or failure modes are equivalent.
- Risk tags are rule-based and intentionally favor precision over recall for retirement review.
- Parametrization case counts are estimates for simple literal lists/tuples only.
- Human review remains required before deleting tests.
