# MCP-01 — Readonly Context Tools First

## Final status

Completed. The default MCP server now exposes only readonly local context tools and does not import, list, or execute live probe functions.

## Scope

Files changed:

- `server/mcp_server.py`
- `tests/unit/test_mcp_server.py`
- `docs/reviews/MCP_01_READONLY_CONTEXT_TOOLS_FIRST.md`

## Behavior

The MCP server now lists these readonly tools only:

- `read_latest_market_snapshot`
- `read_watchlist_observations`
- `read_ai_context_pack`
- `read_chatgpt_briefing`
- `read_m3g_caveats_register`
- `read_source_contract_baseline`

Every tool response includes governance metadata showing:

- `execution_mode: readonly_local_artifact_read`
- `network_calls: false`
- `production_refresh: false`
- `frontend_refresh: false`
- `live_probe_execution: false`

Readonly tools read local artifacts from disk and return structured JSON text through MCP. JSON artifacts are parsed into JSON objects; Markdown artifacts are returned as strings.

Missing local files fail closed with `status: missing_file` and a clear error message instead of an unstructured crash.

Legacy live probe tool names return `status: unavailable` with an explicit MCP-01 readonly-mode error. The MCP module no longer imports live probe modules.

## Non-goals

MCP-01 did not:

- run live probes;
- run `scripts/run_all_probes.py`;
- run controlled live probe execution;
- write `research/generated/*` artifacts;
- write `frontend/public/*` artifacts;
- perform production refresh or staging writes;
- enable FinMind, Fugle, Fubon, broker, or authenticated APIs;
- perform full-market scans;
- produce trading signals, recommendations, or buy/sell/hold outputs.

## Validation commands

- `python -m compileall server tests`
- `pytest -m "not network" tests/unit/test_mcp_server.py`
- `pytest -m "not network"`

## Next recommended step

MCP-02-EXPLICIT-CONTROLLED-LIVE-PROBE-TOOLS

MCP-02 should only be considered after MCP readonly behavior is accepted. Any future live probe MCP surface must require an explicit tool name, explicit confirmation, bounded controlled runner semantics, and must not directly expose legacy broad probes.
