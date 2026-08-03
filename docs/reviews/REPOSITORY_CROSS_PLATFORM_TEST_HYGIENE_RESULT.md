# Repository Cross-Platform Test Hygiene Result

## Status
Passed

## Tested Identity and Environment
- **Baseline SHA:** `e00193d0c1719bbdbd3eea2ed9f0f21c0fd23388`
- **Environment:** Linux (Ubuntu), Python 3.12.13, Pytest 9.1.1, ext4, UTF-8 default.
- **Note:** Linux verification passed with explicit UTF-8 handling. Windows-specific CP950 failures were addressed by code changes derived from prior evidence, but Windows rerun was not performed in this PR.

## Files Changed
10 files bounded specifically to the 20 failures and the 1 import fix:
- `scripts/run_m5c_controlled_staging_promotion.py`
- `tests/unit/test_frontend_readonly_static_contracts.py`
- `tests/unit/test_m5c_staging_failure_injection.py`
- `tests/unit/test_m5c_staging_promotion.py`
- `tests/unit/test_m5e_controlled_frontend_publication.py`
- `tests/unit/test_m5fgh_consumer_consistency.py`
- `tests/unit/test_m5fgh_frontend_static.py`
- `tests/unit/test_m8_controlled_conversation_context_integration.py`
- `tests/unit/test_m8a_tpex_official_eod_adapter.py`
- `tests/unit/test_m8b_final_acceptance.py`

## UTF-8 Normalization Changes
- Replaced implicit `.read_text()` with `.read_text(encoding="utf-8")`
- Replaced implicit `.write_text(...)` with `.write_text(..., encoding="utf-8")`
- Targeted exclusively to the files responsible for the environmental failures.

## Import-Path Changes
- Rewrote ad-hoc relative imports for `validate_m5c_staging_promotion_authorization` into absolute `scripts.` module imports within `run_m5c_controlled_staging_promotion.py`.

## Path-Normalization Changes
None needed for these 20 failures (all were encoding or import issues).

## Targeted Failure Results
- All 20 target failures (environment/state-induced) passed.

## Full Non-Network Before and After
- **Before:** 2053 passed, 43 failed
- **After:** 2089 passed, 12 failed (0 novel failures; 31 total resolved including 11 incidental historical failures)

## M8R Regression Results
- **M8R-05B-03:** 108 passed
- **M8R-05B-02:** 55 passed
- **M8R-05B-01:** 58 passed
- **Fixed Upstream Gate:** 44 passed

## Retained Failures
12 historical retained failures (from M8R-05A-F3 and M8R-02B) remain explicitly unresolved and out of scope.

## Unresolved Failures
None of the 20 targets remain unresolved.

## Novel Failures
0

## Boundary Confirmations
- **No live network execution occurred.**
- **No production semantics changed.**
- **M8R-05C was not started.**
- **No accepted evidence schemas were altered.**

## Caveats
Windows rerun was not explicitly performed in this PR. Fixes were verified on Linux.

## Final Decision
Approved. Recommend merging PR-B and starting M8R-05C.
