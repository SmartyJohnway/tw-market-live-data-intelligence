# M6H Test Portfolio Rationalization and E2E Prioritization

## Contract alignment

M6H inspected and reuses the existing README, dependency files, pytest markers, governance/API/output references, operator docs, M6A/M6B/M6D/M6E/M6F/M6G review records, M6E/M6G/operator/M6B/M5K/M5N scripts, TLS policy helper, FastAPI/MCP entry points, readonly frontend, current tests, and M5K/M6G evidence artifacts. No parallel watchlist, observation, source-health, conversation, TLS, or test-taxonomy contract is introduced.

Preserved semantics: M5F is canonical Level 1; M5K/M5L are bounded Level 2 observation; M5Q is source-health evidence; M5N is the Conversation Package; observation is not canonical; reference-only is not current price; `stale_or_closed_session` is degraded; strict TLS remains default; explicit request/query SSL policy precedes `TW_MARKET_SSL_POLICY`; compatibility and unsafe-explicit TLS are explicit opt-in; no silent TLS fallback; no trading output, recommendation, ranking, target price, polling, scheduler, startup network call, or full-market scan.

## Test portfolio inventory

Full inventory is in [`m6h_test_inventory.csv`](m6h_test_inventory.csv). It classifies 116 Python test files and approximately 673 direct `test_*` functions. The reported historical count above 700 is credible because parametrized tests and generated case matrices expand the direct function count at runtime. The portfolio grew because prior milestones added milestone-specific regression tests, source-contract tests, governance scans, artifact-schema checks, FastAPI/MCP checks, frontend static-contract checks, and operator acceptance tests without a formal consolidation gate.

The inventory classification method follows actual execution requirements, not keyword mentions. A deterministic non-network test is not Tier 3 merely because it validates live-related fields, mocks a live source, or contains the word `live`. Tier 3 is reserved for real browser/Playwright execution requirements, actual external network or bounded live execution, OS/runtime-specific validation, real TLS handshakes, and cold-clone acceptance. Tier 2 covers operator acceptance, release preflight, cross-component integration, artifact/package validation, FastAPI TestClient/MCP/operator workflow checks, and check-only acceptance workflows. Tier 1 covers deterministic default-CI-suitable unit/mock/contract/governance/static safety tests.

Repaired approximate distribution by actual execution requirement:

| Tier | Files | Direct `test_*` functions | Execution requirement |
|---|---:|---:|---|
| Tier 1 | 97 | 525 | deterministic, default-CI-suitable, non-network, no real browser |
| Tier 2 | 17 | 136 | operator/release, cross-component, artifact/package, FastAPI TestClient/MCP/check-only workflow |
| Tier 3 | 2 | 12 | real browser marker/Playwright path or network-marked bounded live integration |

The repaired inventory reclassified 43 files that were previously false Tier 3 candidates due to keyword heuristics. Corrected examples include `tests/test_generate_ai_context_pack.py`, `tests/test_generate_chatgpt_briefing.py`, `tests/test_generate_latest_market_snapshot.py`, `tests/test_generate_watchlist_observations.py`, and `tests/unit/test_forbidden_behavior_scanner.py` as Tier 1 deterministic non-network tests; `tests/test_m5q_source_health.py` and `tests/test_m6e_operator_acceptance.py` as Tier 2 check-only/cross-component acceptance tests; and only `tests/test_m6g_browser_operator_e2e.py` plus `tests/integration/test_m6b_live_source_contract.py` as Tier 3 based on actual browser/network execution requirements.

## Formal three-tier test portfolio

### Tier 1 — Default CI / fast / deterministic / non-network

Command: `pytest -m "not network" -v`.

Purpose: fast, deterministic, non-network, high-signal protection for core safety, normalization, schema, dirty-data handling, watchlist validation, fail-closed behavior, forbidden behavior, canonical schema validation, critical API contracts, critical SSL policy resolution, and governance boundaries.

