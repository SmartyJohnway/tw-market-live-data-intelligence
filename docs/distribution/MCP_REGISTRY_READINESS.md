# MCP registry readiness

The repository has not been submitted to an MCP registry. This document is a
readiness note, not a registry manifest or publication claim.

## Current declaration

- Launcher: `python scripts/run_unified_market_evidence_mcp.py`
- Transport: local stdio client to the loopback Local Service
- Tool count: exactly six
- Authentication: no remote account or broker authentication is provided
- Network behavior: no startup market fetch; execution is explicit and bounded
- Product boundaries: no trading, polling, scheduler, background refresh, or
  model-selected URL/executor

## Before any registry submission

1. Publish an approved release tag and public prerelease/release if required.
2. Revalidate the exact tagged commit and its Git-tree-bound manifest.
3. Supply registry-specific metadata from the published contract, without
   claiming realtime guarantees or external execution support beyond evidence.
4. Complete owner review for security, support contact, licensing, and
   disclosure requirements.
