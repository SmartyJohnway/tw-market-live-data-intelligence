# M8R-09 Persistent Watchlist Storage and Versioning Preflight

Baseline: `4b67363cdce50b1d52e55afab2ae95d114fd679a`

Branch: `codex/m8r-09-preflight-persistent-watchlist`

## Decision

The repository is ready for one bounded M8R-09 implementation tranche. No
persistent watchlist implementation, user-state mutation, Security Master
mutation, or market access occurred in this preflight.

The target is an installation-local, cash-instrument watchlist domain backed by
SQLite. It keeps mutable current projections and immutable full-snapshot
revisions in one transaction. ISIN is the durable cash instrument identity;
`MARKET:CODE` remains cached listing/routing metadata. The storage service must
require explicit mutation intent, an optimistic `expected_version`, and a
confirmation binding. It must not execute market requests, monitor, poll,
schedule, or notify.

## Current-state inventory

### Legacy M5K/M5N workspace

`config/m5k_default_watchlist.json` is a Git-tracked default/import template,
not per-installation user state. Although it declares `m5n_watchlist.v1`, its
stored shape is the older three-category layout. `scripts/m5k_common.py`
normalizes that layout into 19 flat items. The current validator accepts both
`m5k_watchlist.v1` and `m5n_watchlist.v1`, enforces a 25-target execution-era
bound, validates symbol/market/basic fields, and has no durable version or
transaction contract.

Legacy item IDs such as `twse:2330` and `tpex:6488` are listing/routing
identities. Items also carry `symbol`, `display_name`, `market`,
`instrument_type`, `adapter`, `preferred_sources`, `category`, `enabled`,
`display_order`, `tags`, and `notes`. JSON import/export is a browser/file
workflow; CSV remains advertised as future-only. No server-side CRUD or
per-installation persistence exists.

The current roles are:

| Surface | Current role | Persistence | Disposition |
| --- | --- | --- | --- |
| `config/m5k_default_watchlist.json` | Repo-tracked default and legacy execution input | Git-tracked template only | Retain as import template and compatibility fixture; never mutate as user state |
| `scripts/m5k_common.py` | M5K/M5N normalize, validate, route, observe, summarize, and conversation-context compatibility | Writes only observation artifacts when explicitly executed | Retain compatibility adapter; persistent domain must not reuse its identity or 25-target storage bound |
| `GET /api/watchlist` | Read normalized default template plus latest observation rows | None | Retain legacy during M8R-09; redirect/adapt in M8R-10 |
| `GET /api/watchlist/summary` | Read summary of default template | None | Retain legacy during M8R-09; realign in M8R-10 |
| `GET /api/watchlist/schema` | Informal M5N schema descriptor | None | Retain legacy; new formal schemas get distinct identities |
| `POST /api/m5k/watchlist/validate` | Validate caller-supplied legacy JSON | None | Retain as import compatibility validator |
| Legacy `server/mcp_server.py` watchlist tools | Read/validate old workspace | None | Compatibility/historical surface, not current Unified MCP authority |
| Unified MCP six-tool server | Market evidence validate/preview/execute/read/export | None | No watchlist CRUD in M8R-09; unchanged |
| `watchlist-workspace.html` | Read server default, browser-local import, export | Browser memory only | Retain read-only preview; replace/adapt in M8R-10 |
| `M5KLocalAIWorkbench.html` / `m5k-workbench.js` | Browser-local edit/import/export and explicit observation | Browser memory only | Legacy workspace; integrate persistent product in M8R-10 |

The focused current-state test completed with `10 passed`; all tested read
surfaces declare zero network calls.

### `persistent_watchlist_reference`

The M8R-03B/03C name is not evidence of a durable object. Its implemented
contract contains a logical `watchlist_id`, a source discriminator, and an
ordered non-empty `enabled_target_ids` array. Fixtures use values such as
`operator_supplied_watchlist`, `wl-fixture`, and listing IDs. The strict 03C
validator does not resolve storage or verify a persisted version. The 03E
projection optionally passes through `watchlist_version`, but the strict input
validator does not currently accept that field.

Current consumers are the 03B/03C validators, watchlist bundle builders, 03D
planning/execution adapters, 03E context projection and validation, fixture
generators, performance runners, and their tests. It is therefore a
request-scoped logical selection binding, with many fixture/historical uses.

