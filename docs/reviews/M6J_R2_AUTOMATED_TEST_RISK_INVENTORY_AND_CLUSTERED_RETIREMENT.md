# M6J-R2 Automated Test Risk Inventory and Clustered Retirement

## Purpose

M6J-R2 adds machine-generated test-risk inventory tooling so future retirement decisions can start from repeatable evidence rather than intuition. The work is inventory and governance tooling only; it does not change product behavior, source adapters, observation semantics, source-health semantics, Conversation Package semantics, M5F, TLS policy, or trading boundaries.

## Method

The analyzer at `scripts/analyze_test_risk_inventory.py` statically parses `tests/` with the Python standard-library AST. It identifies test functions, decorators, pytest markers, parametrization estimates, imports, called functions, assertions, string constants, inferred risk tags, likely authoritative owners, and duplicate-risk cluster keys. It does not execute tests and does not dynamically import application code.

Static analysis is advisory. It does not prove semantic equivalence by itself. Human review is still required before retirement.

## Inventory outputs

- Script path: `scripts/analyze_test_risk_inventory.py`
- Output directory: `docs/reviews/m6j_r2_inventory/`
- Inventory CSV: `docs/reviews/m6j_r2_inventory/test_function_inventory.csv`
- Duplicate cluster CSV: `docs/reviews/m6j_r2_inventory/duplicate_risk_clusters.csv`
- Summary: `docs/reviews/m6j_r2_inventory/summary.md`

## Total test functions detected

- Static AST test functions detected: 636

## Risk tag distribution

- `mcp_fail_closed`: 209
- `invalid_ssl_fail_closed`: 203
- `frontend_static_contract`: 181
- `frontend_public_write`: 142
- `m5b_staging`: 130
- `snapshot_schema`: 112
- `observation_not_canonical`: 93
- `unknown`: 85
- `bounded_watchlist`: 81
- `fastapi_execute_confirmation`: 75
- `m5c_staging`: 63
- `m5e_publication`: 63
- `ai_context_pack`: 57
- `production_prod_write`: 54
- `governance_path`: 53
- `m5f_canonical`: 51
- `ssl_policy`: 30
- `conversation_context`: 27
- `research_generated_write`: 26
- `no_trading_semantics`: 24
- `briefing_render`: 23
- `source_health`: 15
- `no_full_market_scan`: 15
- `raw_payload_leakage`: 12
- `m6g_browser_e2e`: 11
- `m6e_acceptance`: 7
- `forbidden_behavior`: 7

## Largest duplicate clusters

- `invalid_ssl_fail_closed:assert:8b0002c9c02c` — size 5; action `manual_review_required`; reason: static cluster overlap needs human semantic review
- `fastapi_execute_confirmation:assert:8b0002c9c02c` — size 3; action `manual_review_required`; reason: static cluster overlap needs human semantic review
- `unknown:no_assert:_assert_probe_envelope_first_row_freshness` — size 3; action `manual_review_required`; reason: static cluster overlap needs human semantic review
- `bounded_watchlist:assert:fce22b4b2569` — size 2; action `manual_review_required`; reason: static cluster overlap needs human semantic review
- `frontend_public_write:assert:40c836ea8217` — size 2; action `manual_review_required`; reason: static cluster overlap needs human semantic review

## safe_to_auto_retire clusters

- Count: 0
- No repository clusters were retired in this PR because the conservative analyzer found no safe cluster that met all required conditions in the real suite: `semantic_equivalence_guess=true`, `safe_to_auto_retire=yes`, explicit authoritative owner, and non-safety-critical duplicate risk.

## manual_review_required clusters

- Count: 11
- These clusters show static overlap but require human semantic review before any retirement. They were intentionally preserved.

## Clusters intentionally not retired

- M5F canonical, bounded observation/watchlist, source health, Conversation Package, M6E, M6G, SSL policy, FastAPI/MCP fail-closed, raw-payload leakage, no-trading semantics, governance scanner, unique transformation, crash recovery, tamper detection, rollback, and failure-injection owners were preserved.
- Partial or unclear equivalence was not retired.

## Retirement section

| retired_test_or_assertion | risk_cluster_key | risk_tags | authoritative_owner | semantic_equivalence | why_safe |
|---|---|---|---|---|---|
| None | n/a | n/a | n/a | n/a | No real-suite cluster satisfied the allowed retirement condition. |

## Limitations of static analysis

- Call and assertion fingerprints cannot prove that setup side effects, monkeypatches, fixtures, subprocess behavior, or failure modes are equivalent.
- Risk tags are heuristic and intentionally over-inclusive.
- Parametrization case counts are estimates for simple literal lists/tuples only.
- Human review remains required before deleting tests.
