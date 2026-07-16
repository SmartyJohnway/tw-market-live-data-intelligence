# M8R-03E-R2-F0 test-suite lifecycle and profile realignment

Baseline SHA: `1c2144498b524e52b2bf21fce8ed00683d9eb3a7`.

Disposition: **GO_WITH_CAVEATS**.

F0 separates core regression, active contract, component-specific, milestone acceptance, historical archive, and performance tests. The authoritative inventory is `docs/quality/m8_test_suite_lifecycle_inventory.json`; the execution policy is `docs/quality/M8_TEST_SUITE_LIFECYCLE_AND_PROFILE_POLICY.md`.

Default CI now remains bounded to current core/contract/security smoke and excludes historical/performance groups. Historical archive checks live under `tests/acceptance_archive/` and are only routed by `historical-acceptance`.
