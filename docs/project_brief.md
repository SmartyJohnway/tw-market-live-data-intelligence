# Project Brief — TW-Market Live Data Intelligence

## Background

Daily market discussion with AI assistants is limited when the assistant cannot reliably access current Taiwan market data. Web search may return stale closing data, dynamically rendered pages may hide live values, and unofficial endpoints may require sessions, cookies, or special headers.

This project investigates how AI systems can obtain Taiwan market information in a legal, safe, reproducible, and maintainable way.

## Primary questions

1. Which Taiwan market data sources are available?
2. Which sources are official, unofficial, commercial, delayed, or real-time?
3. Which sources can be accessed from simple HTTP requests?
4. Which require browser sessions, cookies, JavaScript, WebSocket, SDKs, or API keys?
5. Which are appropriate for ChatGPT conversation workflows?
6. Which are appropriate for local MCP or Codex workflows?
7. What is the best long-term architecture?

## Candidate data needs

- TAIEX / weighted index
- TPEx index
- TSMC 2330
- MediaTek 2454
- Hon Hai 2317
- Quanta 2382
- AI-related watchlist
- Futures / TX near-month
- Market breadth
- Volume / turnover
- Sector performance
- ADR comparison
- Global market context

## Candidate source families

- TWSE official website and OpenAPI
- TPEx official website and OpenAPI
- TWSE MIS
- Yahoo Taiwan Finance
- Yahoo Finance global endpoints
- Goodinfo
- FinMind
- Fugle MarketData API
- Fubon Neo API
- Open Securities APIs
- Browser automation
- MCP/local tools

## Success criteria

The project succeeds when an AI assistant can reliably discuss Taiwan markets using verified, reproducible, maintainable data sources, without relying on stale search summaries or user screenshots as the only data source.
