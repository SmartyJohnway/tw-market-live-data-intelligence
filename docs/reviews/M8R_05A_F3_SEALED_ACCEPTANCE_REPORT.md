# M8R-05A-F3 sealed verification evidence

## Scope
This evidence records F3 verification only; it does not mark the PR accepted.

## Targeted and compile results
- Targeted F3 suite: **39 passed in 0.76s**.
- Compile validation: **pass**.

## Full profile
`python scripts/run_test_profile.py full-non-network --json` returned 1: **1862 passed, 8 failed, 1 skipped, 1 deselected** in 109.61s. The profile reported `network_may_have_occurred: false`.

## Baseline comparison
The baseline is `docs/reviews/M8R_05A_F2_SEALED_ACCEPTANCE_REPORT.json`. Seven M5D/M5E failures are retained. The filesystem node `tests/unit/test_m8r_filesystem_containment.py::test_prefix_collision_absolute_path_rejected` is unresolved: it expected `absolute_output_path_forbidden` but reproduced `rooted_output_path_forbidden`. PR #165 does not change the filesystem implementation or its test, but that does not establish a repository-wide baseline classification.

## Runtime cleanup
The full profile temporarily generated conversation-context, M6E, and portable-skill outputs. They were restored/removed; the final `research/live_observation_runs` diff is empty.

## Decision
**not_yet_accepted**. M8R-05A-F3 targeted implementation is verified. No F3-specific regression was identified. Repository-wide acceptance remains not yet accepted because one filesystem-containment failure cannot be classified against an auditable accepted baseline.

## Next allowed action
Resolve or baseline-classify the filesystem-containment node, then re-evaluate repository-wide acceptance without changing F3 implementation scope.
