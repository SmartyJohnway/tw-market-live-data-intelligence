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

V3 being preferred does not make all Phase H routes executable. Catalog support
is semantic scope; selected Route / production executor authority determines
current executability. The following summary describes the current development
line, not the frozen v1.5.0 release artifacts.

| Item | Capability / evidence ID | Current executable scope | Remaining boundary |
|---|---|---|---|
| H1 | `trading_status_context` | TPEx composite: canonical attention and disposition plus source-native cmode; three fixed GETs, retry zero, no fallback. | cmode has unresolved semantics and zero canonical coverage; changed_trading_method, suspension and resumption remain uncovered. No active TWSE H1 route. |
| H2 | `corporate_action_context` | TWSE TWT48U_ALL preannouncement only; at most one GET, retry zero, no fallback; requires the successful same-target H3-derived comparison window. | No full historical coverage or final TWT49U evidence; TPEx inactive; subtype coverage remains incomplete and blocks ordinary-return interpretation. |
| H3 | `recent_performance` | TWSE common shares only; lookback 1..20 completed sessions plus governed end observation; at most three unique STOCK_DAY monthly GETs, retry zero. | TPEx blocked and non-executable; no persistent history accumulation or backfill. |
| H4 | `discontinuity_safety` | Derived from governed H2/H3 evidence; zero-network, no independent request capability or selected executor. | Incomplete corporate-action coverage cannot become ordinary-return clearance. |
| session_status | `session_status` | Modeled / recognized; Catalog support_status remains runtime_executable, but the current Unified route is blocked, with no selected executor; not currently executable. | Local builders consume supplied evidence; authoritative closure retrieval has no approved complete executor. TAIFEX remains provisional. |

H1/H2/H3 execution requires explicit bounded authorization. H2/H3 Owner-controlled
use does not establish provider-approved automation; permission remains
`NOT_ESTABLISHED_TERMS_CONFLICTED`. H4 adds no network call to upstream execution.
`market_describe_capabilities` projects current Catalog / Route / registry truth;
blocked, provisional and modeled states must not be advertised as executable.

## Safety

No seventh tool, scheduler, trading, order routing, broker credentials, startup
market fetch, background polling, or realtime guarantee is part of the current
MCP contract.