Disposition: keep the name and shape as a compatibility contract. Do not make
it the new storage authority and do not break existing fixtures. A future
M8R-10 adapter may construct it from a verified persistent read using the new
immutable `watchlist_id`, a selected revision, and current listing IDs. New
storage/domain schemas remain independently named and versioned.

## Target identity and entry contract

M8R-09 v1 is production-supported for TWSE/TPEX cash instruments only.
Derivatives, indexes without the governed cash ISIN contract, and TAIFEX
identities are explicitly deferred; legacy templates may still contain them
but import must report them as deferred rather than invent a durable ID.

Known cash instruments outside the execution universe may be persisted when
the Identity Service resolves a governed ISIN. `PERSISTABLE` and `EXECUTABLE`
are separate projections. A warrant can therefore remain on a watchlist while
market-evidence execution fails closed as unsupported.

| Entry field | Classification | Contract |
| --- | --- | --- |
| `watchlist_entry_id` | REQUIRED | Opaque UUIDv4 storage identity; not a security identity |
| `instrument_id` | REQUIRED | Normalized ISIN for v1 cash instruments |
| `identity_scheme` | REQUIRED | `ISIN` in v1 |
| `display_name` | CACHED | Last confirmed Identity Service display metadata |
| `cached_market` | CACHED | Current listing market, never identity authority |
| `cached_security_code` | CACHED | Current routing code, never identity authority |
| `cached_listing_id` | CACHED | `MARKET:CODE`, never durable identity |
| `enabled` | REQUIRED | User preference for selectable evidence actions, not exchange lifecycle |
| `display_order` | REQUIRED | Deterministic contiguous integer order in the revision snapshot |
| `tags` | OPTIONAL | User-authored, ordered canonical unique strings |
| `notes` | OPTIONAL | User-authored exact text; never overwritten by identity reconciliation or AI |
| `created_at` / `updated_at` | AUDIT | UTC timestamps set by the domain service |
| `resolved_under_security_master_release_id` | AUDIT | Release used when the identity was confirmed |
| `identity_status` | DERIVED | Current read projection; stored confirmation status may remain in audit metadata |
| `migration_status` | AUDIT | Explicit pending/reviewed successor workflow state |
| `instrument_type` | CACHED/DERIVED | Identity Service projection, not user-editable authority |
| `adapter` / `preferred_sources` | DO_NOT_PERSIST | Current capability/routing decision |
| market values, AI interpretation, raw prompt | DO_NOT_PERSIST | Not watchlist state |

Within one watchlist, one active entry per ISIN is the business uniqueness
rule. A duplicate add returns `WATCHLIST_ENTRY_ALREADY_EXISTS` with the existing
entry reference; it does not silently upsert. The same ISIN may appear in
different watchlists.

Input such as `2330` or `台積電` must resolve through the active Taiwan Market
Identity Service before a mutation preview is confirmable. `NOT_INITIALIZED`,
ambiguous, or not-found results cannot be persisted. Ambiguity requires user
selection followed by a new preview and confirmation.

## Watchlist identity and multiplicity

Use an opaque UUIDv4 `watchlist_id` as immutable storage identity and a mutable
`name` as display identity. UUIDv4 uses the standard library, is easy to audit
and migrate, and avoids both an additional security identifier and a new ULID
dependency.

The v1 product supports one optional default plus multiple named watchlists.
This is the smallest sustainable architecture: fresh installation has
`NO_WATCHLISTS`; creating the first list may designate it default, and changing
the default is an explicit mutation. References survive rename. Arbitrary
cross-user or cloud tenancy is out of scope.

## Storage decision

| Criterion | JSON snapshots + revision files | SQLite |
| --- | --- | --- |
| Atomic current + revision update | Requires careful multi-file protocol | Native single transaction |
| Concurrent writers | External locks and recovery protocol | Transactions plus optimistic version check |
| Immutable revisions | Natural files but chain/current pointer can split | Revision rows protected by domain layer/triggers/tests |
| Backup/export | Human-readable directory | Explicit JSON export required |
| Human readability | High | Lower |
| Schema migration | File-by-file rewrite complexity | Transactional migration with domain schemas |
| Dependency cost | Standard library | Standard-library `sqlite3` |
| Windows behavior | Rename/locking edge cases across files | Well-understood local file locking |
| Clean-install/test isolation | Good | Good with injected root/database path |
| Future local API | Adequate | Strong querying and transaction support |

