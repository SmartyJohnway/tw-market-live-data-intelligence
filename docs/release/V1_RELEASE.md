# V1.0.0 stable release

The current stable ProductVersion and GitHub Release are
[`v1.0.0`](https://github.com/SmartyJohnway/tw-market-live-data-intelligence/releases/tag/v1.0.0),
published on 2026-09-14. Its immutable annotated tag peels to
`e02bcb125999f542308a75f349c212f0ff3fee83`.

## Product boundary

V1 provides the local Unified Workbench at `/workbench/`, installation-local
Persistent Watchlists, Taiwan identity resolution, request validation,
capability preview, explicit bounded execute-once retrieval, canonical
Result/Audit output, AI-ready handoff, and the exact six-tool Unified MCP
surface.

V1 does not provide trading, order routing, a scheduler, background refresh,
automatic Watchlist execution, or a realtime guarantee.

## Installation and migration

Install `requirements-lock.txt`, run `python scripts/verify_environment.py`,
and check Security Master status before an explicit initialization update. A
fresh installation reporting `NOT_INITIALIZED` is an expected fail-closed
state. Existing schema-1 Watchlists upgrade through the governed migration
path; v0.1 Watchlist import remains explicit.

## Release provenance

The published RC history is
[`v1.0.0-rc.1`](https://github.com/SmartyJohnway/tw-market-live-data-intelligence/releases/tag/v1.0.0-rc.1),
which remains immutable. The stable release was promoted without runtime
feature expansion from the accepted final-promotion candidate.

Phase F is closed. Phase G has not started.