Protects against schema corruption, unsafe behavior, bad normalization, invalid watchlist acceptance, silent TLS policy downgrade, canonical mutation, raw payload leakage, and trading semantic leakage. It intentionally does not prove real browser DOM behavior, real FastAPI process communication, Chromium fetch behavior, exchange TLS handshakes, live source availability, or cold-clone usability.

Candidate tests: core non-network tests under `tests/` that do not require Playwright, live network, OS-specific browser dependencies, or release artifacts beyond checked-in fixtures.

### Tier 2 — Operator acceptance / release preflight / integration

Purpose: cross-component validation, operator workflow validation, artifact validation, and release readiness.

Expected workflows: M6B source contract preflight check-only, M6E operator acceptance, M5F validation, M5IJ acceptance, M5K postmerge validation, M5Q source-health check-only, M5N conversation package build, FastAPI TestClient integration, MCP startup checks, and operator preflight.

Protects against cross-module contract mismatch, missing artifacts, operator command drift, Conversation Package breakage, FastAPI/MCP integration regressions, and release preflight regressions. Tier 2 does not replace real browser E2E.

### Tier 3 — Browser / bounded live / OS-specific / cold clone

Purpose: prove real operator journeys, actual browser behavior, local-process integration, external source compatibility, real TLS/runtime behavior, and cold-clone usability.

Expected workflows: Playwright browser E2E, M6G check-only, M6G explicit bounded live, Windows/Python 3.13 validation, real TLS handshake validation, release-time bounded source checks, and cold-clone operator acceptance.

Protects against frontend DOM payload defects such as missing watchlist `id`, browser fetch/CORS failure, frontend/API mismatch, local FastAPI connectivity failure, real Chromium behavior, TLS certificate/runtime compatibility, environment-specific failures, and operator bootstrap failure. These are exactly the risks that large mock/static portfolios may miss.

## Rationalization baseline

### Tests to preserve

Preserve Tier 1 tests that guard canonical schema, normalization, dirty data, watchlist validation, fail-closed behavior, forbidden behavior, SSL policy precedence, no raw payload leakage, and no trading semantics. Preserve Tier 2 operator/release scripts and Tier 3 M6G browser/live acceptance because they protect operator journeys that unit/static tests cannot prove.

### Tests to consolidate later

Actual candidate families from the inventory:

| Candidate family | Current files | Overlap | Protected risk | Why consolidation may be safe | Recommended shared suite | Tier |
|---|---|---|---|---|---|---|
| Static frontend string/governance assertions | `tests/test_m6a_frontend_compatibility.py`, `tests/test_m6e_operator_acceptance.py`, `tests/test_m6g_browser_operator_e2e.py`, workbench-related tests | Repeated checks for no polling, no trading text, local API guidance, watchlist/frontend strings | Governance and frontend contract drift | One helper can scan the readonly frontend for forbidden and required strings while M6G proves real DOM behavior | `tests/helpers/frontend_contract.py` plus one static contract file | Tier 1, with Tier 3 E2E evidence |
| Endpoint existence and TestClient schema checks | API/MCP/server-oriented test files | Repeated `TestClient` endpoint status/schema assertions | FastAPI readonly API contract | A route/schema manifest helper can reduce repeated boilerplate without weakening endpoint coverage | `tests/helpers/api_contract.py` | Tier 1/Tier 2 |
| Report schema key enumeration | M6B/M6E/M6G/M5K/M5Q artifact tests | Repeated key-presence assertions for report JSON/Markdown artifacts | Operator artifact readability and contract stability | Shared report-schema helpers can preserve milestone-specific required fields while reducing copy/paste | `tests/helpers/report_contract.py` | Tier 2/Tier 3 |
| Forbidden-field scans | Governance and artifact tests plus scanners | Repeated searches for buy/sell/hold/ranking/target/recommendation/raw payload leakage | Governance boundary | Keep scanners authoritative; reduce duplicate per-file forbidden scans where scanners already cover the same artifact set | Existing scanner scripts with focused regression tests | Tier 1/Tier 2 |
| No-network monkeypatch patterns | Source contract, M5K/M5Q/M6B/M6E tests | Repeated network-block monkeypatches | Default CI network safety | A shared network-deny fixture can make intent clearer and reduce repeated monkeypatch code | `tests/conftest.py` fixture or helper | Tier 1 |
| Artifact-path allowlists | Output artifact/governance tests | Repeated path allowlist checks | Avoid writes to canonical/generated/prod paths | A centralized allowed-write-path helper can reduce drift | `tests/helpers/artifact_paths.py` | Tier 1/Tier 2 |
| SSL policy matrix assertions | M6D/M6F/API/M6G tests | Repeated strict/compatibility/unsafe precedence cases | No silent TLS downgrade and explicit env/query precedence | Preserve core matrix once and keep one API integration regression for env fallback | Shared parameter table in SSL tests | Tier 1/Tier 2 |

