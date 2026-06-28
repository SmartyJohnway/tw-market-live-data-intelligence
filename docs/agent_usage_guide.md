# M5FGH local market context closure

This document supports the North Star: a local-first, bounded-watchlist, explicit manual-refresh Taiwan market context center shared by browser UI and AI Agents.

Canonical package: `research/staging/m5f/m5f_canonical_market_context_01/`. Read `canonical_market_context.json` first, then derived snapshot, observations, AI context pack, briefing, source health, capability summary, lineage, validation report, and manifest.

Safety rules: no investment advice, no trading signal, no target price/ranking, no full-market claim, no realtime guarantee, no production-current-state claim. Always quote source `TWSE_OpenAPI`, source date `2026-06-26`, `historical/stale` badge, and caveats `not_realtime_guaranteed`, `not_trading_signal`, `not_production_current_state`, `source_risk_present`, `freshness_must_be_displayed`.

Safe local workflows: validate with `python scripts/validate_m5f_canonical_market_context_package.py --package-dir research/staging/m5f/m5f_canonical_market_context_01`; run local demo with `python scripts/run_m5fgh_local_product_demo.py --check-only`; preview via `frontend/readonly-preview/M5EMarketContextPreview.html`; start FastAPI with `uvicorn server.main:app`; start MCP with `python server/mcp_server.py`.

Readonly tools/endpoints: FastAPI `/api/context/canonical`, `/api/context/snapshot`, `/api/context/source-health`, `/api/context/capability-summary`, `/api/context/briefing`; MCP `get_canonical_market_context`, `get_source_health`, `get_capability_matrix`, `get_source_catalog`, `get_latest_market_snapshot`, `get_watchlist_observations`, `get_ai_context_pack`, `get_chatgpt_briefing`. `check_bounded_market_refresh_readiness` is check-only and does not use network or writes.

Network use requires future explicit M5I authorization. Do not reuse consumed M5B authorization. Do not run live probes, production refresh, generated artifact refresh, frontend publication, broker/auth activation, full-market scans, or polling loops in this closure.

Agent handoff for Codex/Jules/Claude/Cursor/VS Code: cite package path, exact symbols 0050/00929/2330, source date, manifest hash, validation command, changed files, and forbidden-path check. Missing artifacts fail closed. Preserve last-known-good canonical package on source failure.

Failure playbook: malformed/missing TWSE OpenAPI rows, TPEx failures, TWSE MIS block/cookie/rate-limit/session issues, Yahoo suffix/identity/Japan OTC mismatch, stale/delayed data, partial targets, malformed evidence, manifest mismatch, missing canonical package, or consumer disagreement are release blockers until documented and repaired.

Release checklist: compile/tests, deterministic rebuild, manifest verification, exact symbols/source/date/value checks, frontend/API/MCP consistency, no forbidden paths, no network behavior, no frontend/public or research/generated writes, no M5B/M5C/M5D mutation, safety language, docs consistency, no PR merge.

## M5FGH repair notes

Serve the frontend preview from the repository root with `python -m http.server 8000`; do not rely on `file://` because browser origin rules may block package fetches. MCP product consumption is readonly; the legacy M3G live evidence execution tool is not listed as an M5F product refresh path and is disabled pending future M5I authorization. The M5B authorization was already consumed and must not be reused.
