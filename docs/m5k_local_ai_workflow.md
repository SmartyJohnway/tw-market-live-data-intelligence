# M5K Watchlist and Live Observation Local AI Workflow

M5K is a Level 2 layer for bounded, temporary, conversational market observation. It does not redesign M5F and does not replace canonical artifacts.

## Levels

- **Level 1: M5F canonical product context** — reviewed, validated, reproducible, deterministic, historical/EOD, promotion based, package oriented.
- **Level 2: M5K live observation layer** — explicit, bounded, temporary, conversational, current observation oriented, never canonical, never automatically promoted.

## Workflows

- **Mode A:** AI reads M5F only.
- **Mode B:** user executes one bounded M5K observation.
- **Mode C:** AI and user create a watchlist, frontend imports/edits/exports it, frontend executes one observation, AI reads back the observation.

## Artifacts and APIs

- Default watchlist: `config/m5k_default_watchlist.json`.
- Watchlist schema version: `m5k_watchlist.v1`.
- Conversation handoff schema version: `m5k_conversation_handoff.v1`.
- Observation schema version: `m5k_live_observation.v1`.
- Latest local observation path: `research/live_observation_runs/m5k/latest_observation.json`.
- Plan-only observation path: `/api/m5k/live-observation/plan` and `scripts/run_m5k_live_observation.py --plan-only`; this validates and routes the watchlist without network calls or writes.
- FastAPI endpoints: `/api/m5k/watchlist/default`, `/api/m5k/watchlist/validate`, `/api/m5k/conversation/handoff`, `/api/m5k/live-observation/latest`, `/api/m5k/live-observation/execute?confirm_live_observation=true`.
- MCP tools: `get_m5k_default_watchlist`, `create_m5k_conversation_handoff`, `read_m5k_latest_live_observation`, `run_m5k_bounded_live_observation`.
- Frontend: `frontend/readonly-preview/M5KLocalAIWorkbench.html`; the workbench provides a table editor for enabled/disabled state, symbol, display name, market, instrument type, preferred sources, category, add/remove rows, JSON import/export, plan-only, and explicit execution.

## Current support limitations

Initial execution support is limited to TWSE MIS bounded routes for explicitly marked `market: twse` instruments (`tse_<symbol>.tw`), explicitly marked `market: tpex`/`otc` instruments (`otc_<symbol>.tw`), and TAIEX (`tse_t00.tw`). TX futures/TAIFEX is represented in routing plans but remains unsupported until contract-month mapping and endpoint semantics are verified. Observation payloads intentionally do not expose raw source fields, raw payloads, or response samples to AI/API/MCP/frontend consumers.

## Governance

M5K never writes `frontend/public`, never writes `research/generated`, never promotes to M5F, never starts network activity at startup, never polls, never schedules refresh, and never emits buy/sell/hold/ranking/target-price/broker/order content.
