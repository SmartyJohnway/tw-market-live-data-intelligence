# Phase L L2-A6-R1 — Migration Source Lineage Clarification

**Date:** 2026-10-15
**Disposition:** `L2_A6_R1_MIGRATION_SOURCE_LINEAGE_CLARIFICATION_FROZEN_FOR_A6_CANDIDATE`
**A6 base:** `origin/main@ef95878d0c1ae7b800df595c8a9f44fdc5090c58`
**Owner final acceptance:** not recorded

## 1. Corrected A6 entry authority

The original A6 request required both an A5 restore receipt and an A5 result of
`MIGRATION_REQUIRED`. Those conditions cannot coexist under the accepted A5
contract: A5 only materializes a destination and receipt for
`DIRECT_RESTORE_COMPATIBLE`; `MIGRATION_REQUIRED` is classification-only and
stops before any restore write. This clarification corrects the A6 source
lineage and leaves A5 implementation and semantics unchanged.

The migration source is now `VERIFIED_A4_BACKUP_REQUIRING_MIGRATION`, established
on every lifecycle operation by all of the following:

1. A4 `verify_backup()` succeeds and yields the manifest SHA-256.
2. The explicit `CompatibilityAttestation.backup_manifest_sha256` equals that
   verified manifest SHA-256.
3. A5 `inspect_restore()` is called with the same explicit target compatibility
   contract and independently derives `MIGRATION_REQUIRED`.
4. The derived migration identifiers are present in the bounded A6 registry.

No stored status string, previous inspection, or A5 restore receipt substitutes
for those checks. A5 restore remains read-only on this path and creates no
restore target.

## 2. Source identity and scope

Canonical source identity binds `backup_id`, verified A4 manifest SHA-256,
`source_state_identity`, A4 `selection_scope`, `backup_tier`, the A5 family
version facts, target contract version/hash, and migration path identifiers.
The scope remains `EXPLICIT_DECLARED_MEMBERS_ONLY`; A6 does not claim whole
installation completeness. A deterministic hash of the canonicalized
compatibility attestation may bind the exact facts used, but establishes only
content consistency and not external provenance authenticity.

## 3. Checkpoint and rollback authority

The verified immutable A4 source package is the mandatory checkpoint:
`checkpoint_kind=SOURCE_A4_BACKUP`, bound to its own backup ID and manifest hash.
It suffices only for the declared members actually present in that package.
If required affected or rollback members are absent, A6 fails with
`MIGRATION_CHECKPOINT_INCOMPLETE`; it does not fetch, rebuild, or reconstruct
them. The source package is never modified.

Copy-on-write creates a separately named `MIGRATION_WORKING_COPY` staging tree
from exact A4 member bytes. A migrated candidate is isolated and is not an A5
restore, active installation, or activation authority. Rollback uses the
verified retained A4 source bytes, never an inverse transform. A rollback
candidate, if produced, is a new isolated tree with its own receipt.

## 4. Migration registry and current authority gap

The production registry contains `watchlist-schema-v0-to-v1` as
`KNOWN_NOT_IMPLEMENTED`. Current repository authority provides no Watchlist v0
schema, historical fixture/database contract, or deterministic v0-to-v1
transform. A5's classification identifier alone does not authorize an SQL
transformation. Production apply therefore returns
`MIGRATION_PATH_NOT_IMPLEMENTED` before creating a working copy or writing a
target. Test-only synthetic transformers, when used to exercise generic
lifecycle behavior, are injected only by focused tests and are absent from the
production registry and compatibility contract.

## 5. A5 compatibility boundary

A5's `MIGRATION_REQUIRED` stop behavior is preserved: it does not materialize a
restore target, write a restore receipt, or perform migration. A6's separate
working-copy lifecycle begins from the independently verified A4 package and
A5 classification. No A5 code or contract is amended by this R1.

## 6. Scope and disposition

This clarification authorizes A6 implementation under the corrected source
lineage. It does not authorize fabricated migrations, activation, in-place
mutation, source acquisition, public API/MCP changes, or A7. Technical
acceptance and Owner final acceptance remain separate; Owner acceptance is not
recorded here.
