# Windows CP950 Test Hygiene Validation Result

## SHAs
- Baseline: `e00193d0c1719bbdbd3eea2ed9f0f21c0fd23388`
- Tested Implementation Candidate: `90275beea4fa3804d88c0b3047fcc75e4a40dd02`
- Evidence Parent Commit: `90275beea4fa3804d88c0b3047fcc75e4a40dd02`

## Summary
- Status: **pass_with_caveats**
- Baseline failures: 43
- Candidate failures: 0
- Retained failures: 0
- Removed failures: 43
- Novel failures: 0

## Details
- All 20 target CP950 decoding nodes were successfully fixed (see JSON array for per-node confirmation).
- M5C dual invocation (script vs package) verified.
- M6E containment verified via `git diff --exit-code e00193d0c1719bbdbd3eea2ed9f0f21c0fd23388 HEAD -- research/`.
- Filesystem reason code is correctly deterministic.
- `git diff --check e00193d0c1719bbdbd3eea2ed9f0f21c0fd23388 HEAD` exit code 0.

## Caveats
- The targeted Windows CP950 hygiene failures were removed with zero novel failures, while 22 baseline-preexisting non-network failures remain retained and are outside this bounded PR.
