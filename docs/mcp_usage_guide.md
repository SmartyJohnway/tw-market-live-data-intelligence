# Unified MCP Usage Guide (CURRENT)

For the **published `v1.5.1`** product, use the supported six-tool Unified MCP:
[Unified MCP Reference](reference/MCP_REFERENCE.md),
[MCPB Distribution](distribution/MCP_DISTRIBUTION.md), and
[Operator Quick Start](operator/QUICK_START.md).
The previous M5F `server/mcp_server.py` tool examples were **legacy
engineering-era interfaces**, not the current public product tool contract.
Those historical interfaces/acceptance notes may still exist in source and
historical documents; this guide does not claim they were deleted.

## Published installation

The frozen Windows MCPB package:
[`v1.5.1` Release](https://github.com/SmartyJohnway/tw-market-live-data-intelligence/releases/tag/v1.5.1).
Check the SHA-256 in [publication record](release/V1_5_1_RELEASE_PUBLICATION.md),
then import via a local MCPB-capable client. It is not a hosted API and does
not acquire live market data simply by starting.

For developers using source, first initialize installation state offline,
start the loopback Local Service, then verify the Unified MCP stdio adapter:

```powershell
python -B scripts/run_unified_market_evidence_mcp.py --startup-check
python -B scripts/run_unified_market_evidence_mcp.py
```

The second command is the MCP client's stdio subprocess, not a replacement
for the running loopback service. Use the same HOME/STATE_ROOT. A fresh
Security Master may correctly be `NOT_INITIALIZED` for identity-dependent
operations; starting MCP does not activate it.

## Exactly six current governed tools

1. `market_describe_capabilities`
2. `market_validate_request`
3. `market_preview_request`
4. `market_read_result`
5. `market_export_ai_handoff`
6. `market_fetch_evidence`

`market_fetch_evidence` is a **bounded execute-once** operation permitted only
under the current Catalog/Route/executor and explicit authorization contract.
Validate and preview do not authorize a fetch. Read/export do not imply a
new source call. Unified Request V3 is preferred; V1/V2 are retained
compatibility authorities.

No background scheduler, polling, silent market fetch, trading, broker,
model-chosen URL/executor, full-market scan or realtime guarantee exists in
the current published MCP contract.

## Legacy M5F notes

The former M5F command `python server/mcp_server.py` and its `get_*`
readonly/context-tool vocabulary belong to older M5 engineering history,
**not** the current six-tool Unified MCP user instructions. Refer to
the accepted [engineering history](release/README.md) when tracing them.
Do not treat an old test or snapshot as current tool discovery.
