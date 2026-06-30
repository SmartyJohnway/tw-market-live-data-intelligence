# M5OP Operator Workflow — Frontend Product UX and Operator Runbook

This runbook defines the normal local Mode C workflow for a human operator. It does not add sources, trading logic, broker authentication, polling, scheduler behavior, full-market scans, or automatic orders.

## Daily usage

1. **Start FastAPI locally** from the repository root:
   ```bash
   uvicorn server.main:app --host 127.0.0.1 --port 8000
   ```
2. **Open frontend workspace** at `http://127.0.0.1:8000/frontend/readonly-preview/M5KLocalAIWorkbench.html` when served by the local app/static server setup, or open the file from `frontend/readonly-preview/` for static inspection.
3. **Check canonical context** in **Mode A**. Confirm the M5F source path, source date, symbols, caveats, and the canonical / not live warning.
4. **Use Mode A** when the task only needs reviewed historical canonical context. Do not infer current market state from M5F.
5. **Review the watchlist**. Confirm category grouping, display order, enabled/disabled state, symbol, display name, market, instrument type, adapter, tags, notes, and latest local observation status.
6. **Use Mode B** to validate the watchlist and plan routes. Mode B is plan-only: it shows adapter routes, source capability, unsupported/risky routes, and the no-network confirmation.
7. **Use Mode C** only when a bounded live observation is needed. Click the explicit execution button once, review observation status, value semantics, `reference_only`, source timestamp, retrieved-at time, freshness, delay, caveats, failures, and recommended next step.
8. **Generate conversation context** after reviewing observations. Use the frontend buttons to build context, inspect the summary and Markdown preview, then copy JSON or Markdown or download either file.
9. **Paste context into ChatGPT** and discuss caveats, source reliability, and follow-up investigation. The context is temporary discussion input, not canonical data and not a trading signal.

## Interpretation guide

- `ok`: A normalized observation row was produced. It is current-like only if its caveats, source timestamp, retrieved-at time, freshness, and delay fields support that interpretation; realtime is not guaranteed.
- `reference_only`: The value is a fallback/reference observation. Do not treat it as current market price.
- `value_unavailable`: The route completed without a usable value. Inspect source caveats and failure details before retrying.
- `failed`: The adapter/source failed or rejected the route. Use the failure reason and recommended next step.
- `stale`: The source timestamp or freshness assessment indicates stale data. Do not present it as current.
- `closed-session`: The output may reflect a closed market session rather than active trading.
- `not_realtime_guaranteed`: No displayed value is guaranteed realtime unless verified by contract fields.
- **Source caveats**: Legal, maintenance, delay, unofficial endpoint, missing-field, session, and availability warnings from the source/adapter matrix or observation contract.
- **Adapter caveats**: Route-specific limitations such as unsupported market/type, front-month futures selection constraints, fallback semantics, or fragile browser endpoint behavior.

## Safety rules

- No recommendation.
- No ranking.
- No target price.
- No buy/sell/hold.
- No broker/auth credentials.
- No automatic orders.
- No polling.
- No scheduler.
- No full-market scan.
- M5F is canonical but not live.
- M5K/M5L/M5N are live-observation only and not canonical.
- Conversation context must not include raw endpoint payload.
- Level 2 live observation must not mutate M5F, `frontend/public`, `research/generated`, production paths, or prod paths.

## Troubleshooting

- **FastAPI not running**: Start `uvicorn server.main:app --host 127.0.0.1 --port 8000`, then reload the frontend.
- **No latest observation available**: This is normal before Mode C execution. Use Mode B plan first, then execute a bounded observation only if needed.
- **Reference-only value appears**: Treat the row as fallback context, not a current price. Keep the `reference_only` caveat when pasting to ChatGPT.
- **Source returns missing data**: Review `value_unavailable`, failure reason, source capability, adapter caveats, and recommended next step.
- **TX contract not available**: The TAIFEX route may lack a selected/available contract. Check contract month, contract selector, source session, and failure details.
- **Stale/closed-session output**: Check source timestamp, retrieved-at time, freshness, and delay. State explicitly that the row is stale or closed-session.
- **Frontend cannot load API**: Confirm the host/port, browser CORS origin, and that the API endpoints return JSON. Use `/api/health` as a quick check.
- **Conversation context has no observations**: Build context after Mode C or accept that it will contain watchlist-only context with zero observations and caveats.
