# AI Safety Policy

## Required framing
AI responses must state that M5F data is historical/stale reviewed evidence for a bounded watchlist. Always include source, source date, freshness/staleness, and caveats.

## Prohibited outputs
Do not provide investment advice, buy/sell/hold instructions, target prices, rankings, portfolio actions, full-market claims, realtime guarantees, production-current-state claims, or broker/execution guidance.

## Source authority rules
TWSE_OpenAPI is official reference evidence in this package, not an intraday realtime feed. Source authority must be quoted from the package; do not upgrade source status based on assumptions.

## Freshness requirements
Display `historical/stale`, source date, retrieval timestamp where available, delay status, and `not_realtime_guaranteed`. If a symbol or source fails in future packages, disclose it instead of fabricating values.

## Bounded watchlist requirement
Only discuss the symbols present in the canonical payload. Do not infer market-wide conclusions from 0050, 00929, and 2330.

## Failure behavior
If package validation fails or a consumer reports malformed/missing artifacts, refuse market summarization and ask the operator to restore or rebuild the canonical package through the validator and builder.


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
