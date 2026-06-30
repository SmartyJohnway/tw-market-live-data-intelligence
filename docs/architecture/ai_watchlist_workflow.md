# AI Watchlist Workflow, Watchlist Workspace, and Conversation Context

M5N makes the watchlist the shared workspace for AI conversation, frontend display, FastAPI reads, and MCP reads. It does not add market sources and does not change the M5F canonical package.

## Workflow

```text
AI conversation
  -> config/m5k_default_watchlist.json (formal M5N watchlist)
  -> adapter planning (Mode B, no network)
  -> explicit live observation (Mode C only after confirmation)
  -> normalized observations/failures
  -> temporary conversation context
  -> human discussion
```

## Watchlist contract

The formal JSON schema version is `m5n_watchlist.v1`. Each item has:

- `id`
- `symbol`
- `display_name`
- `market`
- `instrument_type`
- `adapter`
- `category`
- `enabled`
- `display_order`
- `tags`
- `notes`

JSON import/export is supported by using the same object shape. CSV is reserved as a future format and is advertised as `csv_future` only; there is no CSV parser yet.

## Read surfaces

- FastAPI: `GET /api/watchlist`, `GET /api/watchlist/summary`, `GET /api/watchlist/schema`, and `GET /api/conversation/context`.
- MCP: `get_watchlist()`, `get_watchlist_summary()`, and `validate_watchlist()` are readonly and make no network calls.
- Frontend: `frontend/readonly-preview/watchlist-workspace.html` reads the same FastAPI endpoints and offers local JSON import/export.

## Conversation context

`python scripts/build_m5n_conversation_context.py` writes:

- `research/live_observation_runs/current_conversation_context/conversation_context.json`
- `research/live_observation_runs/current_conversation_context/conversation_context.md`

The package summarizes the watchlist, observation successes/failures, freshness, source health, risk, and caveats. It intentionally excludes raw endpoint payloads and is temporary conversation context, not canonical M5F.

## Mode boundaries

- Mode A uses M5F only.
- Mode B shows planned routes, supported adapters, and feasibility without network calls.
- Mode C reads the watchlist, latest explicit observations, and conversation package after an explicit observation run.

No automatic refresh, polling, trading signals, recommendations, ranking, target prices, or production mode are introduced.