Recommendation: SQLite at installation-local
`data/watchlists/watchlists.sqlite3`, with the containing path added to Git
ignore during implementation. JSON snapshot/revision directories are the
portable alternative but are rejected for v1 because atomic multi-file current
state plus revision history and concurrent local writers require more custom
recovery machinery. Raw SQLite bytes are not the backup contract; canonical
JSON export of current state and optional history is.

## Versioning and transaction contract

Use a hybrid model:

```text
watchlist current_version = N
  + current normalized entry projection
  + immutable revision N full snapshot
      created_at
      mutation_type
      previous_version
      actor/source
      affected entry/instrument IDs
      confirmation provenance
      canonical content hash
```

Every semantic user mutation is one SQLite transaction that validates the
command, checks `expected_version`, inserts an immutable revision, and updates
the current projection and version. Either all changes commit or none do.
Historical revisions are never updated. Rollback reads an old revision and
creates a new current revision; it never rewrites history.

The domain document schema, immutable revision schema, mutation command/schema,
and storage migration version must be explicit. A database migration number is
not a substitute for the domain contract. Migrations are versioned,
transactional, backed up/exportable, and fail closed on unsupported schemas or
partial chains.

`expected_version` is mandatory for mutation of an existing watchlist. If
current is 7 and expected is 7, a successful command creates version 8. If
expected is 6, the service returns `WATCHLIST_VERSION_CONFLICT`; no last-write-
wins behavior is permitted.

User-state changes increment the version: create, rename, add/remove,
enable/disable, reorder, tags, notes, import, migration confirmation, delete,
restore, and rollback. Same-ISIN name/listing cache reconciliation is a derived
resolution/cache projection and does not increment the user-state version.
Read may compute that projection but must not silently persist or migrate it.
An explicit `system_metadata_reconcile` may update a separate cache generation
atomically without changing the semantic watchlist version.

Retain all revisions in v1. Watchlist deletion uses a tombstone revision;
entry removal is represented in the new snapshot while prior revisions retain
the entry. No automatic compaction or hard delete is included. A future
retention/compaction policy must preserve export and audit guarantees.

## Mutation and confirmation boundary

The storage layer exposes explicit commands, never a generic upsert:

- `create_watchlist`, `rename_watchlist`, `set_default_watchlist`
- `add_entry`, `remove_entry`, `set_entry_enabled`, `reorder_entries`
- `set_entry_tags`, `set_entry_notes`
- `delete_watchlist`, `rollback_watchlist`
- `import_legacy_watchlist`, `confirm_identity_migration`

M8R-09 must implement the domain operations required to prove storage,
versioning, import, and rollback. User-facing workflow polish is M8R-10.

All mutation commands require explicit mutation intent. Creation, add/remove,
identity replacement, bulk import, deletion, and rollback additionally require
a preview bound to exact normalized command content, resolved identities,
current/expected version, affected entries, warnings, and a content hash. Commit
requires explicit confirmation of that exact preview before expiry. Rename,
enabled, order, tags, and notes may use a direct explicit owner action but still
carry `expected_version` and confirmation provenance. AI-assisted actions may
never infer confirmation from conversational mention.

The minimal actor/source enum is `human`, `ai_assisted`, `import`, `migration`,
`rollback`, and `system_metadata_reconcile`. Audit stores operation, UTC time,
old/new version, affected IDs, preview/confirmation ID and hash, and reason
code. It stores no secret, full conversation, or raw prompt.

The temporary promotion flow is:

```text
conversation-local target
  -> current Identity Service resolution
  -> candidate entry and mutation preview
  -> explicit user confirmation
  -> atomic persistent revision
```

Mentioning a symbol never mutates persistence and persistent mutation never
triggers market evidence or network activity.

## Corporate action and release interaction

