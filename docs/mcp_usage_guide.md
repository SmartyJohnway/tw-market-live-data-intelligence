# MCP Usage Guide

## Start command
From the repository root run `python server/mcp_server.py`. The server adjusts `sys.path` before importing validators, so this direct command is supported.

## Stdio client example
Configure an MCP stdio server with command `python` and args `["server/mcp_server.py"]`, working directory set to the repository root.

## Readonly M5F tools
- `get_canonical_market_context`
- `get_latest_market_snapshot`
- `get_watchlist_observations`
- `get_ai_context_pack`
- `get_chatgpt_briefing`
- `get_source_health`
- `get_capability_matrix`
- `get_source_catalog`

Every M5F artifact tool validates the package first and fails closed with `package_validation_failed` if manifest, lineage, or derivatives diverge.

## Check-only tool
`check_bounded_market_refresh_readiness` performs no network calls and no writes. It reports that future M5I authorization is required and that M5B authorization is already consumed.

## Disabled legacy execution
`run_m3g04_controlled_live_probe_evidence` is not listed as an M5F product refresh path and returns `legacy_live_tool_disabled_pending_m5i` if called.

## Safe questions
Ask for package caveats, exact symbols, source health, source authority registry, or briefing text. Unsupported questions include live refresh, production publication, broker activation, target prices, rankings, and trading signals.
