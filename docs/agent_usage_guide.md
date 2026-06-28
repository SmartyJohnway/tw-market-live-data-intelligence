# Agent Usage Guide

## Goal
Agents should help operate a local-first, bounded-watchlist Taiwan market context center. The first artifact to read is `research/staging/m5f/m5f_canonical_market_context_01/canonical_market_context.json`.

## Citation and quoting rules
When answering, quote the package path, source, source date, freshness/stale status, caveats, and exact symbols. Do not summarize price-like values without saying they are reviewed historical evidence, not realtime prices.

## Safe workflow for Codex/Jules/Claude/Cursor/VS Code agents
1. Run `python scripts/validate_m5f_canonical_market_context_package.py --package-dir research/staging/m5f/m5f_canonical_market_context_01`.
2. Read canonical payload, then derived briefing if needed.
3. Use FastAPI/MCP readonly tools only for consumption.
4. Before handoff, report commands run, files touched, package hashes, and forbidden-path checks.

## Actions that may use network
Only future explicitly authorized refresh work may use market-data network calls. This M5FGH package does not authorize live probes, broker/auth flows, or publication.

## Forbidden agent claims
No investment advice, buy/sell/hold, target price, ranking, full-market coverage, realtime guarantee, or production-current-state claim.

## Handoff checklist
Include branch, commit, validation output, exact symbols, source date, caveats, and whether `frontend/public`, `research/generated`, M5B, M5C, or M5D changed.