| Identity event | Stored state | Read projection | Confirmation | User version |
| --- | --- | --- | --- | --- |
| Same ISIN, name change | Keep entry/notes/tags | Show current name and stale cache distinction | No | No |
| Same ISIN, listing metadata change | Keep entry/ISIN | Use current listing/routing projection | No | No |
| Official old ISIN to new ISIN successor | Keep predecessor and migration audit; propose successor | `IDENTITY_MIGRATION_REVIEW_REQUIRED` | Required | Yes after confirmation |
| Missing from latest release / lifecycle uncertain | Keep entry enabled state | Mark unresolved/stale metadata; no routing | No automatic action | No |
| Security Master rollback | Keep durable ISIN | Recompute current projection from selected release | No persistent identity mutation | No |

Snapshot absence never terminates, deletes, disables, or migrates an entry.

## Legacy import and compatibility

Legacy import is parse -> validate -> resolve listing/name/code via the Identity
Service -> deduplicate by ISIN -> report deferred/ambiguous/not-found items ->
preview exact changes -> explicit confirmation -> one new revision. A legacy
`id` is never trusted as durable identity. Partial resolution is reportable;
the user confirms only an explicit accepted subset. Unsupported-known cash
instruments may be included with clear non-executable status. Derivative/index
rows are deferred in v1.

`config/m5k_default_watchlist.json` becomes a repo-tracked `IMPORT_TEMPLATE`
and `LEGACY_COMPATIBILITY_FIXTURE`, not a default mutable seed and never an
automatic first-run write.

## Minimal service/API boundary

M8R-09 should add a local domain service and only the API needed to exercise it:

- `GET /api/watchlists`
- `GET /api/watchlists/{watchlist_id}`
- `GET /api/watchlists/{watchlist_id}/versions`
- `GET /api/watchlists/{watchlist_id}/versions/{version}`
- `POST /api/watchlist-mutations/preview`
- `POST /api/watchlist-mutations/commit`

The two command endpoints cover typed mutations without proliferating unsafe
CRUD/upsert routes. Current `/api/watchlist*` endpoints remain legacy reads in
M8R-09 and are adapted or redirected in M8R-10. No new MCP tool is added in
M8R-09. Persistent read/mutation MCP exposure and its higher-level confirmation
UX are M8R-10 decisions; the Unified six-tool evidence contract remains intact.

Persistent watchlist execution semantics remain separate:

```text
read selected enabled entries
  -> current identity/listing projection
  -> explicit bounded target subset
  -> normal Unified Request preview/authorization/execute-once
```

Display order does not imply execution of all entries. No automatic chunking,
background fetch, refresh, monitoring, scheduler, or notification is allowed.

## Failure model

Required reason-code families are:

- `NO_WATCHLISTS`, `WATCHLIST_NOT_FOUND`, `WATCHLIST_ENTRY_NOT_FOUND`
- `WATCHLIST_VERSION_CONFLICT`, `WATCHLIST_ENTRY_ALREADY_EXISTS`
- `WATCHLIST_SCHEMA_INVALID`, `WATCHLIST_STORAGE_CORRUPT`
- `WATCHLIST_STORAGE_SCHEMA_UNSUPPORTED`, `WATCHLIST_VERSION_CHAIN_BROKEN`
- `WATCHLIST_CONFIRMATION_REQUIRED`, `WATCHLIST_CONFIRMATION_MISMATCH`
- `WATCHLIST_IMPORT_TOO_LARGE`, `WATCHLIST_RESOURCE_LIMIT_EXCEEDED`
- `SECURITY_MASTER_NOT_INITIALIZED`, `IDENTITY_AMBIGUOUS`, `IDENTITY_NOT_FOUND`
- `IDENTITY_MIGRATION_REVIEW_REQUIRED`, `IDENTITY_SCHEME_UNSUPPORTED`

Missing/empty storage is legal `NO_WATCHLISTS`. Corrupt, unsupported, hash-
mismatched, or chain-broken storage fails closed and is never auto-reset.
Security Master availability and watchlist existence are independent states.

## Security and resource bounds

The implementation must contain paths under one configured installation-local
root, reject traversal and symlink/reparse escapes, use parameterized SQL,
enable SQLite foreign keys, define busy/locking behavior, use transactions,
validate every import, and bound JSON depth and size. User text must be rendered
as text, not trusted HTML/script.

