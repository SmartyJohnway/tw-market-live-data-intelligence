# Recommended Architecture

Based on our feasibility research and probes into various Taiwan Equity market data sources, here is the recommended architecture for a robust AI workbench.

## Findings

1. **TWSE / TPEx OpenAPI**: Free, high fidelity end-of-day data. Good for historical analysis and end-of-day reports. No live intraday data.
2. **TWSE MIS**: Unofficial fragile live candidate for real-time probing. It requires careful handling of request parameters (`ex_ch`, `delay`, `timestamp`) and headers, and carries a high risk of being blocked if accessed too frequently.
3. **Yahoo Finance**: Unofficial third-party REST endpoint (`query1.finance.yahoo.com`). Provides intraday minute bars and metadata without strict authentication. It is a bounded low-frequency candidate that requires strict identity validation, must preserve caveats, and must fail closed on mismatch. It is not an official exchange authority.
4. **FinMind**: Great structural API for historical quotes and statements. Rate limits apply to free tier. Good for data aggregation but not sub-second realtime.
5. **Fugle / Fubon Neo**: Best for high-frequency trading or true realtime websocket feeds. Requires keys/certificates which limits "zero-config" broad deployment.

## Architecture Suggestion

We recommend a **Hybrid Python Backend + Static Frontend** approach:

1. **Backend Layer (Python + FastAPI + MCP)**
   - Responsible for stateful probing, secrets management (`FINMIND_TOKEN`), and normalized schema enforcement.
   - Exposes `OpenAPI` spec to standard AI Chatbots (e.g. Custom GPTs).
   - Exposes `MCP (Model Context Protocol)` interface locally or via standard transports for Agentic coding tools (like Cursor, VSCode, Claude Desktop).

2. **Frontend Layer (Static Workbench)**
   - A static dashboard providing visual evidence of source capabilities (`capability_matrix.md` and `probe_log.md` compiled to JSON).
   - **No Netlify / Serverless Pass-throughs**: The architecture explicitly avoids public open proxies or serverless edge functions. It relies completely on the local backend and CORS restricted to localhost.

## M5B staging-only evidence flow

M5B confirms the architecture should keep live execution behind a single-use authorization validator, retain only bounded target rows, and emit a staging candidate that cannot promote itself to production. M5C or any frontend/publication path requires a separate explicit authorization.

## M5E controlled publication architecture

Use a three-layer flow: (1) immutable M5D candidate and runtime compatibility audit, (2) explicit future authorization decision plus single-use token validated against Draft 2020-12 schemas, and (3) injectable atomic publisher transactions that can be fully tested under temporary directories. The repository release gate remains check-only and reports authorization absence until a human supplies a future explicit authorization.

## M5FGH product convergence status

PR #59 / M5E is treated as merged upstream. M5FGH converges the reviewed M5C/M5D historical evidence into the current canonical local product line: `research/staging/m5f/m5f_canonical_market_context_01/canonical_market_context.json` is the only source-of-truth payload for browser preview, FastAPI readonly endpoints, MCP readonly tools, and AI briefing artifacts.

North Star: a local-first, bounded-watchlist, explicit manual-refresh Taiwan market context center shared by browser and AI Agents. The package is historical/stale reviewed evidence for 0050, 00929, and 2330 from TWSE_OpenAPI source date 2026-06-26; it is not realtime, not production current state, not full-market coverage, and not a trading signal.

Historical M3 generated artifacts under `research/generated/` remain legacy generated artifacts. M5F is the current canonical consumer package. Bounded live evidence exists in prior governed evidence, so the repo is not fixture-only, but M5FGH does not run new live probes. The only remaining main bundle after this closure is M5IJ for future explicitly authorized refresh execution and final release hardening.

## M5K Level 2 Live Observation Layer

M5K is the Level 2 layer beside, not inside, M5F. M5F remains the Level 1 canonical product context: reviewed, validated, reproducible, historical/EOD, deterministic, promotion-based, and package-oriented. FastAPI, MCP, and the readonly frontend continue to read M5F by default and startup remains network-free.

M5K adds a bounded local AI workflow:

- **Mode A — Canonical Discussion:** AI reads only M5F artifacts for historical, reviewed, deterministic context.
- **Mode B — Manual Live Observation:** a user explicitly executes one bounded observation from a watchlist; the result is written only under `research/live_observation_runs/m5k/latest_observation.json` and never overwrites M5F.
- **Mode C — Conversational Watchlist Workflow:** AI and user create or modify an `m5k_watchlist.v1` artifact, the frontend imports/edits/exports it, the frontend executes one bounded observation, and MCP/FastAPI can read the resulting observation back into the same conversation.

The machine-readable handoff is `m5k_conversation_handoff.v1`. M5K also exposes `m5k_live_observation_plan.v1` so users can validate and inspect source routing without network calls or writes before executing. It contains the watchlist, validation result, frontend actions, and governance caveats. M5K prohibits full-market scans, polling, scheduling, automatic startup refresh, trading recommendations, target prices, ranking, broker integration, authentication, and automatic orders.

### Source Investigation

Endpoints investigated for M5K:

1. **TWSE MIS** — `https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=...&json=1&delay=0`. Accepted for bounded observation candidates for TWSE-listed equities, ETFs, and TAIEX because the existing repository already investigates TWSE MIS and the endpoint supports compact symbol-bounded requests. Limitations: browser-oriented JSON endpoint, realtime status is not guaranteed by M5K, exchange/source timestamp must be displayed, missing symbols are recorded as failures, raw fields are not exposed to consumers, TAIEX must use `tse_t00.tw`, listed instruments must route through `tse_<symbol>.tw`, and TPEx/OTC instruments must route through `otc_<symbol>.tw`.
2. **TWSE OpenAPI STOCK_DAY_ALL** — `https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL`. Retained as an official EOD/reference fallback in source preference metadata, but not used as the primary M5K observation source because M5K is for current bounded observation while this endpoint is EOD/batch oriented.
3. **TPEx OpenAPI** — retained in watchlist source preferences for OTC-like instruments. Initial M5K implementation records source preference but does not silently route unverified OTC live observation through an undocumented endpoint.
4. **TAIFEX** — identified for TX futures. Rejected for initial automatic execution because futures contract mapping and endpoint semantics require a separate verified contract. M5K records TX futures as unsupported in the initial live observation result rather than fabricating data.
5. **Yahoo/third-party/commercial APIs** — not adopted for default M5K because official or semi-official sources are preferred and credentialed APIs must not be hardcoded.

Future recommendations: add a dedicated TAIFEX futures adapter with explicit contract-month semantics; add a verified TPEx live quote route if a stable official endpoint is confirmed; keep source routing per instrument category rather than assuming one source fits all instruments.

## M5L Live Sources Validation extension

M5K Level 2 now treats live sources as adapters below the canonical M5F layer. TWSE MIS and TAIFEX MIS remain Level 2 observation sources only. TAIFEX TX support is implemented as a bounded `TX -> TXF front_month` adapter with contract-month normalization and explicit freshness/delay output. This must not alter M5F canonical semantics or promotion logic.
