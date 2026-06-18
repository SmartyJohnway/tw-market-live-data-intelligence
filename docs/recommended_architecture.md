# Recommended Architecture

Based on our feasibility research and probes into various Taiwan Equity market data sources, here is the recommended architecture for a robust AI workbench.

## Findings

1. **TWSE / TPEx OpenAPI**: Free, high fidelity end-of-day data. Good for historical analysis and end-of-day reports. No live intraday data.
2. **TWSE MIS**: Usable for real-time probing but requires careful handling of request parameters (`ex_ch`, `delay`, `timestamp`) and headers. High risk of being blocked if accessed too frequently.
3. **Yahoo Finance**: Highly reliable REST endpoint (`query1.finance.yahoo.com`). Provides intraday minute bars and metadata without strict authentication. Excellent candidate for low-frequency polling.
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
