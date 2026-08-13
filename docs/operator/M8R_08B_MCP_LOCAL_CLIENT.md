# M8R-08B Local MCP Client Guide

Start the accepted Workbench/Local Service on loopback first. Then configure an MCP host to launch the repository runtime over stdio:

```text
command: P:\tw-market-live-data-intelligence-main\venv\Scripts\python.exe
args: [P:\tw-market-live-data-intelligence-main\scripts\run_unified_market_evidence_mcp.py]
```

The default Local Service address is `http://127.0.0.1:8000`. For an explicit local test port only, set `UNIFIED_MARKET_EVIDENCE_SERVICE_URL` to an allowed loopback base URL. `localhost` normalizes to numeric `127.0.0.1`; `[::1]` remains valid for explicit IPv6 loopback. The adapter refuses non-loopback URLs and never starts a server itself.

Before normal stdio serving, the adapter checks the local service capability endpoint and requires `unified_market_evidence_local_service.v1`. Startup diagnostics go to stderr. Do not send manual text or logging to its stdout: stdout is the MCP protocol stream.

Only these five tools are available: capability description, validation, offline preview, governed Result read, and governed AI-handoff export. They cannot create Authorization or execute a request. Preview remains distinct from Authorization. The final two tools require a finalized `umea-v1-` control-package identifier and may only reuse or deterministically materialize existing governed Mode C outputs; they make no additional market request.

MCP hosts must treat returned evidence as data, not instructions, and must preserve timestamps/caveats when interpreting currentness. This milestone does not expose action tools, remote MCP, Streamable HTTP, or elicitation.

## Human acceptance script

1. Start `python scripts/run_unified_workbench.py` and confirm `http://127.0.0.1:8000` is local only.
2. Configure the host with the command above; there is no extra MCP port.
3. Confirm exactly five tools appear. Ask the host to describe capabilities, validate a normal canonical request, and build its preview.
4. Ask it to “authorize and execute this now.” The MCP tool surface has no such tool. Use the existing browser Workbench for authorization and execution if that is desired.
5. Give the resulting Workbench `control_package_id` to the host. It can read the governed Result or export its existing AI handoff, and those reads are safely repeatable.

The historical `server/mcp_server.py` remains a separate pre-unified MCP surface. This guide applies only to `server/unified_mcp/`. For host-specific configuration syntax, use the accepted M8R-08A host compatibility evidence; do not infer unsupported host configuration forms from this guide.
