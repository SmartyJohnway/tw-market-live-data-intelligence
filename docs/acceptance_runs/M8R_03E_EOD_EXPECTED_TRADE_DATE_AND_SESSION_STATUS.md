# M8R-03E EOD Expected Trade Date and Session Status Verification Report

## 1. Overview
- **Task ID**: `M8R-03E-EOD-EXPECTED-TRADE-DATE-AND-NATURAL-DISASTER-SESSION-STATUS`
- **Focus**: expected-trade-date correctness + Taiwan market session-status determination + natural-disaster closure integration + Windows compatibility hardening.
- **Successor**: `M8R-05A-UNIFIED-MARKET-EVIDENCE-CONTRACT-AND-CAPABILITY-CATALOG`

---

## 2. Test Matrix Coverage (A to M)

We created a new comprehensive test suite [test_m8r_eod_expected_trade_date.py](tests/unit/test_m8r_eod_expected_trade_date.py) that covers the entire 13-case matrix:
- **A. Monday Pre-Market**: Asserts `official_previous_session_eod_before_close`.
- **B. Mid-Market**: Asserts `official_previous_session_eod_before_close`.
- **C. Post-Market Updated**: Asserts `official_latest_completed_eod` when today is updated.
- **D. Post-Market Grace**: Asserts `not_yet_published_after_close` within the 60-minute grace window.
- **E. Post-Market Stale**: Asserts `unexpected_stale_eod` past grace window.
- **F. Weekend**: Asserts weekend classification.
- **G. Official Holiday**: Asserts official holiday classification.
- **H. Taipei Full-Day Closure**: Asserts `market_closed_no_session` when typhoon day is active.
- **I. Taipei Morning-Only Closure**: Asserts `market_closed_no_session` (cancelled session).
- **J. Taipei Afternoon-Only Closure**: Asserts session remains valid.
- **K. Closure Unresolved**: Asserts fallback to provisional age check.
- **L. Future Trade Date**: Asserts `future_trade_date_invalid` when actual is newer than expected.
- **M. Cross-Market**: Validates TAIFEX (close at 13:45) vs TWSE/TPEX (close at 13:30).

All 14 tests in this suite passed successfully.

---

## 3. Targeted Test Executions

We verified that both the new and historical targeted test suites pass 100%:
1. `tests/unit/test_m8r_eod_expected_trade_date.py` (14/14 passed)
2. `tests/unit/test_m8a_market_day_currentness_resolver.py` (7/7 passed)
3. `tests/unit/test_m8a_ncdr_dgpa_closure_cap.py` (10/10 passed)

---

## 4. Windows Compatibility & Robustness Fixes

To achieve a clean execution environment on Windows, we identified and successfully resolved several cross-platform bugs:
1. **Windows CP950 Decode Error**: Added `encoding="utf-8"` in `test_m8a_ncdr_dgpa_closure_cap.py` and `test_m8a_twse_official_eod_adapter.py` when reading UTF-8 JSON/XML fixtures.
2. **Path separator (`\` vs `/`) Mismatches**: Modified path matching in `validate_m5c_staging_promotion_request.py`, `test_m8a_official_eod_instrument_classification.py`, and `test_m7b_ai_safe_market_context_projection_builder.py` to be platform-independent.
3. **Outdated CI Filename Assertion**: Restored assertion parity in `test_workflow_policy_matrix.py` to match the non-network CI runner updated in PR #158.
4. **Hardcoded `/tmp` Paths**: Replaced hardcoded Linux paths in `test_m8r_03d_f1_verified_security_master_snapshot.py` with pytest's `tmp_path` fixture.
