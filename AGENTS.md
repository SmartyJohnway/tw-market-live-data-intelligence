# AGENTS.md — AI Collaboration Guide

## Project objective

Research and build an AI-native Taiwan live market data access workbench. The goal is to discover, validate, compare, and document reliable methods for obtaining Taiwan market data usable by AI assistants.

## Operating mode

This is a high-freedom research task. Do **not** assume a preferred solution. Do **not** force TWSE MIS as the answer. Explore, test, document, and compare.

## Required behavior

1. Prefer evidence over assumptions.
2. Keep raw probe results and failure reasons.
3. Distinguish official APIs, unofficial endpoints, commercial APIs, browser-rendered pages, and user-provided screenshots.
4. Never hardcode credentials or API keys.
5. Use low-frequency probing and avoid abusive access patterns.
6. Document timestamp semantics: source time, exchange time, retrieval time, delay status.
7. Preserve reproducibility: command, URL, headers, response status, response sample, and parsing method.
8. If a method is blocked, say exactly how and why.
9. Keep recommendations separate from raw findings.

## Strong prohibitions

- Do not claim a data source is real-time unless verified.
- Do not use yesterday's close as current market data.
- Do not bypass authentication or evade access control.
- Do not scrape aggressively.
- Do not commit `.env`, API keys, account credentials, cookies, or session tokens.

## Definition of done for any probe

A probe is not complete unless it records:

- source name,
- source type,
- URL or SDK/library,
- request method,
- required headers/cookies/session if any,
- status code,
- sample response or failure body,
- parsed fields,
- timestamp fields,
- freshness assessment,
- legal/maintenance risk,
- AI integration suitability.

## Suggested first workstream

Run source discovery and probing in this order:

1. Official TWSE / TPEx sources
2. TWSE MIS candidate endpoints
3. Yahoo Finance / Yahoo Taiwan Finance
4. FinMind
5. Fugle MarketData API feasibility
6. Fubon Neo API feasibility
7. MCP / local tool architecture

## Output discipline

Update:

- `docs/source_catalog.md`
- `docs/capability_matrix.md`
- `research/probe_log.md`
- `docs/recommended_architecture.md`

Do not create empty ornamental files. Add files only when they contain useful findings.
