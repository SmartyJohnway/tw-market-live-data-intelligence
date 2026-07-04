# M6J True Duplicate Risk Retirement

## Scope

M6J performed a conservative duplicate-risk retirement pass. It did not change product code, source adapters, M5F canonical artifacts, observation semantics, source-health semantics, Conversation Package behavior, TLS policy, M6E acceptance, or M6G browser/operator E2E behavior.

## Counts

- Before direct test count: 630 direct `test_*` functions.
- After direct test count: 627 direct `test_*` functions.
- Net direct reduction: 3 direct test functions.
- Before pytest collected count: 712 collected; 711 selected by `pytest -m "not network" -v`; 710 passed, 1 skipped, 1 deselected (M6I baseline).
- After pytest collected count: 709 collected; 708 selected by `pytest -m "not network" -v`; final pass/fail recorded in validation output for this PR.
- Net collected reduction: 3 collected pytest cases.

## Files changed

- `tests/unit/test_m5fgh_frontend_static.py` removed.
- `tests/unit/test_frontend_readonly_static_contracts.py` removed one tautological direct test.
- `tests/unit/test_m5c_controlled_staging_promotion.py` removed.
- `docs/reviews/m6j_duplicate_risk_map.csv` added.
- `docs/reviews/M6J_TRUE_DUPLICATE_RISK_RETIREMENT.md` added.
- `docs/reviews/m6h_test_inventory.csv` updated for changed direct counts and dispositions.
- `docs/reviews/m6i_risk_coverage_matrix.csv` updated with M6J ownership notes.

## Tests retired

| retired_test_or_assertion | risk_id | authoritative_owner | semantic_equivalence | why_safe |
|---|---|---|---|---|
| `tests/unit/test_m5fgh_frontend_static.py::test_frontend_static_uses_m5f_and_safe_dom` | `frontend_historical_m5f_static_preview` | `tests/unit/test_m5f_canonical_market_context_package.py`; `tests/unit/test_frontend_readonly_contract_static.py`; `tests/unit/test_frontend_readonly_static_contracts.py`; `scripts/forbidden_behavior_scanner.py`; `tests/test_m6g_browser_operator_e2e.py` | partial | The retired assertion was a historical static preview wrapper. Canonical ownership remains with M5F tests; frontend static wording remains with readonly static contract tests and scanner coverage; real frontend/operator behavior remains with M6G. |
| `tests/unit/test_frontend_readonly_static_contracts.py::test_no_frontend_public_changed` | `frontend_public_write_guard` | `tests/unit/test_no_frontend_public_write_guard.py` | true | The assertion was tautological because `or True` made it unable to fail. The dedicated public-write guard owns forbidden frontend/public path detection. |
| `tests/unit/test_m5c_controlled_staging_promotion.py::test_m5c_controlled_check_only_passes_before_execution_or_blocks_after_single_use` | `m5c_historical_check_only_wrapper` | `tests/unit/test_m5c_staging_promotion.py::test_one_command_preflight_shape`; `tests/unit/test_m5c_staging_promotion.py::test_preflight_success_whitelist_rejects_simulation_failed` | partial | The retired test was a low-signal milestone-state wrapper that allowed either clean pre-execution or already-consumed/destination-exists state. Focused M5C preflight shape and success-whitelist owners still protect fail-closed promotion semantics. |

## Assertions retired

- Historical M5FGH static preview token assertions for pinned M5F path, manifest tokens, textContent use, and no refresh wording.
- One tautological frontend/public absence assertion.
- One historical M5C check-only wrapper assertion accepting either pass or already-consumed/destination-exists state.

## Authoritative owners used

- M5F canonical package tests and validator remain the canonical schema owner.
- `tests/unit/test_no_frontend_public_write_guard.py` remains the frontend/public write owner.
- `scripts/forbidden_behavior_scanner.py` remains authoritative for forbidden trading language and raw payload leakage scan coverage.
- M6G browser/operator E2E remains the real frontend/operator journey owner.
- `tests/unit/test_m5c_staging_promotion.py` remains the M5C staging package/preflight owner.

## Risks preserved

- M5F canonical package validation and schema validation.
- Observation is not canonical.
- Bounded watchlist only and no full-market scan.
- Raw payload leakage guards.
- No trading recommendation, ranking, target price, buy, sell, or hold output.
- Frontend public write guard.
- Strict TLS default, explicit compatibility opt-in, and no silent TLS fallback.
- FastAPI/MCP invalid `ssl_policy` fail-closed behavior.
- M6E operator/release acceptance.
- M6G browser/operator E2E and evidence semantics.
- M5K observation semantics, M5Q source-health semantics, and M5N Conversation Package semantics.
- Unique crash recovery, tamper detection, rollback, and failure injection tests.

## Risks intentionally not touched

- M5F canonical tests.
- Watchlist validation and invalid watchlist fail-closed tests.
- Snapshot, briefing, watchlist observation, and AI context pack transformation tests.
- M5E publication transaction, crash recovery, symlink, schema, and failure injection tests.
- SSL policy matrix and FastAPI/MCP invalid policy tests.
- M6E and M6G tests.
- Unique M5B/M5C tamper, rollback, authorization, and failure injection tests.

## Remaining duplicate candidates

See `docs/reviews/m6j_duplicate_risk_map.csv`. The main deferred areas are M5E preview static strings, M5C supplemental historical audit validation, and additional frontend static/operator overlap where semantic equivalence is only partial.

## Evidence policy

M6G was run in check-only mode only. The first check-only run reported missing Playwright, so browser dependencies were installed with `python -m pip install -r requirements-browser-e2e.txt` and `python -m playwright install --with-deps chromium`; the rerun passed. No bounded-live execution was run by this task. Generated M6E/M6G/conversation evidence artifacts were restored to their pre-task checked-in state after validation so M6J does not commit acceptance-run evidence churn.
