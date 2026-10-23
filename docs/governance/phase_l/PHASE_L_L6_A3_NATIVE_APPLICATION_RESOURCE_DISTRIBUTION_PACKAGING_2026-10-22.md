# Phase L6-A3 — Native Application / Resource Distribution Packaging

POST-INCIDENT CLEAN REIMPLEMENTATION FROM MERGED A2.

Technical disposition: `L6_A3_DEPENDENCY_CLOSURE_BLOCKED`.
Owner acceptance: PENDING. No technical completion or PR claim.

## Authority and entry

Owner authority: `USER_CHAT_2026-10-22_PHASE_L_L6_A3_CLEAN_REIMPLEMENTATION_FROM_MERGED_A2_AUTHORIZATION`.
Exact fetched base: `911a841b866795e8d0cd83d80b30b34701aa5980`.
Base tree: `72234b87fb3d47758c196c2ac80cc88549463837`.
Fresh branch: `phase-l/l6-a3-native-distribution-packaging-clean`.
Implementation commits: `3e0eca3e2bf483bff9626c67c95586ea84658f64`, `03774040265dcfd8d78fba9abbb26740b7d90514`.
Implementation tree: `596e0075806e263d6f1424ed5450c45407f73126`.
Run: `l6-a3-clean-20261023T002829Z`. Work began 2026-10-22 and resumed 2026-10-23 Asia/Taipei.
Lost original commit/tree `3f4965bf55155c1e176e128c57c05ac0b69fefe8` / `5903859c136afc05201346100b4f4619e9966fb7` remain historical reference only. No old source identity was reconstructed.

## Implemented but unaccepted

Package C exact-file role allowlist, builder, distribution/dependency manifests,
standard-library integrity verifier, offline bundle-local bootstrap, three relative
launchers, and package instructions exist in committed source. Version continues
to use tracked VERSION. Security Master release producer gains packaged-source
identity lookup with integrity validation; source checkout behavior remains.
49 Windows CPython 3.13 x64-compatible locked wheels were downloaded from the
explicit PyPI index. The temporary tools environment installed them offline and
`pip check` passed. Consumer bootstrap is not accepted merely from this result.
40 focused integrity/exclusion tests passed in the recorded intermediate run.

Resource policy is provisional. Review identified omitted imports from
`m8r_05b_03/__init__.py` (controlled_dispatch/orchestrator), so resource closure
has not passed. One exact frozen I3 governance JSON is provisionally included as
an active runtime contract exception; no historical authority file was changed.

## Blocking dependency/path conflict

Sections 18, 33, 50.27 and 51 prohibit dependency changes, forbid portable D-drive
path strings, require zero leakage, and require stopping when closure is blocked.
A decompressed-member scan found 213 D-like strings across seven unchanged
upstream wheels and 80 members. Cryptography accounts for 122 matches across two
members; its `_rust.pyd` contains upstream build paths such as `D:\a\infra\...`.
Some other matches are documentation examples. These strings do not establish
local D-drive access or runtime path authority. Full wheel hashes and member
hashes are in `dependency_embedded_path_scan.json`.

The builder's raw compressed-byte scan also false-positives on incidental byte
sequences. Correcting that scanner would not eliminate genuine upstream strings.
No wheel has been stripped, patched, rebuilt, substituted, dropped or upgraded.
A bounded Owner clarification is pending to exempt unchanged, hash-pinned,
third-party upstream build/debug provenance while retaining the prohibition on
local/first-party paths and runtime dependencies. No exception is assumed.

## Verification limits and safety

No accepted ZIP, consumer bootstrap, idempotence, lifecycle, exact-six MCP,
Security Master package run, APP_ROOT write guard, or relocation probe exists.
The historical SERVICE_EXITED_DURING_START is not adjudicated by this work.
Current-environment baseline default CI remains FAIL; candidate comparison is
not completed, and candidate-only failures are unknown. Intermediate logs are
retained rather than represented as final acceptance.

All parent Git/build/test commands target C:\twmarket_temp. No D-drive commands
were issued and no live provider acquisition was executed. The Python guard is
process-scoped, not OS-wide. Initial delegated smoke-test TEMP/TMP confinement
was not retained; therefore this report does not assert complete filesystem
write proof for that early smoke run. No user production installation was used.

A1-G07 remains CLOSED_A2_PART / REMAINDER_DEFER_A3; A1-G16 remains DEFER_A3.
P1-P5 remain PARTIAL; P6 NOT_YET_IMPLEMENTED / A4. No P1-P6 completion claim.
A4/A5/L7/Phase M, Docker, installer, merge and auto-merge remain unauthorized.
Current rollups have not been advanced to a completed A3 candidate.
