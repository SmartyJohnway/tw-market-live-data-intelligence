# M5IJ final local product release

M5F is the canonical local product context at `research/staging/m5f/m5f_canonical_market_context_01/`. Default startup, tests, FastAPI, MCP, and frontend readonly preview read local artifacts only and make no market-data network calls.

M5I adds an explicit bounded refresh CLI only. A refresh requires `--execute-refresh`, a machine-verifiable authorization token, `--source TWSE_OpenAPI`, targets bounded to the configured watchlist and the M5F product scope, plus flags forbidding frontend publication, production refresh, generated refresh, and trading output. Failed validation does not claim the single-use token. Once execution starts, evidence records that network calls may have occurred. No full-market scan, polling, broker/auth, credentials, automatic orders, trading signals, target prices, recommendations, or rankings are allowed.

Required local checks:

```bash
python -m pip install -r requirements.txt
pytest -m "not network" -v
python scripts/validate_m5f_canonical_market_context_package.py --package-dir research/staging/m5f/m5f_canonical_market_context_01
python scripts/run_m5ij_end_to_end_acceptance.py --check-only
uvicorn server.main:app --host 127.0.0.1 --port 8000
python server/mcp_server.py --startup-check
```

Explicit refresh, only with a checked authorization file:

```bash
python scripts/run_m5i_explicit_bounded_refresh.py --execute-refresh --authorization-token <authorization.json> --source TWSE_OpenAPI --targets 0050 00929 2330 --no-frontend-publication --no-production-refresh --no-generated-refresh --no-trading-output
```
