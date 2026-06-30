# Troubleshooting

- Dependency errors: run `python -m pip install -r requirements.txt`.
- Syntax/import errors: run `python -m compileall scripts server tests` and inspect the first failure.
- Non-network test failure: run `pytest -m "not network" -v` and inspect failing test names before editing behavior.
- M5F validation failure: run the M5F validator and do not mutate M5F unless a separate approved task says so.
- Missing latest observation: normal before explicit Mode B execution; use check-only planning first.
- Source health degraded/failed: treat as source usability evidence, not an operator instruction to retry aggressively.
- MCP startup failure: run `python server/mcp_server.py --startup-check`.
- FastAPI confusion: check [API Reference](../reference/API_REFERENCE.md) for current endpoints; `/api/probe/*` is disabled/fail-closed.
