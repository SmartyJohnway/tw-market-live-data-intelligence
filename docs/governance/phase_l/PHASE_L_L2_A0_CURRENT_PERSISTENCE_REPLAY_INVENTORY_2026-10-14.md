# Phase L L2-A0 — Current Persistence / Replay Inventory

**Date:** 2026-10-14
**Base:** `main@4508fd6ee1d82e528b40a9adbda1a01a6d4bafe7`
**Disposition:** `L2_A0_CURRENT_PERSISTENCE_REPLAY_INVENTORY_COMPLETE`
**Owner entry authorization:** L2 explicitly started on 2026-10-14.
**Authority:** frozen L0; L1 closed under `PHASE_L_L1_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`; current Git main.

## 1. Purpose and boundary

L2-A0 inventories the persistence, replay, retention, hash, backup/restore, compatibility,
and migration substrate already present in the product and historical repository layers.
It does not implement migration, restore, retention cleanup, or a new public API.

No production Security Master or Watchlist state is initialized or mutated. No authorization
is created or consumed. No market/source acquisition is performed.

Frozen L0 requires L2 to keep replay of old evidence distinct from re-fetch of current evidence,
and to cover retention, backup/restore, hash verification, schema compatibility, migration,
and rollback without silent incompatible migration.
## 2. Current product substrate

| Area | Current substrate | L2 classification |
|---|---|---|
| Finalized control package | Request/plan/authorization/binding/preflight manifest plus claim/receipt/bundle/evidence | REUSE |
| Integrity | Control artifact SHA-256; receipt/bundle/evidence verification; Audit integrity flags and hash | REUSE |
| Audit replay manifest | Request/plan/auth/binding/claim/receipt/bundle identities and hashes | REUSE / EXTEND |
| Result/Audit projection | Deterministic local reconstruction through Mode C from finalized predecessors | REUSE / SPLIT SEMANTICS |
| Read Result / AI handoff | Zero market network, but may materialize missing F3/Result/Audit/Markdown | REUSE WITH L2 CORRECTION |
| Request/Result compatibility | Request v1-v3; Result/Audit v1-v3; preferred v3 | REUSE / FORMALIZE |
| Security Master | Qualified immutable releases, manifest/content/schema hash verification, history and rollback | REUSE SUBSYSTEM |
| Persistent Watchlist | SQLite integrity, hash-chained revisions, export, rollback-as-new-revision, legacy import | REUSE SUBSYSTEM |
| Whole-product backup/restore | No canonical product manifest or restore orchestrator found | ADD |
| Product state compatibility | No one installation-state compatibility matrix / version authority found | ADD |
| Product migration engine | No cross-state inspect/preview/backup/apply/verify engine found | ADD |
| Product retention authority | No Phase L product retention policy; historical Phase C has local metadata only | ADD |

The physical default roots remain checkout-coupled. L2 must define logical state and backup
contracts without prematurely choosing final Windows install/data paths; final physical mapping
and P1-P6 packaging acceptance remain L6 obligations.
## 3. Replay terminology collision found

The repository currently uses `replay` for several different concepts. L2 must not treat them
as one operation:

1. **authorization replay** — a second execution attempt using consumed one-shot authority;
   this remains forbidden and is blocked before transport;
2. **fixture/historical replay** — M4 and acceptance-era deterministic fixtures used for tests;
   these are not production governed evidence;
3. **evidence replay** — deterministic reconstruction or verification of a finalized governed
   package using retained local predecessors, without market/source acquisition.

The third meaning is the L2 product concern. It must never reuse consumed authorization and must
never fall back to current-source acquisition.

## 4. Mode C semantic gap

Current `market_read_result` / Mode C is network-free and verifies finalized lineage, but its
implementation is not strictly read-only. If F3 or Result/Audit/Markdown derived outputs are
missing, Mode C can reconstruct and materialize them into the control package.

That behavior is deterministic local reconstruction, not source refetch. However, L2 needs an
explicit semantic boundary so a read operation cannot silently become a local persistence
operation. The A1 replay contract therefore separates `READ_EXISTING`, evidence replay, and
current-source refetch.
## 5. Retention and migration findings

The existing Phase C activation metadata contains a 30-day default retention value and manual
pin/delete flags. This is not promoted to Phase L product authority: L0 explicitly deferred
retention durations until later evidence. L2 must decide retention by state class and evidence
requirements rather than inherit an acceptance-era constant silently.

Security Master already has a qualified-release history, manifest/content/schema verification,
and explicit rollback. Persistent Watchlists already have SQLite integrity checks, hash-chained
revisions, export, rollback-as-new-revision, and bounded legacy import. These are valuable
subsystem authorities, not a whole-product migration framework.

Historical M4 fixture replay, M5 backup/rollback helpers, and the M8R-03E v1-to-v2 evidence-only
migration remain reference patterns or historical mechanisms. They are not automatically
promoted to product replay, backup, or migration authority.

## 6. Bounded verification

Current substrate gate, excluding tests explicitly marked `historical`:

`47 passed, 4 deselected, 393 warnings`.

The warnings are the existing `jsonschema.RefResolver` deprecation warnings in the persistent
Watchlist implementation.

A broader run including historical nodes produced `2 failed, 49 passed`; both failures were
historical Mode C tests hard-coded to v1 output paths while the current preferred default is v3.
They failed before semantic tamper verification because the v1 files were not materialized.
This is recorded as historical-test expectation drift and is not repaired in A0.

## 7. Stop boundary

A0 is inventory only. No runtime implementation begins here. The next architectural step is the
L2-A1 replay-semantics contract; only after that boundary is fixed should Codex receive the first
bounded implementation tranche.
