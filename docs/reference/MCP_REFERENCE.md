# Unified MCP Reference

## Start

First complete the [source first-run sequence](../operator/QUICK_START.md#source-first-run):
install dependencies, initialize installation state offline, then start the
loopback Local Service. Unified MCP is its stdio adapter; it does not start the
service. Use the same HOME / STATE_ROOT in both terminals. Security Master ACTIVE
is required for identity-dependent operations, not for startup-check.

With Local Service running, verify `python scripts/run_unified_market_evidence_mcp.py --startup-check`.
Then configure the MCP host to run:

```bash
python scripts/run_unified_market_evidence_mcp.py
```

Transport is local stdio. Starting MCP does not fetch market data.

## Current tool surface

Exactly six governed tools are exposed:

1. `market_describe_capabilities`
2. `market_validate_request`
3. `market_preview_request`
4. `market_read_result`
5. `market_export_ai_handoff`
6. `market_fetch_evidence`

Do not treat earlier M5/M6 MCP tool lists as the current product surface.

## Current request authority

Accepted:

- `unified_market_evidence_request.v1`
- `unified_market_evidence_request.v2`
- `unified_market_evidence_request.v3`

Preferred: `unified_market_evidence_request.v3`.

`market_fetch_evidence` accepts V3, but route execution still depends on
current Catalog/Route/Executor truth and the normal authorization/execute-once
boundary.

## Semantics

- describe/validate/preview are not market execution;
- preview is not authorization;
- fetch is a bounded action, not a polling primitive;
- read/export operate on governed materialized artifacts and do not imply
  another source call;
- V1/V2 remain compatibility contracts;
- historical persisted artifacts retain their stored version.

## Current Phase H boundary

V3 being preferred does not make all Phase H routes executable. The current
active H1 product slice is TPEx attention only. H2/H3 remain non-executable
where routing authority says blocked/plan-only/inactive.

## Safety

No seventh tool, scheduler, trading, order routing, broker credentials, startup
market fetch, background polling, or realtime guarantee is part of the current
MCP contract.
