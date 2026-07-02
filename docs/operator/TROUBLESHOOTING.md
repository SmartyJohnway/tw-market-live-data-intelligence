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

M6A does not introduce SSL compatibility or unsafe TLS behavior. Strict TLS verification remains the only implemented behavior. A future M6B task may add an explicit compatibility policy, but it must not silently disable verification or install a global unverified SSL context.
