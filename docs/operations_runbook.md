# M5FGH Operations Runbook

## Purpose
Operate the local-first, bounded-watchlist Taiwan market context center without live probes, publication, generated artifact refresh, or trading outputs.

## Install and validation
1. Install project test dependencies as usual for the repository.
2. Validate the canonical package: `python scripts/validate_m5f_canonical_market_context_package.py --package-dir research/staging/m5f/m5f_canonical_market_context_01`.
3. Run consumer alignment: `python scripts/run_m5fgh_local_product_demo.py --check-only`.
4. Run non-network tests before release: `pytest -m "not network" -v`.

## Target config updates
Target changes belong to a future authorized refresh bundle. Do not edit the M5F package manually. For a future target change, update `config/market_targets.json`, document the bounded symbols, then run only check-only validation until an explicit M5I authorization exists.

## Canonical package rebuild
Use `python scripts/build_m5f_canonical_market_context_package.py --check-only` for validation. A repository write is allowed only to `research/staging/m5f/m5f_canonical_market_context_01`; temporary rebuilds must be under `/tmp`. Never pass `scripts`, `server`, `docs`, `frontend/public`, or `research/generated` as output directories.

## Safe local preview
Serve from the repo root so browser `fetch()` can read the package: `python -m http.server 8000`, then open `http://127.0.0.1:8000/frontend/readonly-preview/M5EMarketContextPreview.html`. Opening by `file://` may be blocked by browser origin rules.

## FastAPI startup
Run `uvicorn server.main:app --reload`. Use only readonly context endpoints under `/api/context/*` for M5F product consumption.

## MCP startup
Run `python server/mcp_server.py` over stdio. Use M5F readonly tools first. The old M3G live evidence tool is disabled for M5F product refresh pending M5I.

## Rollback/recovery
Preserve the last-known-good M5F directory and manifest. If validation fails, do not partially edit artifacts; rebuild into `/tmp`, compare hashes, then replace only through the builder.

## Adding a source or target
Requires source catalog update, bounded scope, evidence validation, lineage capture, and explicit future authorization for any network execution. Do not consume prior M5B authorization.

## Explicit authorization required
Any live probe, market-data network call, frontend/public publication, production refresh, broker/auth activation, credential use, or generated artifact refresh requires future explicit authorization.

## Forbidden
No live probes, no full-market scans, no polling loop, no trading signal, no target price/ranking, no realtime guarantee, no production-current-state claim.
