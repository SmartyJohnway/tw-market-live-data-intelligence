# MCP registry readiness

The repository **does have an official MCP Registry entry**, independently
verified against the official live Registry API on **2026-11-05**:
[`io.github.SmartyJohnway/tw-market-live-data-intelligence`](https://registry.modelcontextprotocol.io/v0.1/servers/io.github.SmartyJohnway%2Ftw-market-live-data-intelligence/versions/latest).
The Registry returned `version=1.0.0`, `status=active`,
`isLatest=true`. This page is **readiness guidance for any future Registry
version/update**, not an assertion that `v1.5.1` is registered.
The checked-in `server.json` remains `1.0.0` by design.

## Current declaration

- Launcher: `python scripts/run_unified_market_evidence_mcp.py`
- Transport: local stdio client to the loopback Local Service
- Tool count: exactly six
- Authentication: no remote account or broker authentication is provided
- Network behavior: no startup market fetch; execution is explicit and bounded
- Product boundaries: no trading, polling, scheduler, background refresh, or
  model-selected URL/executor

## Before any later registry version/update

1. Publish an approved release tag and public prerelease/release if required.
2. Revalidate the exact tagged commit and its Git-tree-bound manifest.
3. Supply registry-specific metadata from the published contract, without
   claiming realtime guarantees or external execution support beyond evidence.
4. Complete owner review for security, support contact, licensing, and
   disclosure requirements.
