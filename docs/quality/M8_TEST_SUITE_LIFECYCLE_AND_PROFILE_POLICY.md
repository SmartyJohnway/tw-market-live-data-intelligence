# M8 test-suite lifecycle and profile policy

Baseline SHA: `1c2144498b524e52b2bf21fce8ed00683d9eb3a7`.

## Lifecycle categories

- **Core regression**: permanent product/security invariants. Runs in `default-ci`, component profiles, and `full-non-network`.
- **Active contract**: current authoritative contracts and stable invariants. Runs in `default-ci` and relevant component profiles.
- **Component-specific**: checks scoped to a component such as security, market-source, watchlist/evidence, Agent Skill, frontend publication, or governance. Runs in component profiles and `full-non-network`.
- **Milestone acceptance**: one-time migration/completion evidence. Runs only through `milestone-acceptance` unless promoted to a stable invariant.
- **Historical acceptance/archive**: reproduction of historical PR/release gates. Runs only through `historical-acceptance`; excluded from plain pytest discovery by `norecursedirs`.
- **Performance/benchmark**: timing/scale/baseline checks. Runs through `performance`, not default CI.

## Profiles

- `changed-fast`: local quick feedback.
- `default-ci`: every PR; excludes historical and performance suites.
- `component-security`, `component-market-source`, `component-watchlist-evidence`, `component-agent-skill`, `component-frontend-publication`, `component-governance`: scoped component profiles.
- `milestone-acceptance`: active M8R-03E-R2-F0/R2 milestone checks.
- `historical-acceptance`: archived reproducibility checks in `tests/acceptance_archive/`.
- `full-non-network`: broad non-network regression for milestone/release review.
- `performance`: reproducible performance baseline verification.

Exact pass counts, pass-count deltas, temporary successor values, and exact prose migration assertions are acceptance-run evidence, not permanent registry state.
