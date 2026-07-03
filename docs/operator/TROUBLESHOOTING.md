# Troubleshooting

- Dependency errors: run `python -m pip install -r requirements.txt`.
- Syntax/import errors: run `python -m compileall scripts server tests` and inspect the first failure.
- Non-network test failure: run `pytest -m "not network" -v` and inspect failing test names before editing behavior.
- M5F validation failure: run the M5F validator and do not mutate M5F unless a separate approved task says so.
- Missing latest observation: normal before explicit Mode B execution; use check-only planning first.
- Source health degraded/failed: treat as source usability evidence, not an operator instruction to retry aggressively.
- MCP startup failure: run `python server/mcp_server.py --startup-check`.
- FastAPI confusion: check [API Reference](../reference/API_REFERENCE.md) for current endpoints; `/api/probe/*` is disabled/fail-closed.

## M6A local frontend cannot reach FastAPI

If the readonly workbench shows that the API is unavailable, start the local API with:

```bash
uvicorn server.main:app --host 127.0.0.1 --port 8000
```

For `file://` and localhost static-server usage, the frontend intentionally targets `http://127.0.0.1:8000`. FastAPI CORS is local-only, allows `GET` and `POST`, and does not enable credentials. Do not replace this with credentialed wildcard CORS.

## Windows / Python 3.13 TWSE MIS TLS compatibility

M6D introduces explicit `strict`, `compatibility`, and `unsafe-explicit` SSL policy modes for bounded live commands. Strict remains default; compatibility is explicit and diagnostic; unsafe-explicit must not be used unless you understand TLS verification is disabled. The repository still must not silently disable verification or install a global unverified SSL context.

## M6B source-contract preflight troubleshooting

Use check-only first when diagnosing source-contract readiness:

```bash
python scripts/run_m6b_source_contract_preflight.py --check-only
```

`--check-only` does not perform network calls and does not write artifacts. If an operator explicitly runs live checks, the bounded command is:

```bash
python scripts/run_m6b_source_contract_preflight.py --execute-live-contract-check
```

Live output is written only under `research/live_observation_runs/m6b_source_contract/` and excludes raw endpoint payloads. TLS remains strict by default; M6B does not silently disable certificate verification or install a global unverified SSL context. TLS/certificate failures should be treated as governed diagnostics, not bypassed.


## Windows + Python 3.13 TWSE MIS TLS failures

Symptom: an explicit bounded live observation or M6B source-contract execute run fails with an SSL/certificate verification diagnostic when calling TWSE MIS.

Policy: strict TLS verification is the default and there is no silent fallback. First confirm you are running an explicit bounded live command, not a check-only command. Then retry with compatibility mode only for that bounded command:

```bash
python scripts/run_m5k_live_observation.py --watchlist config/m5k_default_watchlist.json --execute-live-observation --ssl-policy compatibility
```

or:

```bash
python scripts/run_m6b_source_contract_preflight.py --execute-live-contract-check --ssl-policy compatibility
```

Do not use `unsafe-explicit` unless you understand TLS verification is disabled. `unsafe-explicit` is never default, must be explicitly requested by CLI or `TW_MARKET_SSL_POLICY`, and is reported in output diagnostics.

## M6E acceptance troubleshooting

If `python scripts/run_m6e_operator_acceptance.py --check-only` fails, inspect `research/live_observation_runs/m6e_operator_acceptance/latest_operator_acceptance_report.md` first, then rerun the failing child command shown in the JSON report.

## M6G browser/operator E2E troubleshooting

If `python scripts/run_m6g_browser_operator_e2e.py --check-only` reports `skipped_with_caveats`, install browser tooling and rerun:

```bash
python -m pip install playwright
python -m playwright install chromium
python scripts/run_m6g_browser_operator_e2e.py --check-only
```

A skip is acceptable for environments without browser binaries. A failure after browser startup should be investigated as an operator-path regression: frontend payload generation, local FastAPI availability, check-only no-execute guarantees, or SSL policy propagation.

## Browser/operator E2E initially reports missing Playwright or Chromium

Do not treat initial missing browser dependencies as proof that M6G is unsupported. Browser E2E readiness has three layers: Python Playwright package, Chromium browser binary, and OS/system browser dependencies.

Try the explicit browser bootstrap:

```bash
python -m pip install -r requirements-browser-e2e.txt
python -m playwright install --with-deps chromium
```

If Chromium exists but Linux system dependencies are missing:

```bash
python -m playwright install-deps chromium
```

Only keep `skipped_with_caveats` after recording the dependency command attempted, exact blocking error, environment limitation, and recommended next action. The M6G runner does not install dependencies automatically.
