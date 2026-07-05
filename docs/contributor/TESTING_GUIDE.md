# Testing Guide

Core validation commands:

```bash
python -m compileall scripts server tests
pytest -m "not network" -v
python scripts/validate_m5f_canonical_market_context_package.py --package-dir research/staging/m5f/m5f_canonical_market_context_01
python scripts/run_m5ij_end_to_end_acceptance.py --check-only
python scripts/run_m5k_postmerge_validation.py --check-only
python scripts/run_m5q_source_health_probe.py --check-only
python scripts/build_m5n_conversation_context.py
python scripts/governance_forbidden_path_guard.py
python scripts/forbidden_behavior_scanner.py
git diff --check
```

If adding docs, also manually audit Markdown links or run any future link checker added to the repo.

## M6B test taxonomy and markers

M6B separates tests by execution risk rather than by feature ownership:

- `unit`: pure local logic; no network; safe for default CI.
- `mock`: simulated source envelopes, dirty rows, and fail-closed behavior; no network; safe for default CI.
- `integration`: real bounded network source-contract checks; manual only and always paired with `network` so `pytest -m "not network" -v` excludes them.
- `release_preflight`: optional operator-run checks before release; live variants are explicit only.

Default CI remains:

```bash
pytest -m "not network" -v
```

Manual live source-contract checks are bounded to `2330`, `0050`, and `TX`; they do not assert exact price, market direction, trading recommendations, rankings, target prices, or current realtime guarantees.

```bash
pytest -m integration -v
python scripts/run_m6b_source_contract_preflight.py --execute-live-contract-check
```

No-network source-contract preflight is safe for default validation and performs no writes:

```bash
python scripts/run_m6b_source_contract_preflight.py --check-only
```


## M6D compatibility hardening tests

M6D adds non-network tests for SSL policy selection, CLI/env precedence, invalid-policy fail-closed behavior, strict mode avoiding unverified TLS contexts, explicit compatibility/unsafe diagnostics, mocked network context passing, M5K/M6B artifact diagnostics, Windows/Python 3.13 operator hints, and local CORS/frontend compatibility. Default test runs must not perform live network calls.

Run:

```bash
pytest -m "not network" -v
```

## M6E tests

M6E is covered by `tests/test_m6e_operator_acceptance.py`. Default tests do not run live observation or browser E2E; they verify report schema, non-network check-only behavior, FastAPI/MCP fail-closed SSL policy handling, frontend static contracts, and forbidden-field scans.

## M6G browser/operator E2E tests

Default non-network tests do not require browser binaries:

```bash
pytest -m "not network" -v
```

The optional browser/operator acceptance command is:

```bash
python scripts/run_m6g_browser_operator_e2e.py --check-only
```

For full browser automation, install Playwright and Chromium first. Browser, E2E, and live tests are marked `browser`, `e2e`, and `live` so default CI can remain independent of browser installation and explicit network checks.

## M6H three-tier portfolio and test-growth policy

Do not optimize for test count. Optimize for operator journey coverage and risk coverage.

### Tier 1 — default CI

Tier 1 is fast, deterministic, non-network validation for core safety, normalization, schemas, dirty-data handling, watchlist validation, fail-closed behavior, forbidden behavior, canonical contracts, critical API contracts, critical SSL policy resolution, and governance boundaries.

Default CI remains:

```bash
pytest -m "not network" -v
```

Tier 1 protects against schema corruption, unsafe behavior, bad normalization, invalid watchlist acceptance, silent TLS policy downgrade, canonical mutation, raw payload leakage, and trading semantic leakage. Tier 1 does not prove real browser DOM behavior, real FastAPI process communication, Chromium fetch behavior, exchange TLS handshakes, real source availability, or cold-clone usability.

### Tier 2 — operator acceptance and release preflight

Tier 2 covers cross-component validation, operator workflow validation, artifact validation, release readiness, M6B source-contract preflight, M6E operator acceptance, M5F validation, M5IJ acceptance, M5K postmerge validation, M5Q check-only, M5N Conversation Package build, FastAPI TestClient integration, MCP startup checks, and operator preflight.

### Tier 3 — browser, bounded live, OS-specific, cold clone

Tier 3 proves real operator journeys, actual browser behavior, actual local-process integration, external source compatibility, TLS/runtime compatibility, and cold-clone usability. This tier includes Playwright browser E2E, M6G check-only, M6G explicit bounded live, Windows/Python 3.13 compatibility validation, real TLS handshake validation, release-time bounded source checks, and cold-clone operator acceptance.

Tier 3 is the preferred evidence for defects such as frontend DOM payloads missing required `id`, browser fetch/CORS failures, frontend/API mismatches, local FastAPI connectivity failures, real Chromium behavior, TLS certificate/runtime compatibility, environment-specific failures, and operator bootstrap failures.

### High-value operator journeys

