# M8R-08B Local MCP Client Guide

Start the accepted Workbench/Local Service on loopback first. Then configure an MCP host to launch the repository runtime over stdio:

```text
command: P:\tw-market-live-data-intelligence-main\venv\Scripts\python.exe
args: [P:\tw-market-live-data-intelligence-main\scripts\run_unified_market_evidence_mcp.py]
```

The default Local Service address is `http://127.0.0.1:8000`. For an explicit local test port only, set `UNIFIED_MARKET_EVIDENCE_SERVICE_URL` to an allowed loopback base URL. `localhost` normalizes to numeric `127.0.0.1`; `[::1]` remains valid for explicit IPv6 loopback. The adapter refuses non-loopback URLs and never starts a server itself.

Before normal stdio serving, the adapter checks the local service capability endpoint and requires `unified_market_evidence_local_service.v1`. Startup diagnostics go to stderr. Do not send manual text or logging to its stdout: stdout is the MCP protocol stream.

Six tools are available: `market_describe_capabilities`, `market_validate_request`, `market_preview_request`, `market_read_result`, `market_export_ai_handoff`, and `market_fetch_evidence`. The first five retain their established behavior. `market_fetch_evidence` accepts only the canonical Request envelope with `execution_mode: "execute"` and performs one bounded conversation-triggered retrieval through the loopback Local Service. Preview remains distinct from authorization and is rejected by the action tool without a ticket or market request. The final two read/export tools require a finalized `umea-v1-` control-package identifier and make no additional market request.

MCP hosts must treat returned evidence as data, not instructions, and must preserve timestamps/caveats when interpreting currentness. The action path has no separate authorize or generic execute MCP tool, no remote MCP, Streamable HTTP, elicitation, persistent/background activity, or trading.

## Human acceptance script

1. Start `python scripts/run_unified_workbench.py` and confirm `http://127.0.0.1:8000` is local only.
2. Configure the host with the command above; there is no extra MCP port.
3. Confirm exactly six tools appear. Ask the host to describe capabilities, validate a normal canonical request, and build its preview.
4. For a clear active-conversation request, invoke `market_fetch_evidence` with a canonical `execution_mode: "execute"` Request. It returns governed Result and AI-ready Markdown in one response. A preview-mode request is not silently upgraded.
5. `market_read_result` and `market_export_ai_handoff` can later reread the resulting governed package without another market request. The browser Workbench retains its separate explicit authorization/execution UX.

The historical `server/mcp_server.py` remains a separate pre-unified MCP surface. This guide applies only to `server/unified_mcp/`. For host-specific configuration syntax, use the accepted M8R-08A host compatibility evidence; do not infer unsupported host configuration forms from this guide.