### Tests to demote from default CI later

Demote only after replacement evidence exists: long artifact enumeration tests that duplicate a shared schema contract, historical milestone-specific static checks superseded by stable shared contracts, and integration-like tests that are really operator workflow checks rather than unit contracts. Do not demote fail-closed, governance, schema, or SSL policy core tests merely to reduce count.

### Tests to replace or supersede with E2E evidence later

Static/frontend tests that attempt to infer real DOM behavior, frontend/API compatibility, actual fetch/CORS behavior, and local-process browser connectivity should eventually be superseded by M6G browser/operator evidence while retaining a minimal static governance contract.

No tests were deleted in M6H. No mass deletion was performed.

## E2E prioritization policy

Do not optimize for test count. Optimize for operator journey coverage and risk coverage.

Future tests must answer: what unique risk is protected; whether the risk is already covered; whether the test is an exact or near duplicate; whether unit/mock is the correct level; whether integration or browser E2E provides stronger evidence; which tier owns it; whether it belongs in every CI run; whether it relies on external sources; and whether it increases operator journey coverage.

High-value operator journeys:

1. **Workbench Boot E2E** — FastAPI starts, frontend loads, frontend connects to local API, and the operator sees usable workbench state.
2. **Watchlist Validate / Plan E2E** — default watchlist loads, DOM rows are reconstructed, frontend generates watchlist payload, required `id` exists, validate succeeds, and plan succeeds.
3. **Explicit Bounded Live Observation E2E** — operator explicitly requests live observation, confirmation is required, bounded watchlist is used, observation executes, result renders, no polling occurs, and no unexpected execute occurs.
4. **TLS Compatibility E2E** — strict default remains intact, compatibility is explicit, the real environment can perform required source TLS handshake when compatibility is selected, and no silent fallback occurs.
5. **Conversation Package E2E** — observation evidence exists, M5N builds, canonical and observation semantics remain separated, AI handoff is readable, and raw payload leakage does not occur.
6. **Cold Clone Operator Acceptance** — fresh clone, dependency installation, diagnostics, local workbench start, browser load, validate/plan, optional explicit bounded live, and Conversation Package generation.

## Browser/E2E dependency contract

`requirements-browser-e2e.txt` contains core dependencies plus Playwright. Keep Playwright out of `requirements.txt` so the core local workbench remains lightweight.

Readiness has three layers: Python Playwright package, Chromium browser binary, and OS/system browser dependencies. A successful `pip install playwright` alone does not prove browser E2E readiness.

Bootstrap:

- Windows/macOS: `python -m pip install -r requirements-browser-e2e.txt`; `python -m playwright install chromium`.
- Linux/Codex/CI-like: `python -m pip install -r requirements-browser-e2e.txt`; `python -m playwright install --with-deps chromium`.
- If browser binaries already exist but OS dependencies are missing: `python -m playwright install-deps chromium`.

