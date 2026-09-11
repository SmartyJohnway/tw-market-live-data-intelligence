---
name: tw-market-evidence-agent
description: Use for governed Taiwan market-evidence requests through the Unified Market Evidence MCP surface.
---

# Taiwan Market Evidence Agent

Use this Skill when fresh, source-grounded Taiwan market evidence is needed.
The callable interface is the six-tool Unified MCP surface:

`market_describe_capabilities`, `market_validate_request`,
`market_preview_request`, `market_read_result`, `market_export_ai_handoff`,
and `market_fetch_evidence`.

Mode A/B/C describe product workflow concepts; they are not alternate MCP
tools. The canonical request contract is
`schemas/unified_market_evidence_request.v1.schema.json`.

## When to use

Use for current Taiwan-market observations, official EOD evidence, currentness,
session state, execution-relevant identity resolution, or source-grounded
calculations. Do not use for finance theory, non-Taiwan markets, translation,
or when already-provided governed evidence is sufficient and no refresh is
needed.

## Governed workflow

1. Identify conversational intent and requested targets.
2. Call `market_describe_capabilities` when support or market scope is unclear.
3. Author a canonical Unified Request, then call `market_validate_request`.
4. Call `market_preview_request` before any execution-sensitive request.
5. Only for an executable, user-authorized `execution_mode: "execute"` request,
   call `market_fetch_evidence` once. Preview never authorizes execution.
6. Read the governed Result with `market_read_result`; export the same
   AI-ready handoff with `market_export_ai_handoff` when useful.
7. Interpret evidence, citations, coverage, failures, and currentness without
   changing their meaning.

Do not retry outside the governed workflow, silently switch sources, invent
evidence, or turn an unsupported/provisional capability into an execution.

## Persistent Watchlists and temporary targets

The browser Workbench at `/workbench/` can compose a Unified Request from an
installation-local persistent Watchlist. Stored Taiwan cash instruments use
ISIN as durable identity; `MARKET:CODE` is current routing metadata. Selection
is explicit. The entry's `enabled` preference is not implicit execution scope,
although the operator may explicitly choose **Select Enabled**.

Composition is server-owned and offline. It binds the exact watchlist version
and revision hash, resolves identities through the current Identity Service,
preserves watchlist display order, appends temporary request-only targets in
user order, and reports ISIN deduplication decisions. Persistent entries win a
duplicate. Ambiguous or unknown temporary targets require clarification and do
not become a request. Temporary targets remain nonpersistent unless the user
separately previews and confirms an M8R-09 watchlist mutation.

Keep the three confirmation boundaries distinct:

1. watchlist mutation preview and confirmation;
2. evidence-plan authorization;
3. explicit network **Execute Once** confirmation.

A source watchlist change never mutates a frozen composed request. Recompose,
revalidate, and obtain new authorization when the changed state is desired.

## Identity and eligibility

Users may supply `2330`, `台積電`, or `TW0002330008`; do not require them to
know an ISIN. For governed Taiwan cash instruments, `instrument_id` is the
ISIN while `listing_id` and `canonical_target_id` retain `MARKET:CODE` routing
identity. Identity knowledge is broader than execution eligibility: currently
`common_share` and `etf` are cash execution-supported families; known other
instruments can resolve and still fail closed for execution.

Ambiguous identity is not a fuzzy winner: present candidates and obtain the
required clarification.

## Evidence interpretation

- A successful Result is not automatically fresh or realtime. Preserve source
  timestamp, retrieval timestamp, event/trade date, stale/currentness state,
  and `not_realtime_guaranteed` caveats.
- Official EOD is completed-session reference data, never a live quote.
- For partial success, report each provided target/need and each missing need
  with its reason; do not summarize it as wholly successful or wholly failed.
- For source failure, preserve missing coverage, reason codes and citation
  absence. Never fabricate values, retry autonomously, or use an unofficial
  fallback silently.
- TAIFEX support is provisional/non-executable where the capability authority
  says so. This boundary is not a source outage.

## Installation-local Security Master

A fresh installation can legally return `SECURITY_MASTER_NOT_INITIALIZED` (or
the current formal equivalent). Do not fall back to fixtures or ask an end user
to find Candidate B. Direct the operator to the explicit local Security Master
update workflow. There is no scheduler, startup fetch, background polling,
trading, order routing, model-selected URL, or model-selected executor.

## References

- `references/capability_quick_guide.md`
- `references/evidence_semantics.md`
- `references/tool_selection_examples.md`
- `references/current_limitations.md`
- `assets/unified_capability_catalog_portable.json`
