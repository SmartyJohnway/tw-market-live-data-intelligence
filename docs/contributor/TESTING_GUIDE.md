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