M6G remains an acceptance runner, not a package installer. `scripts/run_m6g_browser_operator_e2e.py` must not auto-install Python packages, Chromium, OS dependencies, invoke apt/sudo, or otherwise mutate system dependency state.

Do not immediately accept `skipped_with_caveats` merely because Playwright or Chromium is initially unavailable. Before declaring browser E2E unavailable, investigate or attempt Python Playwright availability, Chromium binary availability, OS dependency readiness, and a supported install path. A skip report must record the dependency step attempted, command attempted, blocking error, environment limitation, and recommended next action.

## Commit 3 targeted consolidation

Commit 3 performed a small targeted consolidation after the M6H inventory repair. No product behavior, source adapter, M5F, observation, source-health, conversation, TLS, M6E, or M6G semantics were changed. No mass deletion was performed.

Files changed for consolidation:

- `tests/unit/test_m6a_observation_ux.py`
- `tests/unit/test_m6d_operator_and_local_networking.py`
- `tests/test_m6e_operator_acceptance.py`
- `tests/test_m6g_browser_operator_e2e.py`
- `docs/reviews/m6h_test_inventory.csv`

Tests removed or merged:

| Area | Previous tests | Consolidated test | Direct-count reduction | Coverage replacement | Why safe |
|---|---|---|---:|---|---|
| Static frontend/operator strings and forbidden static assertions | `test_frontend_local_api_detection_contract_strings`, `test_frontend_watchlist_import_export_multiple_slots_contract`, `test_frontend_history_diff_timeline_source_health_conversation_contract`, `test_frontend_no_startup_observation_execution_or_polling_loop`, `test_frontend_no_forbidden_trading_language_or_raw_payload_leakage` | `test_frontend_static_operator_contract_strings` | 4 | All prior string, no-polling, no-startup-execute, raw payload, and forbidden static assertions remain in one grouped frontend contract test. | These were repeated static frontend contract scans over the same JS/HTML strings. |
| Observation-count degraded closed-session cases | `test_observation_counts_treat_stale_or_closed_session_ok_rows_as_degraded`, `test_observation_counts_treat_closed_session_caveat_as_degraded` | `test_observation_counts_treat_closed_session_rows_as_degraded` | 1 | Both stale/freshness and caveat-driven degraded cases remain asserted. | Same helper and same expected degraded outcome. |
| FastAPI SSL policy API assertions | `test_fastapi_invalid_ssl_policy_returns_400_without_execution`, `test_fastapi_valid_ssl_policy_values_are_accepted` | `test_fastapi_ssl_policy_fail_closed_and_valid_values` | 1 | Invalid policy fail-closed/no-execute and strict/compatibility/unsafe accepted cases remain asserted. | Same endpoint and same minimal watchlist fixture. |
| MCP SSL policy assertions | `test_mcp_invalid_ssl_policy_fails_closed_without_network_or_writes`, `test_mcp_valid_ssl_policy_values_are_accepted` | `test_mcp_ssl_policy_fail_closed_and_valid_values` | 1 | Invalid fail-closed/no-network/no-write and strict/compatibility/unsafe accepted cases remain asserted. | Same MCP tool and same minimal watchlist fixture. |
| M6E operator preflight caveat extraction | `test_run_json_propagates_operator_preflight_caveats`, `test_run_json_extracts_nested_operator_preflight_caveats` | `test_run_json_propagates_operator_preflight_caveats` | 1 | Top-level and nested operator preflight caveat extraction paths remain asserted. | Same `run_json` behavior with two mocked subprocess outputs. |
| M6E invalid SSL policy acceptance | `test_fastapi_invalid_ssl_policy_acceptance`, `test_mcp_invalid_ssl_policy_acceptance` | `test_invalid_ssl_policy_acceptance_surfaces_fail_closed` | 1 | FastAPI invalid policy 400, missing confirmation 400, and MCP invalid fail-closed/no-network remain asserted. | Same default watchlist and same fail-closed boundary. |
| M6G successful next-step guidance | `test_recommended_next_steps_for_pass_check_only_omit_dependency_install`, `test_recommended_next_steps_for_pass_bounded_live_omit_dependency_install` | `test_recommended_next_steps_for_successful_browser_runs_omit_dependency_install` | 1 | Check-only and bounded-live success cases both still assert no install guidance and correct evidence guidance. | Same helper and same invariant for successful browser runs. |
| M6G live SSL env selection | `test_live_strict_does_not_set_compatibility_env`, `test_live_compatibility_sets_explicit_env` | `test_live_ssl_policy_env_selection_for_strict_and_compatibility` | 1 | Strict default/no env override and compatibility env override both remain asserted. | Same mocked browser path and same TLS precedence boundary. |

