# M8R-10 Watchlist and Evidence Workbench Integration — Preflight

## Decision

M8R-10 may proceed as a bounded implementation milestone. This preflight changes no runtime, schema, persistence, MCP, or market-data behavior. Its decision is `READY_FOR_M8R_10_WATCHLIST_EVIDENCE_WORKBENCH_IMPLEMENTATION`.

The existing `frontend/unified-workbench/` is the canonical v1 workbench. It already owns the visible Mode A validation, Mode B1 preview, Mode B2 authorization/Execute Once, and Mode C Result Explorer flow. M8R-10 must extend that surface; it must not create a third workbench. `/workbench/` is the proposed canonical route and `/workbench/mode-a/` remains a compatibility alias/redirect decision for the implementation tranche.

## Authority and composition boundary

`data/watchlists/watchlists.sqlite3`, through M8R-09's installation-local store and API, is the sole durable watchlist authority. Browser storage is only ephemeral UI state. For Taiwan cash instruments, the durable identity is ISIN; `MARKET:CODE` is current listing/routing context only.

The implementation should add a server-owned, read-only composition boundary, conceptually `POST /api/watchlists/{watchlist_id}/evidence-request-preview`. It receives a watchlist ID, exact version, selected entry UUIDs, data needs, response preferences, and execution mode. It reads the verified watchlist revision and the current Identity Service projection, then creates a normal `unified_market_evidence_request.v1` for the existing Mode A validator. It accepts neither a SQLite path nor raw database payload, cached browser identity, raw prompt, or market observation as authority.

The generated targets use `input = instrument_id` (ISIN), `resolution_requirement = exact`, and `client_target_reference = watchlist_entry_id`. `market_hint` may come only from the current Identity Service projection. The selected version and revision hash are frozen before validation; later mutation to version N+1 cannot modify a request built from N.

Unified Request v1 deliberately carries no undefined watchlist database fields. A server-owned selection provenance sidecar (or a governed Mode C audit extension) must bind watchlist ID/version/revision hash, selected entry UUIDs and ISINs, request ID, composition time, and request hash. `persistent_watchlist_reference` remains a legacy request-scoped compatibility projection for old 03C/03D consumers, never a database locator or a route to direct SQLite access.

## User interaction and safety model

The primary UI is a simple request builder. Raw Unified Request JSON remains an advanced mode, but both paths use the same validation, preview, authorization, execution, Result, and handoff pipeline.

There are three independent confirmations:

1. Watchlist mutation preview/confirmation changes only local persistent state through the existing M8R-09 preview and commit endpoints.
2. Evidence authorization approves the exact previewed evidence plan.
3. Network Execute Once confirms one bounded market action.

No confirmation implies another. Loading a watchlist, composing a request, validation, preview, Result read, and handoff never call a market source. Any material input or selection change invalidates downstream validation, preview, authorization, execution, and Result state. If a source watchlist later changes, the already-composed request remains frozen and the UI shows a stale-source warning with an explicit rebuild action.

The state model is: `BOOT`, `SECURITY_MASTER_UNAVAILABLE`, `WATCHLIST_READY`, `SELECTION_DIRTY`, `REQUEST_COMPOSED`, `VALIDATED`, `EVIDENCE_PREVIEWED`, `AUTHORIZED`, `EXECUTION_CONFIRMATION_REQUIRED`, `EXECUTING`, `EXECUTED`, `RESULT_READY`, `MUTATION_PREVIEW`, `MUTATION_CONFIRMATION_REQUIRED`, and `CONFLICT_OR_EXPIRY`. Conflict, expiry, or stale identity context requires reload, rebuild, and reconfirmation; no silent retry/rebase is permitted. Controls must be keyboard-operable and explain disabled prerequisites.

## Selection and identity policy

An ambiguous identity requires explicit candidate selection. A known unsupported cash instrument stays visible and can remain persisted, while its non-executable state remains visible and it is never silently executed or removed. An unresolved persisted entry remains visible. A successor requires Review Migration followed by an M8R-09 mutation preview and explicit commit. `enabled` means selection preference, not executability.

Temporary targets are not persistent. Promotion is an explicit Add to Watchlist action followed by M8R-09 preview, identity/listing/warning display, confirmation, and commit. A mixed request orders persistent selection first then temporary targets. Equivalent ISIN duplication retains the persistent entry as source, suppresses the temporary duplicate visibly, and keeps every target reference unique.

The M8R-09 storage cap (500), the Workbench selection cap, and Unified execution bounds are distinct. The current Capability Catalog default target limit is 10 and hard target limit is 50. An over-bound selection must ask the user to reduce the set (or explicitly select a bounded first subset); it must not auto-split, batch, schedule, or run in the background.

## Existing surfaces and compatibility

Capability display must use `/api/unified/capabilities` or the canonical catalog. UI presets are mappings rather than a second capability authority. The Result Explorer shows the canonical Result/Audit and, once implemented, selection provenance. It does not write results into notes or cache market values. AI handoff uses server-owned Mode C outputs only and never exposes raw SQLite, full notes, or unselected entries.

The following remain compatibility or historical surfaces, not M8R-10 authority: `/api/watchlist*`, `/api/m5k/*`, legacy M5K MCP tools, `frontend/readonly-preview/watchlist-workspace.html`, `frontend/M5KLocalAIWorkbench.html`, and legacy `persistent_watchlist_reference`. Their retirement/redirect policy is an implementation decision; M8R-10 must not route new execution through them. The Unified MCP contract stays exactly six tools and needs no watchlist-specific tool.

## Implementation order and acceptance

1. 10-01: add and test the read-only watchlist-to-request composition contract.
2. 10-02: integrate watchlist read/mutation preview/commit UI through existing M8R-09 APIs.
3. 10-03: integrate builder, provenance, A/B/C state flow, and compatibility route decision into the existing Workbench.
4. 10-04: perform separately authorized, bounded end-to-end acceptance; market execution remains explicit and never automatic.

The implementation must prove persistent-only, temporary-only, mixed/deduplicated, and post-composition mutation flows; M8R-09 CRUD/concurrency/expiry; unresolved/ambiguous/successor/unsupported/Security-Master-unavailable paths; schema and Mode A validation; B1/B2 boundaries; Mode C no-extra-call handoff; and the unchanged six-tool MCP contract.

## Deferred work

This preflight does not authorize new MCP tools, background refresh, scheduler/polling, automatic watchlist execution, market data stored in watchlist notes, TAIFEX activation, Security Master acquisition, Phase G, or V1 release work. `owner_decisions` is empty: the existing authorities provide sufficient direction for the planned implementation slices.
