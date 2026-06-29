# MCP Usage Guide

## Start command
From the repository root run `python server/mcp_server.py`. The server adjusts `sys.path` before importing validators, so this direct command is supported.

## Stdio client example
Configure an MCP stdio server with command `python` and args `["server/mcp_server.py"]`, working directory set to the repository root.

## Readonly M5F tools
- `get_canonical_market_context`
- `get_latest_market_snapshot`
- `get_watchlist_observations`
- `get_ai_context_pack`
- `get_chatgpt_briefing`
- `get_source_health`
- `get_capability_matrix`
- `get_source_catalog`

Every M5F artifact tool validates the package first and fails closed with `package_validation_failed` if manifest, lineage, or derivatives diverge.

## Check-only tool
`check_bounded_market_refresh_readiness` performs no network calls and no writes. It reports that future M5I authorization is required and that M5B authorization is already consumed.

## Disabled legacy execution
`run_m3g04_controlled_live_probe_evidence` is not listed as an M5F product refresh path and returns `legacy_live_tool_disabled_pending_m5i` if called.

## Safe questions
Ask for package caveats, exact symbols, source health, source authority registry, or briefing text. Unsupported questions include live refresh, production publication, broker activation, target prices, rankings, and trading signals.


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
