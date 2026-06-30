# MCP Reference

Startup check:

```bash
python server/mcp_server.py --startup-check
```

Run for an MCP client:

```bash
python server/mcp_server.py
```

## Current tools

Readonly canonical/context tools include `get_canonical_market_context`, `get_source_health`, `get_capability_matrix`, `get_source_catalog`, `get_latest_market_snapshot`, `get_watchlist_observations`, `get_ai_context_pack`, and `get_chatgpt_briefing` plus backward-compatible `read_*` aliases.

Watchlist/source tools include `get_watchlist`, `get_watchlist_summary`, `validate_watchlist`, `get_conversation_context`, `create_m5k_conversation_handoff`, `plan_m5k_bounded_live_observation`, `read_m5k_latest_live_observation`, `get_m5l_source_adapter_matrix`, `get_m5l_source_capabilities`, `get_source_health_latest`, and `get_source_health_schema`.

`run_m5k_bounded_live_observation` is explicit/manual only and requires `confirm_live_observation=true`; it never promotes to M5F.

Legacy controlled probe tools are fail-closed or compatibility surfaces and must not be treated as normal product operation.
