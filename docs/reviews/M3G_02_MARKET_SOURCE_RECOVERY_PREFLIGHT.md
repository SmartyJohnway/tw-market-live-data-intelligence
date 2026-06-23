# M3G-02-MARKET-SOURCE-RECOVERY-PREFLIGHT Completion Report

## 1. Final Status

M3G_02_COMPLETED_WITH_CAVEATS_READY_FOR_M3G_03

## 2. Baseline Merge SHA

5ac0e71ef79ce5ba8b9702211fc84c394570a6ac (PR #33 merged)

## 3. Files Inspected

*   `research/generated/latest_market_snapshot.json`
*   `research/generated/watchlist_observations.json`
*   `research/generated/ai_context_pack.json`
*   `research/generated/chatgpt_briefing.md`
*   `config/market_targets.json`
*   `README.md`
*   `docs/reviews/M3G_01_RELEASE_TAG_ARTIFACT_REFRESH_AND_FRONTEND_REVALIDATION.md`

## 4. Files Changed

*   `docs/protocol/M3G_SOURCE_RECOVERY_PLAN.md`
*   `docs/reviews/M3G_02_MARKET_SOURCE_RECOVERY_PREFLIGHT.md`
*   `README.md`

## 5. Confirmation no live probes were run

Confirmed. No live probes or network scripts (e.g., `scripts/run_all_probes.py`) were executed during this preflight.

## 6. Confirmation no generated artifacts were modified

Confirmed. All files under `research/generated/*` remain untouched and reflect the previous merged state.

## 7. Confirmation no frontend files were modified

Confirmed. No files under `frontend/public/*` were modified.

## 8. Confirmation no source recovery was performed

Confirmed. This milestone strictly focused on planning and inventory. No code was altered to recover the sources.

## 9. Current artifact failure inventory

Based on the inspection of `research/generated/latest_market_snapshot.json`:

*   All 10 bounded watchlist symbols (`2330`, `1435`, `8069`, `5347`, `0050`, `00929`, `9105`, `TAIEX`, `TX`, `FUNDA`) are currently listed in `failed_symbols` due to `all_sources_failed`.
*   The primary canonical sources (`TWSE_MIS`, `Yahoo_Finance`, `TWSE_OpenAPI`, `TPEx_OpenAPI`) are failing with the error `offline_mode_no_local_input`.
*   `FinMind` is not attempted (`not_attempted_offline_default`).
*   Broker sources (`Fugle`, `Fubon`) are skipped (`auth_required_doc_only_skipped`).

## 10. Per-source recovery classification

*   **TWSE_MIS**: `mock_fixture_recovery_candidate`
*   **Yahoo_Finance**: `third_party_context_candidate`
*   **TWSE_OpenAPI**: `official_eod_reference_candidate`
*   **TPEx_OpenAPI**: `official_eod_reference_candidate`
*   **FinMind**: `doc_only_deferred`
*   **Fugle**: `auth_required_deferred`
*   **Fubon**: `auth_required_deferred`

*Detailed classification is available in `docs/protocol/M3G_SOURCE_RECOVERY_PLAN.md`.*

## 11. Mock fixture strategy summary

The strategy mandates the creation of local mock files in `tests/fixtures/market_sources/` to enable deterministic testing without network calls. Mocks will cover at least the core bounded symbols. Generators will remain unchanged for production but will support parameter-level or `pytest monkeypatch` injection of mocks during tests to verify parser contracts and ensure non-empty artifact generation.

## 12. Controlled live probe preflight summary

Controlled live probes must be carefully authorized following a strict ladder (LEVEL_0 through LEVEL_4). Live probes must adhere to bounded watchlist limits, strictly handle timeouts/rate limits, and emphatically reject any generation of trading signals, rankings, or real-time coverage claims.

## 13. Source authority risk summary

Official EOD sources (OpenAPI) are safe but delayed. Unofficial endpoints (TWSE_MIS) present a medium risk due to fragility and rate limits. Third-party APIs (Yahoo) are low-risk context but lack official authority. Broker APIs present a blocked risk due to authentication and execution proximity.

## 14. Frontend impact summary

The frontend is currently rendering the offline/failed state. Recovering sources via mocks (and later live probes) will populate the frontend context tables with valid data instead of failure flags. The frontend must continue to display the caveats (e.g., "offline mode" when applicable, or bounded watchlist warnings).

## 15. Recommended M3G-03 execution level

**LEVEL_1 mock fixture and parser contract repair**

## 16. Recommended M3G-03 task list

1.  Create mock JSON/HTML response files for `TWSE_MIS`, `TWSE_OpenAPI`, `TPEx_OpenAPI`, and `Yahoo_Finance` covering the bounded watchlist in `tests/fixtures/market_sources/`.
2.  Update tests to inject these mock fixtures into the parser functions.
3.  Verify that running the test suite generates non-empty data contracts.
4.  Do not attempt LEVEL_2 (live probes) until LEVEL_1 is proven stable.

## 17. Remaining caveats

*   The generated artifacts still represent an empty/offline state.
*   Broker and authentication-required sources remain explicitly out of scope.
*   No full-market coverage is available.

## 18. Validation commands and results

```bash
python -m compileall scripts server tests
```
*Result: Succeeded. All files compiled.*

```bash
pytest -m "not network" -v
```
*Result: Succeeded. All 14 tests passed (2 warnings about pytest config).*

## 19. Recommended next milestone

M3G-03-CONTROLLED-MARKET-SOURCE-PROBE-REPAIR (LEVEL_1 mock fixture and parser contract repair first)