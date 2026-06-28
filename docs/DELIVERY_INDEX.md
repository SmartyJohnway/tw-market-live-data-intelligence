# Delivery index: local-first Taiwan market data workbench

## Current deliverable status

The repository is a local-first, fixture-backed staging implementation suitable for governed validation. It is not production-ready, does not refresh live sources, and does not publish frontend artifacts.

## Safe commands

- `python -m compileall scripts tests`
- `pytest -m "not network" tests/unit/test_controlled_refresh_staging_writer.py`
- `pytest -m "not network" tests/unit/test_controlled_refresh_staging_validator.py`
- `pytest -m "not network" tests/unit/test_frontend_readonly_context_package.py`
- `pytest -m "not network" tests/unit/test_local_delivery_acceptance.py`
- `pytest -m "not network" tests/unit/test_governance_regression_guards.py`
- `pytest -m "not network"`
- `python scripts/run_local_delivery_acceptance.py --check-only`

## Forbidden commands

- `scripts/run_all_probes.py`
- `python scripts/run_all_probes.py`
- Any live probe script, controlled live probe execution, broker/auth script, production refresh script, or frontend public refresh script unless a future authorization explicitly permits it.

## Core docs map

- `docs/source_catalog.md`
- `docs/capability_matrix.md`
- `docs/recommended_architecture.md`
- `docs/DELIVERY_INDEX.md`

## Contracts map

- `docs/contracts/controlled_refresh_staging_write_contract.md`
- `docs/contracts/frontend_readonly_caveat_staleness_display_contract.md`
- `docs/contracts/frontend_readonly_context_package_schema.md`

## Runbooks map

- `docs/runbooks/OPERATOR_RUNBOOK_LOCAL_FIRST_MARKET_CONTEXT.md`

## Scripts map

- `scripts/controlled_refresh_staging_writer.py`: fixture-backed staging payload builder and temp/staging writer.
- `scripts/controlled_refresh_staging_validator.py`: reusable staging schema and governance validator.
- `scripts/build_frontend_readonly_context_package.py`: readonly package builder for operator-supplied temp/staging paths only.
- `scripts/run_local_delivery_acceptance.py`: check-only local delivery acceptance runner.

## Tests map

- `tests/unit/test_controlled_refresh_staging_writer.py`
- `tests/unit/test_controlled_refresh_staging_validator.py`
- `tests/unit/test_frontend_readonly_context_package.py`
- `tests/unit/test_local_delivery_acceptance.py`
- `tests/unit/test_governance_regression_guards.py`

## Source authority summary

Allowlisted staging source identifiers are `TWSE_OpenAPI`, `TPEx_OpenAPI`, `TWSE_MIS`, and `Yahoo_Finance`. Official OpenAPI sources remain distinct from unofficial or third-party sources.

## TWSE MIS caveats

`TWSE_MIS` is treated as an unofficial endpoint. It must preserve an unofficial-source risk flag, preferably `unofficial_source_risk`; the legacy alias `unofficial_endpoint` remains accepted. `live_candidate` values are not realtime guarantees.

## Staging writer status

Implemented as fixture-backed and fail-closed. It requires explicit confirmations and rejects production-looking paths, `research/generated/*`, `frontend/public/*`, full-market targets, realtime guarantee fields, and trading fields.

## Frontend readonly package status

Implemented for temporary/staging output only. It emits caveats including `not_realtime_guaranteed`, `not_trading_signal`, `not_production_current_state`, `source_risk_present`, and `freshness_must_be_displayed`.

## Acceptance runner status

Implemented in check-only default mode. Optional reports may be written only to operator-supplied non-forbidden paths.

## Not production-ready list

- No live probes.
- No production refresh.
- No production write.
- No durable evidence promotion.
- No frontend/public publication.
- No broker/auth activation.
- No trading signals.
- No realtime guarantee.

## Next authorization ladder

1. Authorize a bounded, explicit live probe dry run.
2. Validate evidence without promotion.
3. Authorize staging-only write from fresh evidence.
4. Review package caveats manually.
5. Separately authorize frontend/public publication only after production-readiness blockers are resolved.

## M3MNOP Bundle 03

Adds non-network CI, fixture/golden corpus, operator manuals, docs index, release readiness, and a local readonly frontend preview outside frontend/public. No live probes, no production refresh, no generated artifacts, no frontend public publication, no trading signals, and no realtime guarantee.


## M4 Omega

Adds local-only fixture-only governed platform skeleton: governance policy, source registry, evidence ledger, fixture replay, readonly observability, release gates, authorization ladder, and operator checks.

## M5FGH product convergence status

PR #59 / M5E is treated as merged upstream. M5FGH converges the reviewed M5C/M5D historical evidence into the current canonical local product line: `research/staging/m5f/m5f_canonical_market_context_01/canonical_market_context.json` is the only source-of-truth payload for browser preview, FastAPI readonly endpoints, MCP readonly tools, and AI briefing artifacts.

North Star: a local-first, bounded-watchlist, explicit manual-refresh Taiwan market context center shared by browser and AI Agents. The package is historical/stale reviewed evidence for 0050, 00929, and 2330 from TWSE_OpenAPI source date 2026-06-26; it is not realtime, not production current state, not full-market coverage, and not a trading signal.

Historical M3 generated artifacts under `research/generated/` remain legacy generated artifacts. M5F is the current canonical consumer package. Bounded live evidence exists in prior governed evidence, so the repo is not fixture-only, but M5FGH does not run new live probes. The only remaining main bundle after this closure is M5IJ for future explicitly authorized refresh execution and final release hardening.
