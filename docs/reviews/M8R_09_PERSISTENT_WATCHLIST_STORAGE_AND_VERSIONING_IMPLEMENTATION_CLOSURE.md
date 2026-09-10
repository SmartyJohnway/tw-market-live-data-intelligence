# M8R-09 Persistent Watchlist Storage and Versioning — Implementation Closure

Baseline: `458e240d0ba97867795568016c82c3f9cb8fc191`
Validated code commit: `1d68940355a9268053f2f786e3abbf47d9b8a797`
Validated code tree: `058a23d025bcea7e48b8c5b2274cec680a476917`

## Decision

`M8R_09_CLOSED_READY_FOR_M8R_10_PREFLIGHT`

M8R-09 is installation-local SQLite user state. It is not a market-data
executor, scheduler, cache, or Unified MCP mutation surface.

## Final governance correction

- Preview documents are schema-validated before persistence and again after
  SQLite read. Their content hash excludes `content_sha256`; the embedded hash,
  database hash, and caller confirmation hash must agree.
- Mutation commands use strict command-specific typed branches. Unknown caller
  fields, prompts, conversations, and raw legacy payloads are never persisted.
- Legacy import accepts only governed `m5n_watchlist.v1` / `m5k_watchlist.v1`
  shapes, persists only normalized accepted entries and bounded provenance, and
  defers unsupported identities.
- SQLite enforces zero-or-one active default. Default transfer and rollback are
  explicitly previewed and committed atomically. Revision and current-state
  reads schema-validate and verify hash-chain integrity before returning data.

## Exact-code validation

An external `git clone --no-local` checked out the exact validated commit and
installed `requirements-lock.txt`. Environment verification, both Skill
validators, portable catalog sync, runtime/Skill/Guide drift validation,
watchlist/legacy/Identity/Mode A/B focused tests (`97 passed`), integrity
verification, compileall, and `NOT_INITIALIZED` clean-install behavior passed.

Default CI on that same clone completed with `2351 passed, 69 failed, 18
skipped`. The clean baseline was `2328 passed, 69 failed, 18 skipped`.
Normalized pytest node-set comparison found 69 unchanged historical failures,
zero resolved nodes, and `new_failure_nodes = []`. The retained failures are
inherited non-blocking fixture/provenance debt and are outside this tranche.

No market network request, Security Master mutation, background behavior,
M8R-10 implementation, or v1 release occurred. The next authorized action is
M8R-10 preflight only.
