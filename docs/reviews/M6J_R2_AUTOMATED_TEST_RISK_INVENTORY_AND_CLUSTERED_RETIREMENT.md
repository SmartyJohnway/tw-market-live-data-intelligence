# M6J-R2 Automated Test Risk Inventory and Clustered Retirement

## Purpose

M6J-R2 adds machine-generated test-risk inventory tooling so future retirement decisions can start from repeatable evidence rather than intuition. Commit 2 keeps the AST analyzer skeleton and improves risk-classification precision by replacing broad keyword OR matching with rule-based evidence scoring. The work is inventory and governance tooling only; it does not change product behavior, source adapters, observation semantics, source-health semantics, Conversation Package semantics, M5F, TLS policy, or trading boundaries.

## Method

The analyzer at `scripts/analyze_test_risk_inventory.py` statically parses `tests/` with the Python standard-library AST. It identifies test functions, decorators, pytest markers, parametrization estimates, imports, called functions, assertions, string constants, inferred risk tags, likely authoritative owners, and duplicate-risk cluster keys. It does not execute tests and does not dynamically import application code.

Risk inference now uses rule-based evidence scoring. High-risk tags require multiple pieces of evidence; for example, `mcp_fail_closed` requires MCP identity plus rejection/error/status evidence, `invalid_ssl_fail_closed` requires SSL/TLS policy evidence plus invalid/unsupported evidence plus fail-closed/400/exception evidence, `frontend_public_write` requires an exact `frontend/public` path or frontend plus write/output/destination evidence, and `frontend_static_contract` requires frontend plus static/contract/html/js/token evidence.

Cluster keys now use `primary_risk_id:normalized_called_target:normalized_assertion_shape` instead of first tag plus assertion hash, making clusters more reviewable and stable across assertion text churn.

Static analysis is advisory. It does not prove semantic equivalence by itself. Human review is still required before retirement.

## Inventory outputs

- Script path: `scripts/analyze_test_risk_inventory.py`
- Output directory: `docs/reviews/m6j_r2_inventory/`
- Inventory CSV: `docs/reviews/m6j_r2_inventory/test_function_inventory.csv`
- Duplicate cluster CSV: `docs/reviews/m6j_r2_inventory/duplicate_risk_clusters.csv`
- Summary: `docs/reviews/m6j_r2_inventory/summary.md`

## Total test functions detected

- Static AST test functions detected: 644

## Risk tag distribution

- `unknown`: 257
- `frontend_static_contract`: 79
- `frontend_public_write`: 65
- `ai_context_pack`: 57
- `conversation_context`: 56
- `research_generated_write`: 44
- `m5f_canonical`: 43
- `m5c_staging`: 43
- `mcp_fail_closed`: 40
- `m5b_staging`: 36
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

## Largest duplicate clusters

- `mcp_fail_closed:asyncio_run:equals` — size 14; action `manual_review_required`; reason: static cluster overlap needs human semantic review
- `mcp_fail_closed:assertionerror:boolean_identity+equals` — size 10; action `manual_review_required`; reason: static cluster overlap needs human semantic review
- `unknown:generate_symbol_observations:contains` — size 7; action `manual_review_required`; reason: static cluster overlap needs human semantic review
- `unknown:load:equals` — size 7; action `manual_review_required`; reason: static cluster overlap needs human semantic review
- `unknown:any:contains+equals` — size 6; action `manual_review_required`; reason: static cluster overlap needs human semantic review
- `unknown:copy_candidate:contains` — size 6; action `manual_review_required`; reason: static cluster overlap needs human semantic review
- `unknown:datetime:contains+equals` — size 6; action `manual_review_required`; reason: static cluster overlap needs human semantic review
- `unknown:datetime_now:contains+truthy` — size 6; action `manual_review_required`; reason: static cluster overlap needs human semantic review

## safe_to_auto_retire clusters

- Count: 0
- No repository clusters were retired in this PR because Commit 2 is a precision pass and the real suite still has no conservative cluster satisfying all required conditions: `semantic_equivalence_guess=true`, `safe_to_auto_retire=yes`, explicit authoritative owner, and non-safety-critical duplicate risk.

## manual_review_required clusters

- Count: 101
- These clusters show static overlap but require human semantic review before any retirement. They were intentionally preserved.

## Clusters intentionally not retired

- M5F canonical, bounded observation/watchlist, source health, Conversation Package, M6E, M6G, SSL policy, FastAPI/MCP fail-closed, raw-payload leakage, no-trading semantics, governance scanner, unique transformation, crash recovery, tamper detection, rollback, and failure-injection owners were preserved.
- Partial or unclear equivalence was not retired.

## Retirement section

| retired_test_or_assertion | risk_cluster_key | risk_tags | authoritative_owner | semantic_equivalence | why_safe |
|---|---|---|---|---|---|
| None | n/a | n/a | n/a | n/a | Commit 2 was a classifier-precision pass; no real-suite cluster satisfied the allowed retirement condition. |

## Precision fixtures added

Synthetic analyzer tests now verify that isolated words such as `fail`, `contract`, or `public` do not trigger high-risk tags by themselves, while MCP invalid-request fail-closed, invalid SSL policy HTTP 400, exact `frontend/public`, frontend static contract, and reviewable cluster-key examples are tagged as intended.

## Limitations of static analysis

- Call and assertion fingerprints cannot prove that setup side effects, monkeypatches, fixtures, subprocess behavior, or failure modes are equivalent.
- Risk tags are rule-based and intentionally favor precision over recall for retirement review.
- Parametrization case counts are estimates for simple literal lists/tuples only.
- Human review remains required before deleting tests.
