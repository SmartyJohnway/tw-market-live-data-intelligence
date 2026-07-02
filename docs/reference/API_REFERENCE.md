# API Reference

Run locally with:

```bash
uvicorn server.main:app --host 127.0.0.1 --port 8000
```

## Current readonly/safe endpoints

- `GET /api/health` — local service health.
- `GET /api/governance` — governance flags.
- `GET /api/matrix` — capability/source matrix summary.
- `GET /api/context/canonical` — M5F canonical context.
- `GET /api/context/snapshot` — M5F latest reviewed snapshot.
- `GET /api/context/source-health` — M5F source health.
- `GET /api/context/capability-summary` — M5F capability summary.
- `GET /api/context/briefing` — M5F briefing Markdown.
- `GET /api/watchlist`, `/api/watchlist/summary`, `/api/watchlist/schema` — local watchlist workspace.
- `GET /api/conversation/context` — M5N conversation context.
- `GET /api/m5l/source-adapter-matrix`, `/api/m5l/source-capabilities` — adapter metadata.
- `GET /api/m5k/watchlist/default` — default watchlist.
- `POST /api/m5k/watchlist/validate` — validate supplied watchlist, no network.
- `POST /api/m5k/conversation/handoff` — create AI handoff payload.
- `GET /api/m5k/live-observation/latest` — read latest local Level 2 artifact.
- `POST /api/m5k/live-observation/plan` — plan routes, no network.
- `POST /api/m5k/live-observation/execute?confirm_live_observation=true` — explicit bounded execution only.
- `GET /api/source-health/latest`, `/api/source-health/schema` — source-health report/schema.

## Disabled / deprecated

`/api/probe/*` routes are excluded from the public schema and fail closed. Do not document or use them as current product endpoints.

## M6A local UX summary endpoints

- `GET /api/m5k/live-observation/history` — readonly summary of local M5K observation artifacts under `research/live_observation_runs/m5k/`; no network calls, no raw endpoint payload exposure.
- `GET /api/source-health/history` — readonly summary of local M5Q source-health artifacts under `research/live_observation_runs/source_health/`; no network calls, no raw endpoint payload exposure.

## M6A local CORS policy

FastAPI permits local browser origins matching `http://localhost:<port>` or `http://127.0.0.1:<port>` for `GET` and `POST` only. Credentials are disabled. The `file://` double-click workflow is handled by frontend API-base detection, which targets `http://127.0.0.1:8000` rather than trusting remote origins.
