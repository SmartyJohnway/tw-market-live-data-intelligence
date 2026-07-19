# M8R EOD Expected Trade Date and Session Status Walkthrough

## 1. Summary of Changes

We have fully hardened the expected EOD trade date evaluator, resolved all review blocker items from PR #159, and implemented a robust runtime official calendar provider and caching system.

### Core Modules
- **[m8r_eod_expected_trade_date.py](scripts/m8r_eod_expected_trade_date.py) [MODIFY]**: 
  - Implements strict early YYYY-MM-DD pattern verification (overriding loose parses in Python 3.11+) and returns `invalid_trade_date_format` immediately on failure.
  - Implements the fail-closed unresolved rule: forces `currentness_status` to `"calendar_status_unresolved"` if calendar or closure data is unresolved, storing the provisional heuristical status under `"provisional_candidate_status"`.
  - Declares the TAIFEX provisional day-session policy caveat.
- **[m8r_03d_watchlist_controlled_executor.py](scripts/m8r_03d_watchlist_controlled_executor.py) [MODIFY]**: 
  - Implements a runtime production calendar fetcher (`_load_production_calendar`) that pulls official TWSE holidaySchedule, Normalizes it via `build_twse_trading_calendar_from_holiday_schedule`, and writes it to a sandbox/artifacts cache.
- **[m8r_03d_watchlist_source_integration.py](scripts/m8r_03d_watchlist_source_integration.py) [MODIFY]**: 
  - Restructured to preserve `detailed_status` and `provisional_candidate_status` inside the verified watchlist results instead of flat legacy status mappings.

### Schemas
- **[m8r_eod_expected_trade_date_status.schema.json](schemas/m8r_eod_expected_trade_date_status.schema.json) [MODIFY]**:
  - Exposes `provisional_candidate_status` to the JSON schema validation properties.

---

## 2. Test Parity & Verification

We expanded the testing matrix:
- **[test_m8r_eod_expected_trade_date.py](tests/unit/test_m8r_eod_expected_trade_date.py) [MODIFY]**:
  - Added pre-market and mid-market tests with unresolved inputs to verify forced fallback to `calendar_status_unresolved`.
  - Added strict date formatting boundary tests (e.g. `2026-7-2`, `20260721`, empty strings) to verify strict format validation.
- **[test_m8r_03d_production_calendar_integration.py](tests/unit/test_m8r_03d_production_calendar_integration.py) [NEW]**:
  - Verifies dynamic production calendar loading, cached file write assertions, and network failure fallback logic under Phase C request policies.

All targeted tests and existing pipeline checks passed successfully:
```bash
.venv\Scripts\pytest tests/unit/test_m8a_market_day_currentness_resolver.py tests/unit/test_m8a_ncdr_dgpa_closure_cap.py tests/unit/test_m8r_eod_expected_trade_date.py tests/unit/test_m8r_03d_production_calendar_integration.py
```
> **100% Passed (35 tests)**
