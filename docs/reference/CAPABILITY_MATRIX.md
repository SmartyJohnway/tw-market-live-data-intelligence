# Capability Matrix

| Capability | Primary artifacts | Mode | Level | Network behavior | Write behavior | Notes |
|---|---|---|---:|---|---|---|
| Canonical context | M5F package | A/C | 1 | None for read/validate | Reads only during validation | Historical reviewed baseline |
| Planning | watchlist + adapter matrix | B | 2 | None | No writes | Validates route feasibility |
| Bounded observation | M5K latest observation | B/C | 2 | Explicit manual only | Writes under `research/live_observation_runs/` | Non-canonical temporary context |
| Source health | M5Q report | B/C | 2 | Check-only none; execute manual bounded | Writes source-health run artifacts on execute | healthy/degraded/failed/unsupported |
| Conversation package | M5N context | C | 1/2 | None | Local temporary conversation context | AI handoff with caveats |
| FastAPI | `server/main.py` endpoints | A/B/C | 1/2 | Startup none | Readonly except explicit bounded endpoints | Local workbench API |
| Frontend | readonly preview | A/B/C | 1/2 | Browser calls local FastAPI | No `frontend/public` writes | Operator UI |
| MCP | `server/mcp_server.py` tools | A/B/C | 1/2 | Startup none | Readonly except explicit bounded tool | AI tool integration |
| AI handoff | Conversation Package Markdown/JSON | C | 1/2 | None | Local file generation | No trading outputs |
