# Current Local API Reference

Start the current Unified Workbench / Local Service with:

```bash
python scripts/run_unified_workbench.py
```

Canonical browser entry:

```text
GET /workbench/
```

`/workbench/mode-a/` is a compatibility redirect to the canonical Workbench.

## Unified evidence API

The current Unified router is mounted under `/api/unified`.

| Method | Endpoint | Purpose | Market network |
|---|---|---|---|
| GET | `/api/unified/capabilities` | current Catalog/Route/Executor projection | no |
| POST | `/api/unified/validate-request` | Mode A request + identity validation | no |
| POST | `/api/unified/preview-request` | deterministic Mode B1 preview/plan | no |
| POST | `/api/unified/authorizations` | create server-owned authorization | no |
| POST | `/api/unified/executions` | consume an authorization exactly once | only when explicitly confirmed and route requires it |
| POST | `/api/unified/fetch-evidence` | bounded local-operator action used by MCP | only through governed execution |
| POST | `/api/unified/result-package` | build/verify Mode C Result/Audit output | no additional market fetch |
| GET | `/api/unified/result-package/{id}/audit.json` | verified Audit read | no |
| GET | `/api/unified/result-package/{id}/handoff` | verified AI handoff | no |

Accepted Request contracts are V1/V2/V3; V3 is preferred.

## Persistent Watchlist API

Current durable Watchlist endpoints include:

- `GET /api/watchlists`
- `GET /api/watchlists/{watchlist_id}`
- `GET /api/watchlists/{watchlist_id}/versions`
- `GET /api/watchlists/{watchlist_id}/versions/{version}`
- `GET /api/watchlists/{watchlist_id}/export`
- `POST /api/watchlists/{watchlist_id}/evidence-request-preview`
- `POST /api/evidence-request-previews`
- `POST /api/watchlist-mutations/preview`
- `POST /api/watchlist-mutations/commit`

Persistent mutation and market evidence execution are separate confirmation
domains.

## Local service health / governance

- `GET /api/health`
- `GET /api/governance`

## Compatibility / historical endpoints

The server still contains earlier M5/M6 context, observation, source-health and
compatibility endpoints. They are preserved for historical workflows and tests;
they are **not** the preferred current product API.

`/api/probe/*` routes are excluded from the public schema and fail closed.

Do not infer current product architecture from legacy endpoint names merely
because compatibility code remains in `server/main.py`.
