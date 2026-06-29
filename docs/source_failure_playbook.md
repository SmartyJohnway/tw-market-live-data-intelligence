# Source Failure Playbook

## TWSE OpenAPI malformed or missing rows
Record missing symbol, row shape, status code, retrieval timestamp, and parser error. Preserve last-known-good M5F package. Do not substitute yesterday close as current data.

## TPEx OpenAPI failures
Classify as source failure or unsupported target. Record URL, method, status, body sample, and parsed fields if available. Do not promote partial TPEx data without caveats.

## TWSE MIS block/cookie/rate-limit/session issues
Treat as unofficial browser-rendered endpoint risk. Do not bypass cookies, sessions, or rate limits. Do not use MIS as canonical product refresh without future authorization.

## Yahoo identity and suffix mismatch
Reject suffix-drop, Japan OTC, or name/identity mismatch. Record symbol requested, symbol returned, exchange, timezone, and mismatch reason.

## Stale or delayed data
Display source date, retrieval timestamp, stale/delay status, and caveats. Never relabel stale data as realtime.

## Partial target failure
Keep successful targets descriptive and disclose failed targets separately. Do not fabricate missing symbols.

## Malformed evidence or manifest/hash mismatch
Fail closed. Recompute hashes from immutable upstream artifacts. If mismatch persists, block release and preserve last-known-good package.

## Missing canonical package
FastAPI and MCP must return structured errors. Operators should rebuild in the platform temp directory, validate, then write only to the fixed M5F path.

## Consumer disagreement
If frontend/API/MCP symbols, source date, hashes, or caveats diverge, block release. Canonical payload wins; regenerate derivatives from it.

## Last-known-good preservation
Never delete prior validated evidence while investigating. Do not write into M5B/M5C/M5D, `research/generated`, or `frontend/public` during M5FGH repair.


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