Initial limits are deliberately separate from execution bounds:

| Limit | Decision |
| --- | --- |
| Watchlists per installation | 32 |
| Entries per watchlist | 500 |
| Tags per entry | 20 |
| Tag length | 64 Unicode code points |
| Notes length | 4,096 Unicode code points |
| Name length | 120 Unicode code points |
| Import bytes | 1 MiB |
| JSON nesting | 20 levels |

These are storage limits, not a market-execution target bound. The current
Capability Catalog default request limit is 10 and the legacy M5K bound is 25;
neither becomes `WATCHLIST_STORAGE_LIMIT`. Future evidence actions must select
an explicit bounded subset.

## Artifact and consumer impact plan

Implementation will require new formal watchlist domain, revision, mutation,
export/import, and API schemas; a storage/domain module; an installation-root
resolver; `.gitignore` coverage; a minimal FastAPI integration; and tests. The
Identity Service is read-only authority and is consumed, not modified.

Legacy observation, source-health, conversation-context, M7D cross-context,
and M8R-03 bundle consumers remain compatible through adapters. They are not
deleted in M8R-09. M8R-10 will bind persistent reads into the Workbench and
Unified evidence request selection and retire misleading current-authority
documentation/surfaces after compatibility acceptance.

Proposed authority chain:

```text
Human / AI-assisted explicit mutation
  -> Persistent Watchlist Domain Service
  -> Identity validation or migration guard
  -> optimistic expected-version check
  -> SQLite transaction
  -> current projection + immutable revision
  -> read projection
  -> current Taiwan Market Identity Service resolution
  -> future M8R-10 Workbench / bounded Unified Request
```

## Bounded implementation tranche

One M8R-09 implementation tranche should deliver:

1. Formal schemas and reason-code contract.
2. Installation-local SQLite storage and injected-root test isolation.
3. Current projection plus immutable revisions, atomic transactions, and
   optimistic concurrency.
4. Typed mutation preview/commit with confirmation binding and no generic
   upsert.
5. ISIN-bound identity resolution, unsupported-known separation, successor
   review, and cache projection.
6. Legacy M5K/M5N import preview and explicit migration commit.
7. Tombstone deletion, rollback-as-new-revision, canonical JSON export, and
   fail-closed corruption/schema migration behavior.
8. Minimal local FastAPI read and mutation-command endpoints.
9. Unit, schema, transaction, concurrency, rollback, identity integration,
   migration, API, clean-install, and independent-install tests.

M8R-10 owns full watchlist/evidence Workbench integration, user-facing mutation
UX, and any future MCP exposure. Monitoring remains Phase H.

## Acceptance matrix

Implementation acceptance must cover:

- Basic: empty/list creation, default selection, rename, TWSE stock, TPEx
  stock, ETF, unsupported-known cash instrument, remove, enable/disable,
  reorder, tags, and exact notes preservation.
- Versioning: deterministic increments, immutable history, rollback creates a
  new revision, optimistic conflict, current/revision atomicity, and failed
  transaction leaves both unchanged.
- Identity: code/name resolves to ISIN before persistence, ambiguous/not-found/
  `NOT_INITIALIZED` do not persist, same-ISIN cache refresh is not migration,
  successor requires review, and snapshot absence does not auto-delete.
- Import: legacy conversion, partial resolution, ambiguity, deferred
  derivatives, unsupported-known, duplicate ISIN, preview binding, and explicit
  confirmation.
- Storage: `NO_WATCHLISTS`, schema migration, corruption/hash/chain fail-closed,
  parameterized SQL, path containment, resource limits, canonical export, and
  no raw prompt/secrets.
- Isolation: Git ignored, clean install, two installation roots independent,
  no market network, and no Security Master mutation.
- API: read without mutation, exact version reads, preview without mutation,
  confirmation mismatch refusal, and no mutation-triggered evidence execution.

No unresolved owner decision remains for this tranche. Product expansion to
derivative durable identity, cloud/multi-user tenancy, MCP mutation, and
retention compaction is explicitly deferred rather than left ambiguous.

## Principal decision

`READY_FOR_M8R_09_PERSISTENT_WATCHLIST_IMPLEMENTATION`
