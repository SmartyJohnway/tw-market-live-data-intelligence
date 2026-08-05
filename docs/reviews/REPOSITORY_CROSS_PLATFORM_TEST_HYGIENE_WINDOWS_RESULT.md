# Windows CP950 Test Hygiene Validation Result

## SHAs
- Baseline: `e00193d0c1719bbdbd3eea2ed9f0f21c0fd23388`
- Tested Implementation Candidate: `5c1b0e9952fd65ea079727ad88522c6c33795e2c`
- Evidence Parent Commit: `5c1b0e9952fd65ea079727ad88522c6c33795e2c`

## Summary
- Status: **pass_with_caveats**
- Baseline failures: 43
- Candidate failures: 22
- Retained failures: 22
- Removed failures: 21
- Novel failures: 0

## Details
- All 20 target CP950 decoding nodes were successfully fixed.
- M5C dual invocation (script vs package) passed without PYTHONPATH.
- M6E containment verified via `git diff --exit-code e00193d0c1719bbdbd3eea2ed9f0f21c0fd23388 HEAD -- research/` and `git status`.
- Filesystem reason code is correctly deterministic (`absolute_output_path_forbidden` on Windows).

## Caveats
- The targeted Windows CP950 hygiene failures were removed with zero novel failures, while 22 baseline-preexisting non-network failures remain retained and are outside this bounded PR.
