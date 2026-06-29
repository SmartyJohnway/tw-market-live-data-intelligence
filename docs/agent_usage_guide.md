# Agent Usage Guide

## Goal
Agents should help operate a local-first, bounded-watchlist Taiwan market context center. The first artifact to read is `research/staging/m5f/m5f_canonical_market_context_01/canonical_market_context.json`.

## Citation and quoting rules
When answering, quote the package path, source, source date, freshness/stale status, caveats, and exact symbols. Do not summarize price-like values without saying they are reviewed historical evidence, not realtime prices.

## Safe workflow for Codex/Jules/Claude/Cursor/VS Code agents
1. Run `python scripts/validate_m5f_canonical_market_context_package.py --package-dir research/staging/m5f/m5f_canonical_market_context_01`.
2. Read canonical payload, then derived briefing if needed.
3. Use FastAPI/MCP readonly tools only for consumption.
4. Before handoff, report commands run, files touched, package hashes, and forbidden-path checks.

## Actions that may use network
Only future explicitly authorized refresh work may use market-data network calls. This M5FGH package does not authorize live probes, broker/auth flows, or publication.

## Forbidden agent claims
No investment advice, buy/sell/hold, target price, ranking, full-market coverage, realtime guarantee, or production-current-state claim.

## Handoff checklist
Include branch, commit, validation output, exact symbols, source date, caveats, and whether `frontend/public`, `research/generated`, M5B, M5C, or M5D changed.


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
