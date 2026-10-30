# Contributing

Thank you for improving this local-first evidence workbench. Start with the
[contributor guide](docs/contributor/CONTRIBUTING.md), [development guide](docs/contributor/DEVELOPMENT_GUIDE.md), and [testing guide](docs/contributor/TESTING_GUIDE.md).

## Before opening a pull request

1. Keep changes small and explain their contract or user-visible effect.
2. Do not add secrets, credentials, cookies, raw personal data, or production
   Security Master / Watchlist state.
3. Preserve explicit authorization, execute-once, and no-trading boundaries.
4. Run the narrowest relevant tests, then the documented validation profile
   when the change affects a public contract or release gate.

Use the bug-report template for reproducible defects and the feature-request
template for proposals. Architecture and governance changes need the relevant
contract and acceptance evidence; they are not implied by an issue alone.

## Development safety

Use isolated local roots for tests. Do not perform external market requests,
Security Master acquisition, or data mutation merely to make a test pass.

## Current test authority

`config/test_governance_authority.json` owns operational roles and selection
policy. `config/test_execution_profiles.json` owns reviewed explicit enrollment.
Current counts are observations, not fixed acceptance thresholds. Test additions
need role review and collection evidence, never edits to historical TG ledgers.

Before normal merge, run affected tests and:

```powershell
python -B scripts/validate_current_test_governance.py
python -B scripts/validate_phase_h_v3_contracts.py
python -B scripts/validate_portable_catalog_sync.py
python -B scripts/validate_runtime_skill_guide_sync.py
python -B scripts/run_current_merge_gate.py --output C:/twmarket_temp/s3-r1-merge.json
git diff --check
```

`default-ci` is the normal reviewed core/current developer profile. It excludes
network, live, browser, performance, historical-marked and release-preflight
nodes. It is not exhaustive coverage or proof of release readiness. Some mixed
files still contain obsolete historical assertions without historical markers;
their failures remain visible and must be classified, not silently waived.
The S3 governance record documents the 12 known historical/transition failures.
Raw default diagnostics: `python -B scripts/run_test_profile.py default-ci --json`.
Raw pytest exit status remains unchanged. The bounded `current-merge-gate` executes
all default tests and reports the exact authorized historical/transition diagnostics
separately from blocking current failures. New failures, coverage loss, collection
errors, and unauthorized skip/xfail fail the machine merge verdict. Known diagnostics
that pass are disclosed for explicit later governance retirement.

The governed minimum path/node identities and update policy live in
`config/current_test_coverage_floor.v1.json`; growth is allowed, reductions require
explicit Owner governance review. The validator pins the reviewed floor bytes;
regenerating the manifest alone cannot bless coverage loss.

Broad current regression:

```powershell
python -B scripts/run_test_profile.py full-current --json
```

`full-current` is the explicit broad current lifecycle superset of default, with
the same exclusions. `full-non-network` instead discovers `tests` with only
`not network and not historical and not performance`, then invokes additional
acceptance runners. It may include browser/live/release-marked cases and platform
specific diagnostics; its name does not guarantee the tighter current policy.
It is a separate manual diagnostic, not the release-blocking authority.

Release blocking (existing Node/Git and governed dependencies required):

```powershell
python -B scripts/run_test_profile.py release-blocking-ci --json --output-root C:/twmarket_temp/release-check
```

This delegates to `scripts/run_deterministic_ci.py` and the unchanged
`config/release_blocking_ci.v1.json`. `release-preflight-current` is a separate
small lifecycle selection; it cannot establish release readiness by itself.

Historical replay / integrity:

```powershell
python -B scripts/validate_test_governance_tg5.py
python -B scripts/run_test_profile.py historical-milestone-replay --json
python -B scripts/run_test_profile.py mixed-historical-diagnostic --json
python -B scripts/run_test_profile.py pre-tg5-default-ci --json
```

The TG5 validator checks frozen acceptance snapshots, not today's enrollment.
Its optional runtime inputs are historical TG5 run artifacts, not new current
runs. Replay profiles execute original assertions on today's tree and may fail;
exact rollback acceptance requires the frozen repository baseline. No historical
failure is automatically a current correctness waiver.

Both `.github/workflows/ci.yml` (default-ci) and
`.github/workflows/non-network-ci.yml` (full-non-network) currently use only
`workflow_dispatch`. They are manually invoked workflows, not automatic PR gates;
`automatic_ci_allowed` is eligibility metadata, not a trigger or branch protection.

Other profiles remain specialized: fast/changed-fast for inner-loop feedback;
component-* for focused checks; phase-j-regression-authority for J4/J3 semantic
regression; operator-preflight for operator checks; milestone-acceptance and
historical-acceptance for their explicit milestone/archive scopes; browser-e2e
for browser acceptance; bounded-live only with explicit bounded authorization;
performance for manual measurement. Do not enroll these wholesale into default.

## Release status

See [PROJECT.md](PROJECT.md) for current stable product authority. Frozen release
source/assets and historical release documents retain their own gate identities.

Historical current-tree diagnostic != exact historical-context replay.
The latter requires its original source context; current-tree historical failures
do not invalidate frozen acceptance or enter the current merge verdict.
