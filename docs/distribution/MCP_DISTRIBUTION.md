# Unified MCP distribution

TW-Market Live Data Intelligence provides a local, stdio-based Unified MCP
server. It does not introduce a hosted market service.

## Windows MCPB download

The V1 Windows bundle is published with the immutable
[`v1.0.0` release](https://github.com/SmartyJohnway/tw-market-live-data-intelligence/releases/tag/v1.0.0):

- [MCPB bundle](https://github.com/SmartyJohnway/tw-market-live-data-intelligence/releases/download/v1.0.0/tw-market-unified-mcp-v1.0.0-win-x64.mcpb)
- [SHA-256 sidecar](https://github.com/SmartyJohnway/tw-market-live-data-intelligence/releases/download/v1.0.0/tw-market-unified-mcp-v1.0.0-win-x64.mcpb.sha256)

The bundle was validated on Windows and is intentionally labelled `win-x64`.
It starts the existing Unified MCP over stdio and requires no market credential
merely to start. A fresh installation has no active Security Master and reports
`NOT_INITIALIZED` until an operator explicitly initializes one.

## Tools

The MCP surface has exactly six governed tools:

1. `market_describe_capabilities`
2. `market_validate_request`
3. `market_preview_request`
4. `market_read_result`
5. `market_export_ai_handoff`
6. `market_fetch_evidence`

The familiar local launcher remains available from a source checkout:

```bash
python scripts/run_unified_market_evidence_mcp.py
```

## Boundaries

This distribution preserves the V1 product contract: local stdio transport,
explicit validation and preview, and one bounded execution only after explicit
authorization. It does not provide trading, order routing, a scheduler,
background polling, automatic Watchlist execution, or a realtime guarantee.

## Registry metadata

The proposed official MCP Registry identity is
`io.github.smartyjohnway/tw-market-live-data-intelligence`. The Registry is a
preview service, and publication requires the repository owner's GitHub device
authorization through the official `mcp-publisher` tool. Until that step is
completed, use the MCPB asset above as the supported distribution path.

The release asset is bound by SHA-256:

```text
c60f2fbbfb2b4d34191d84bc5631dc7df27f39aaa7dd61c0a94f41465b7e529b
```

This artifact supplements the immutable V1 Git release; it does not redefine
the release commit or its Git-tree-bound release manifest.
