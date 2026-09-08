# Unified Market Evidence Agent Usage Guide

This is the current operating guide for AI agents using the local Unified
Market Evidence product. Runtime schemas, the canonical capability catalog,
and registered MCP contracts remain authoritative when details differ.

## Use boundary

Use the product for fresh or official Taiwan-market evidence, identity needed
for execution, EOD reference, currentness/session state, citations, and
source-grounded calculations. Do not call it for general theory, non-Taiwan
markets, translation, or when existing evidence is sufficient and no refresh
is requested.

## Callable interface

The six MCP tools are:

1. `market_describe_capabilities`
2. `market_validate_request`
3. `market_preview_request`
4. `market_read_result`
5. `market_export_ai_handoff`
6. `market_fetch_evidence`

Mode A/B/C are workflow concepts—validate, preview/authorize/execute once, and
Result/handoff—not tool names or JSON parameters.

## Request and execution workflow

Author a `unified_market_evidence_request.v1` request from the conversation.
Users may identify a target by code, name, or ISIN. Validate it, inspect the
preview and capability boundary, and call `market_fetch_evidence` only when the
request is executable, explicitly authorized, and has `execution_mode:
"execute"`. Preview does not authorize execution. A fetch is one bounded
governed action; do not retry or switch sources outside that workflow.

Use `market_read_result` to read the same finalized canonical Result and
`market_export_ai_handoff` to obtain its AI-ready projection. Follow-up
discussion does not itself trigger another fetch; create and authorize a new
request when fresh evidence is genuinely required.

## Identity semantics

For governed Taiwan cash instruments:

- `instrument_id` is ISIN, such as `TW0002330008`.
- `listing_id` and compatible `canonical_target_id` are routing identity,
  such as `TWSE:2330`.
- Identity knowledge is broader than execution eligibility. `common_share` and
  `etf` are the governed cash execution families; other known instruments may
  resolve but remain blocked.

Never choose a fuzzy winner for an ambiguous identity. Present candidates and
obtain clarification.

## Result interpretation

Execution success, freshness, and realtime status are separate facts. Preserve
observation/event timestamps, retrieval time, trade date, source authority,
currentness status, caveats, and citations. Official EOD is completed-session
reference data, not live price. `full_success` never implies realtime.

For partial success, identify each successful target/need and each missing need
with its reason. For source failure, preserve reason and coverage impact; do not
invent values, hide absent citations, retry automatically, or silently use an
unofficial fallback. TAIFEX remains provisional/non-executable where the
capability catalog says so; a capability boundary is not a source outage.

## Installation-local Security Master

A fresh clone normally reports `NOT_INITIALIZED`. Identity-dependent calls must
fail closed through the governed public error rather than fixtures or Candidate
B. The operator initializes or refreshes explicitly:

```bash
python scripts/manage_security_master.py status
python scripts/manage_security_master.py update --live
python scripts/manage_security_master.py history
python scripts/manage_security_master.py rollback RELEASE_ID
```

There is no automatic Security Master update, startup fetch, scheduler,
background polling, persistent watchlist mutation, trading, or order routing.
