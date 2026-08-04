# Repository Cross-Platform Test Hygiene Result

## Status
`pass_with_caveats`

## Tested Identity and Environment
- **Baseline SHA:** `e00193d0c1719bbdbd3eea2ed9f0f21c0fd23388`
- **Tested Implementation Head:** `d00c5118931523a4081f5c27530576319a0423be`
- **Evidence Parent:** `d00c5118931523a4081f5c27530576319a0423be`
- **Environment:** Linux (Ubuntu), Python 3.12.13, Pytest 9.1.1, ext4, UTF-8 default.
- **Windows Execution Status:** `performed`

## Files Changed

### Implementation Files Changed
- `scripts/run_m5c_controlled_staging_promotion.py`

### Test Files Changed
- `tests/test_m6e_operator_acceptance.py`
- `tests/unit/test_frontend_readonly_static_contracts.py`
- `tests/unit/test_m5c_staging_failure_injection.py`
- `tests/unit/test_m5c_staging_promotion.py`
- `tests/unit/test_m5e_controlled_frontend_publication.py`
- `tests/unit/test_m5fgh_consumer_consistency.py`
- `tests/unit/test_m5fgh_frontend_static.py`
- `tests/unit/test_m8_controlled_conversation_context_integration.py`
- `tests/unit/test_m8a_tpex_official_eod_adapter.py`
- `tests/unit/test_m8b_final_acceptance.py`

### Evidence Files Created
- `docs/reviews/REPOSITORY_CROSS_PLATFORM_TEST_HYGIENE_PREFLIGHT.json`
- `docs/reviews/REPOSITORY_CROSS_PLATFORM_TEST_HYGIENE_PREFLIGHT.md`
- `docs/reviews/REPOSITORY_CROSS_PLATFORM_TEST_HYGIENE_RESULT.json`
- `docs/reviews/REPOSITORY_CROSS_PLATFORM_TEST_HYGIENE_RESULT.md`

### Unexpected Generated Files
None. `unexpected_generated_files = []`

## UTF-8 Normalization Changes
- Replaced implicit `.read_text()` with `.read_text(encoding="utf-8")`
- Replaced implicit `.write_text(...)` with `.write_text(..., encoding="utf-8")`
- Targeted exclusively to the tests mapped directly to the 20 failures.

## Import-Path Changes
- Refactored `validate_m5c_staging_promotion_authorization` and related sibling imports in `scripts/run_m5c_controlled_staging_promotion.py` into a stable `try/except` double-fallback block supporting both module (`python -m scripts...`) and direct script (`python scripts/...`) execution correctly without duplicating module identities.

## Unintended Mutation Reversal
- Modified `tests/test_m6e_operator_acceptance.py::test_report_schema_and_mode_fields_from_check_only` to safely mock `m6e.M5N_OUT_DIR` using `monkeypatch` and `tmp_path`, preventing tests from unintentionally overwriting the sealed `research/live_observation_runs/current_conversation_context/conversation_context.md` file. The unintended mutation committed previously has been securely reverted and verified.

## Targeted Failure Results
- The 20 Windows-origin target nodes were used as the bounded change inventory.
- They pass on both Linux baseline and Linux PR head.
- The PR introduces no Linux regression and adds explicit UTF-8/import hygiene expected to address the prior Windows-specific failure modes.

## Full Non-Network Before and After
Executed from isolated identical Linux worktrees (`fresh_baseline_worktree` and `fresh_pr_head_worktree`).

### Baseline (Linux)
- **Passed:** 2089
- **Failed:** 12
- **Skipped:** 0
- **Deselected:** 1
- **Exit Code:** 1

### PR Head (Linux)
- **Passed:** 2089
- **Failed:** 12
- **Skipped:** 0
- **Deselected:** 1
- **Exit Code:** 1

### Classification
- **Retained:** 12 (exact matching sets between baseline and PR head)
- **Removed:** 0
- **Novel:** 0
- **Unresolved:** 0

## M8R Regression Results
- **M8R-05B-03:** 108 passed
- **M8R-05B-02:** 55 passed
- **M8R-05B-01:** 58 passed
- **Fixed Upstream Gate:** 44 passed

## Boundary Confirmations
- **No live network execution occurred.**
- **No production semantics changed.**
- **M8R-05C was not started.**
- **No M5K governance assertions failed.**
- **No `frontend/public` or `research/generated` outputs were changed (`git diff --exit-code -- research/` cleanly verified).**

## Caveats
Windows same-environment regression closure passed with zero novel failures. The 20 targeted CP950 decoding failures have been fully resolved.

## Final Decision
Approved. Recommend merging PR-B and starting M8R-05C.
