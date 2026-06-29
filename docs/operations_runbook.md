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
Use `python scripts/build_m5f_canonical_market_context_package.py --check-only` for validation. A repository write is allowed only to `research/staging/m5f/m5f_canonical_market_context_01`; temporary rebuilds must be under the platform temp directory, for example `/tmp` on Linux/macOS or `%TEMP%` on Windows. Never pass `scripts`, `server`, `docs`, `frontend/public`, or `research/generated` as output directories.

## Safe local preview
Serve from the repo root so browser `fetch()` can read the package: `python -m http.server 8000`, then open `http://127.0.0.1:8000/frontend/readonly-preview/M5EMarketContextPreview.html`. Opening by `file://` may be blocked by browser origin rules.

## FastAPI startup
Run `uvicorn server.main:app --reload`. Use only readonly context endpoints under `/api/context/*` for M5F product consumption.

## MCP startup
Run `python server/mcp_server.py` over stdio. Use M5F readonly tools first. The old M3G live evidence tool is disabled for M5F product refresh pending M5I.

## Rollback/recovery
Preserve the last-known-good M5F directory and manifest. If validation fails, do not partially edit artifacts; rebuild into the platform temp directory, compare hashes, then replace only through the builder.

## Adding a source or target
Requires source catalog update, bounded scope, evidence validation, lineage capture, and explicit future authorization for any network execution. Do not consume prior M5B authorization.

## Explicit authorization required
Any live probe, market-data network call, frontend/public publication, production refresh, broker/auth activation, credential use, or generated artifact refresh requires future explicit authorization.

## Forbidden
No live probes, no full-market scans, no polling loop, no trading signal, no target price/ranking, no realtime guarantee, no production-current-state claim.


## M5IJ local product release

M5F is the canonical product context. M5I is explicit bounded refresh only; M5J is final local release hardening. Default startup makes no market-data network calls. Refresh requires explicit single-use authorization and is bounded to the configured watchlist and product scope. Failed refresh preserves last-known-good M5F. No full-market scan, polling, frontend/public publication, research/generated refresh, production/prod write, broker/auth, automatic order, trading signal, target price, ranking, or recommendation is allowed. FastAPI `/api/probe/*` is disabled pending M5I and returns 410.

Required commands:

```bash
python -m pip install -r requirements.txt
pytest -m "not network" -v
python scripts/validate_m5f_canonical_market_context_package.py --package-dir research/staging/m5f/m5f_canonical_market_context_01
python scripts/run_m5ij_end_to_end_acceptance.py --check-only
uvicorn server.main:app --host 127.0.0.1 --port 8000
python server/mcp_server.py --startup-check
```

Explicit authorization refresh command, if supported by the operator environment:

```bash
python scripts/run_m5i_explicit_bounded_refresh.py --execute-refresh --authorization-token <authorization.json> --source TWSE_OpenAPI --targets 0050 00929 2330 --no-frontend-publication --no-production-refresh --no-generated-refresh --no-trading-output
```