Approximate direct test count before Commit 3 consolidation was 684 direct `test_*` functions after the previous M6G next-step regression additions. The count after consolidation is 673 direct `test_*` functions, a net reduction of 11 direct tests. Pytest collection remains higher because parametrized tests expand at runtime.

Coverage preserved:

- Governance and forbidden behavior scanners remain intact.
- No trading semantics and raw payload leakage guards remain asserted.
- SSL strict/default/env/query precedence and invalid-policy fail-closed coverage remains asserted.
- FastAPI and MCP invalid `ssl_policy` fail-closed checks remain asserted.
- M6E operator acceptance remains covered.
- M6G browser/operator E2E and bounded-live evidence remain covered.
- M5F canonical validation, M5K observation semantics, and M5N conversation semantics were not weakened or removed.

Remaining future consolidation candidates are unchanged: shared helpers for broader frontend contract scans, report schema validation, artifact-path allowlists, forbidden-field scans already covered by authoritative scanner scripts, and shared SSL policy matrices. Those candidates require separate focused review and were not mass-deleted in Commit 3.

## M6G evidence preserved

### Successful check-only evidence

After browser bootstrap, M6G check-only passed with Playwright available, FastAPI started, frontend loaded, watchlist payload checked, 19 watchlist items checked, id generation passed, validate passed, plan passed, execute not executed, zero unexpected execute requests, no polling, no network calls, strict requested SSL policy, no effective server env SSL policy, default browser execute SSL policy source, and strict SSL policy. This proves local FastAPI and headless Chromium start, real frontend/DOM operations run, validate/plan requests are captured, watchlist item id generation works, check-only does not execute live observation, no polling occurs, strict default is preserved, and compatibility env override is not silently applied.

### Successful bounded live evidence

M6G bounded live browser/operator E2E passed in this task with `python scripts/run_m6g_browser_operator_e2e.py --execute-bounded-live-check --ssl-policy compatibility`. The actual browser path executed; the frontend generated the watchlist payload; validate and plan succeeded; explicit execute succeeded; no API fallback was used; no unexpected execute occurred; no polling occurred; compatibility TLS was explicitly selected; the temporary FastAPI process received compatibility through `TW_MARKET_SSL_POLICY`; the live observation remained bounded; and M5K latest observation was updated by explicit bounded live execution.

Targets: `0050`, `00878`, `00919`, `00929`, `00934`, `00939`, `00940`, `00981A`, `1569`, `2317`, `2324`, `2330`, `2603`, `2609`, `3293`, `3483`, `3543`, `TAIEX`, `TX`.

Committed evidence artifacts:

- `research/live_observation_runs/m5k/latest_observation.json`
- `research/live_observation_runs/m6g_browser_operator_e2e/latest_browser_operator_e2e_report.json`
- `research/live_observation_runs/m6g_browser_operator_e2e/latest_browser_operator_e2e_report.md`

This is observation evidence, not canonical data. M5F was not mutated. No full-market scan occurred. No trading signal was produced.
