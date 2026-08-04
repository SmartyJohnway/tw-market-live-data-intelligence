# Windows CP950 Test Hygiene Validation Result

## SHAs
- Baseline: `e00193d0c1719bbdbd3eea2ed9f0f21c0fd23388`
- Tested Implementation Candidate: `bc22a8854cbc1178c06dbb16cd1f66331e923c73`
- Evidence Parent Commit: `bc22a8854cbc1178c06dbb16cd1f66331e923c73`

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
