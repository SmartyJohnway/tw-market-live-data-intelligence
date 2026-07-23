# M8R-03E-R5B-R1 Filesystem Path Error-Code Precedence Reconciliation

## Decision

**PASS_WITH_CAVEATS.** This correction changes no production code and does not weaken filesystem containment. A POSIX prefix-collision candidate such as `/tmp/output-evil/file.json` is rejected during lexical classification as `rooted`, before containment evaluation, with `rooted_output_path_forbidden`. This preserves the explicit distinction from Windows drive-absolute inputs (`absolute_output_path_forbidden`).

## Contract matrix

| Input class | Example | Path class | Error code |
| --- | --- | --- | --- |
| Safe relative | `nested/a.json` | `safe_relative` | none |
| Traversal | `../a.json` / `..\\a.json` | `traversal` | `path_traversal_forbidden` |
| POSIX rooted | `/tmp/a.json` | `rooted` | `rooted_output_path_forbidden` |
| Windows drive absolute | `C:/tmp/a.json` | `absolute` | `absolute_output_path_forbidden` |
| Windows drive relative | `C:tmp/a.json` | `drive_relative` | `drive_relative_output_path_forbidden` |
| UNC | `//server/share/a.json` | `unc` | `unc_output_path_forbidden` |
| URI-like | `https://example.invalid/a.json` | `scheme` | `absolute_output_path_forbidden` |
| Prefix collision | `/tmp/output-evil/a.json`, root `/tmp/output` | `rooted` | `rooted_output_path_forbidden` |

The prefix collision is classified from lexical input before any containment path is composed. The test suite now makes the POSIX, drive-absolute, drive-relative, and UNC distinctions explicit and platform-neutral.

## Verification

* Isolated corrected node: `1 passed in 0.13s`.
* Filesystem containment module: `14 passed in 0.35s`.
* Related deterministic filesystem/security files: `35 passed in 1.67s`.
* `compileall`: passed.
* Full non-network profile: `1867 passed, 7 failed, 1 skipped, 1 deselected` in `103.134s`. The profile return code is `1` only because of the established seven M5D/M5E caveats; it has no novel failures.

The old failing node, `test_prefix_collision_absolute_path_rejected`, is resolved by its precise renamed replacement, `test_prefix_collision_rooted_path_rejected`. The seven retained failures and runtime-side-effect cleanup are recorded in the companion JSON report. Historical M8R-05A-F3 evidence remains unchanged.

## Next task

`M8R-05B-GOVERNED-REQUEST-TO-ORCHESTRATION-HANDOFF-PREFLIGHT`