1. Workbench Boot E2E: FastAPI starts, frontend loads, frontend connects to local API, and the operator sees usable workbench state.
2. Watchlist Validate / Plan E2E: default watchlist loads, DOM rows are reconstructed, frontend generates watchlist payload, required `id` exists, validate succeeds, and plan succeeds.
3. Explicit Bounded Live Observation E2E: operator explicitly requests live observation, confirmation is required, bounded watchlist is used, observation executes, result renders, no polling occurs, and no unexpected execute occurs.
4. TLS Compatibility E2E: strict default remains intact, compatibility is explicit, the real environment can perform required source TLS handshake when compatibility is explicitly selected, and no silent fallback occurs.
5. Conversation Package E2E: observation evidence exists, M5N Conversation Package builds, canonical and observation semantics remain separated, AI handoff is readable, and no raw payload leakage occurs.
6. Cold Clone Operator Acceptance: fresh clone, dependency installation, environment diagnostics, local workbench start, browser load, validate/plan, optional explicit bounded live, and Conversation Package generation.

### Before adding a new test

Contributors should determine:

1. What unique risk does this test protect?
2. Is the risk already covered by an existing test?
3. Is this an exact or near duplicate?
4. Is a unit/mock test the correct level?
5. Would integration testing provide stronger evidence?
6. Would browser E2E provide stronger evidence?
7. Does the test belong in Tier 1, Tier 2, or Tier 3?
8. Should the test run on every CI execution?
9. Does the test rely on external source behavior?
10. Does this test increase operator journey coverage?

Prefer one high-signal regression test over multiple near-identical assertions across several files when the same risk boundary is already protected. Do not weaken critical governance or fail-closed coverage merely to reduce test count.

## Browser/E2E dependency bootstrap

Browser readiness has three layers: the Python Playwright package, the Chromium browser binary, and OS/system browser dependencies. A successful `pip install playwright` alone does not prove browser E2E readiness.

Install browser E2E dependencies explicitly:

```bash
python -m pip install -r requirements-browser-e2e.txt
```

Windows/macOS Chromium install:

```bash
python -m playwright install chromium
```

Linux/Codex/CI-like preferred install:

```bash
python -m playwright install --with-deps chromium
```

If browser binaries already exist but Linux OS dependencies are missing:

```bash
python -m playwright install-deps chromium
```

Do not immediately accept `skipped_with_caveats` merely because Playwright or Chromium is initially unavailable. First investigate or attempt Python Playwright dependency availability, Chromium browser binary availability, required OS/system browser dependencies, and a supported installation path. Only report `skipped_with_caveats` after installation/bootstrap was attempted or proven unavailable, and record the dependency step attempted, command attempted, blocking error, environment limitation, and recommended next action.

`scripts/run_m6g_browser_operator_e2e.py` is an acceptance runner, not a package installer. It must not automatically pip install packages, install Chromium, install OS dependencies, invoke apt/sudo, or mutate system dependency state.

## M6K explicit execution profiles

Use the smallest profile that answers the validation question while preserving broader release validation:

- Small Python helper: `python scripts/run_test_profile.py fast --json`.
- FastAPI or MCP contract: `python scripts/run_test_profile.py default-ci --json`; add `python scripts/run_test_profile.py operator-preflight --json` if an execution path changed.
- Frontend HTML/JS/static contract: `python scripts/run_test_profile.py default-ci --json`; add `python -m pip install -r requirements-browser-e2e.txt`, `python -m playwright install --with-deps chromium`, and `python scripts/run_test_profile.py browser-e2e --json` for real browser validation.
- Source normalization: `python scripts/run_test_profile.py default-ci --json`; run `python scripts/run_test_profile.py full-non-network --json` before merge when broad adapter behavior changed.
- M5F canonical package or consumers: `python scripts/run_test_profile.py full-non-network --json` and `python scripts/run_test_profile.py operator-preflight --json`.
- Release preparation: `python scripts/run_test_profile.py full-non-network --json`, `python scripts/run_test_profile.py operator-preflight --json`, and `python scripts/run_test_profile.py browser-e2e --json`.
- Explicit bounded live validation: `python scripts/run_test_profile.py bounded-live --confirm-bounded-live --ssl-policy compatibility` or `--ssl-policy strict` only when the operator intends live execution.

Profile semantics:

- `fast`: deterministic inner-loop safety checks; no browser, network, or bounded live execution.
- `default_ci`: normal PR/push merge protection; no real network, no browser dependency installation, no bounded live execution.
- `full_regression`: broad non-network regression used by FULL_NON_NETWORK.
- `operator`: operator/preflight validation routed through authoritative scripts rather than duplicated in pytest.
- `browser`: optional browser automation tests and BROWSER_E2E routing.
- `network` and `live`: explicit external or bounded-live checks excluded from normal DEFAULT_CI.

### M6K Commit 2 CI gate preservation

FULL_NON_NETWORK now has two phases: broad `pytest -m "not network"` regression and the legacy check-only CI acceptance gates inventoried in `docs/reviews/m6k_ci_gate_migration_matrix.csv`. Do not assume pytest coverage replaces a standalone acceptance runner. Normal DEFAULT_CI intentionally remains smaller and does not run all legacy acceptance gates on every PR.

Windows compatibility smoke is preserved in the `Windows Compatibility Smoke` workflow. It is manual or `windows-smoke` label gated, uses strict defaults, performs no real network execution, and covers M5F canonical validation, M5I bounded refresh contracts, M5IJ acceptance, FastAPI context, MCP startup/fail-closed behavior, SSL policy, and local networking compatibility.
