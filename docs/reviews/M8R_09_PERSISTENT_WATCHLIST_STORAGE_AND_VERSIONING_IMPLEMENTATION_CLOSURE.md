# M8R-09 Persistent Watchlist Storage and Versioning — Implementation Closure

Baseline: `458e240d0ba97867795568016c82c3f9cb8fc191`
Implementation commit: `fe5466530308d500ec5f0b6442c973e007e250a1`

## Decision

`M8R_09_CLOSED_READY_FOR_M8R_10_PREFLIGHT`

M8R-09 introduces only installation-local persistent watchlist state. SQLite
is the authority at `data/watchlists/watchlists.sqlite3` (Git ignored); it is
not an evidence executor, scheduler, market-data cache, or MCP mutation
surface.

## Accepted contract

- Cash durable identity is ISIN; `MARKET:CODE` is cached listing/routing
  metadata only. TWSE/TPEX known-but-execution-blocked cash identities remain
  persistable. TAIFEX/derivative durable identity is deferred.
- A watchlist and each entry have immutable UUIDv4 storage IDs. Multiple named
  watchlists and at most one default are supported. Entry uniqueness is one
  active ISIN per watchlist, never a generic upsert.
- Semantic changes use typed preview then explicit commit. The stored preview
  binds the normalized command, exact resolved identity, expected version,
  hash, expiry, and active Security Master release where identity-sensitive.
  Commits are single-use and transactional.
- Current state is paired with immutable full-snapshot revisions. Revisions
  are hash-chained; rollback creates a later revision rather than rewriting
  history. Reads project current Identity Service state without silently
  changing durable state.
- M5N/M5K template import is explicit and resolves only accepted cash ISINs.
  Unresolved, ambiguous, duplicate, and derivative inputs are deferred or
  rejected rather than persisted as legacy routing identifiers.

## Verification

The new M8R-09 suite and retained M5N compatibility suite passed `23 passed`.
The exact committed implementation was checked out through a real external
`git clone --no-local` with no inherited watchlist DB: `13 passed`; a fresh
empty store reported `NO_WATCHLISTS`, persisted/reopened state, and the offline
integrity verifier returned `PASS`.

Clean-clone default CI compared the exact baseline and implementation node
sets. Baseline: `2328 passed, 69 failed, 18 skipped`; implementation:
`2341 passed, 69 failed, 18 skipped, 120 warnings`. The implementation adds
13 passing M8R-09 tests and introduced no failure node. The retained 69-node
set is historical M5/Mode-C/Security-Master fixture and provenance debt, not a
watchlist regression. A primary-worktree run was deliberately not used for the
gate because its ignored historical local Security Master material changes
whether loopback tests skip or attempt startup.

No market network call, automatic retrieval, scheduler, polling, notification,
Security Master mutation, Unified MCP change, M8R-10 implementation, tag, or
v1.0 release occurred.
