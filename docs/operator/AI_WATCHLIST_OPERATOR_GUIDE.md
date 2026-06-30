# AI Watchlist Operator Guide

## Normal offline flow

1. Inspect or edit `config/m5k_default_watchlist.json` as JSON.
2. Validate the watchlist with `pytest -q tests/unit/test_m5n_watchlist_workflow.py` or through MCP `validate_watchlist()`.
3. Start FastAPI with `uvicorn server.main:app --host 127.0.0.1 --port 8000`.
4. Open `frontend/readonly-preview/watchlist-workspace.html` from the local preview server context.
5. Use Mode B planning before any explicit observation.
6. Build conversation context with `python scripts/build_m5n_conversation_context.py`.

## Safety rules

- Do not treat observations as realtime unless freshness has been verified.
- Do not promote live observations into M5F.
- Do not run automatic refresh or background polling.
- Do not add credentials, cookies, API keys, or broker sessions to the watchlist.
- Do not infer buy/sell/hold, rankings, or price targets from watchlist observations.

## Readonly endpoints and tools

FastAPI readonly endpoints:

- `/api/watchlist`
- `/api/watchlist/summary`
- `/api/watchlist/schema`
- `/api/conversation/context`

MCP readonly tools:

- `get_watchlist()`
- `get_watchlist_summary()`
- `validate_watchlist()`
