# Phase L L2-A6 — Migration and Rollback Lifecycle

**Date:** 2026-10-15
**Base:** `origin/main@ef95878d0c1ae7b800df595c8a9f44fdc5090c58`
**R1:** `L2_A6_R1_MIGRATION_SOURCE_LINEAGE_CLARIFICATION_FROZEN_FOR_A6_CANDIDATE`
**Technical disposition:** `L2_A6_MIGRATION_AND_ROLLBACK_LIFECYCLE_ACCEPTANCE_REVIEW_PASS`
**Owner acceptance:** `L2_A6_MIGRATION_AND_ROLLBACK_LIFECYCLE_OWNER_ACCEPTED_FOR_MERGE`

## 1. Authority and scope

A6 reuses frozen L0 and L2-A0/A1/A1-R1, accepted A2/A3, and Owner-accepted
A4/A5. R1 corrects the impossible A5-receipt-plus-`MIGRATION_REQUIRED`
precondition. No A5 implementation or behavior is changed. A6 is internal only;
it changes no public HTTP/MCP surface, schemas, Catalog/Route/Executor, or
authorization semantics.

## 2. Source and compatibility authority

The only migration source authority is
`VERIFIED_A4_BACKUP_REQUIRING_MIGRATION`. For each inspection, preview, apply,
verification, and rollback, A6 re-runs A4 `verify_backup()`, binds the
`CompatibilityAttestation.backup_manifest_sha256` to the verified A4 manifest
SHA-256, and calls A5 `inspect_restore()` with the same explicit target
compatibility contract. A5 must independently derive `MIGRATION_REQUIRED` and
the contract's migration IDs must match the A6 bounded registry. An A5 restore
receipt is neither required nor accepted as the lineage root for this path.

Source identity binds A4 backup ID, verified manifest hash, state identity,
`selection_scope`, backup tier, A5 family versions, target contract version/hash,
and migration IDs. The scope remains
`EXPLICIT_DECLARED_MEMBERS_ONLY`; no whole-installation completeness claim is
made. A compatibility-attestation SHA-256, when recorded, proves only content
consistency and not external provenance authenticity.

## 3. Registry and migration path status

The production registry is bounded and static. It contains
`watchlist-schema-v0-to-v1` as `KNOWN_NOT_IMPLEMENTED`. The repository has no
authoritative Watchlist v0 schema, historical fixture/database contract, or
deterministic transformation. The A5 classification ID alone is insufficient
authority for a transformer. Production apply therefore returns
`MIGRATION_PATH_NOT_IMPLEMENTED` before creating staging or writing a target.
No production migration transformer is implemented.

The generic apply/verify/rollback engine is exercised with an explicitly
test-only synthetic transformer injected from the focused test module. It is
not in the production registry, does not describe a Watchlist or Security
Master migration, and is not part of an A5 compatibility contract.

## 4. Preview and immutable plan

`inspect_migration()` is read-only and returns `MIGRATION_NOT_REQUIRED` for a
directly compatible source; unsupported/newer/unknown A5 outcomes fail closed.
`preview_migration()` is deterministic, revalidates A4/A5, and returns a frozen
`MigrationPlan` (`tw_market_migration_plan.v1`) with canonical SHA-256 integrity.
Apply rechecks the plan hash and independently derives migration ID, versions,
member sets, A4/A5 hashes, target contract, registry, and checkpoint binding.
Independent exact-head review additionally requires a valid bounded plan ID,
UTC `created_at`, the exact three-key resource-limit envelope, and exact
`compatibility_contract_version` re-derivation from A5. Rehashing a plan cannot
authorize another migration, change its target contract/version, or launder
malformed operation metadata.

Plan fields include plan ID/schema, migration ID, source backup ID/manifest
hash/state identity/selection scope, compatibility contract version/hash,
attestation content hash, source/target family versions, affected and unchanged
logical members, checkpoint kind/ID/hash, registry hash, resource limits,
creation time, and plan integrity. Machine-specific source paths are not
serialized into the plan.

## 5. Checkpoint and apply

The immutable verified source A4 package is the mandatory checkpoint:
`checkpoint_kind=SOURCE_A4_BACKUP`. The plan binds its backup ID and manifest
hash. A4 exact declared members are the full scope available to A6. Each
executable registry entry must declare required logical member IDs; if those
members are absent, A6 returns `MIGRATION_CHECKPOINT_INCOMPLETE`. A6 does not
infer omitted installation state or create a redundant second backup.

An implemented transformer would copy exact A4 member bytes to a new sibling
staging tree, change only registry-authorized affected members, independently
verify all changed and unchanged bytes, write a migration receipt, reverify,
check the A4 source inventory, and atomically rename staging to a new isolated
candidate. Existing destinations, unsafe Windows paths, reparse points,
repository/source overlap, and caller-supplied forbidden/live roots fail
closed. A failed operation may leave a non-final staging tree. No source,
checkpoint, active installation, or service pointer is changed.

The present production registry has no executable transformer, so this apply
path stops before any staging write with `MIGRATION_PATH_NOT_IMPLEMENTED`.
Test-only synthetic lifecycle verification exercises successful generic
copy-on-write without enabling a production migration.

## 6. Receipts and verification

`migration-receipt.json` uses `tw_market_migration_receipt.v1`. It records the
run and plan IDs/hash, migration ID, A4 source and checkpoint IDs/hashes,
explicit selection scope, compatibility contract/attestation hashes,
source/target versions, source/target inventory hashes, affected/unchanged
members, bounded outcome, member byte hashes/sizes, and UTC creation time. Its
canonical SHA-256 excludes the integrity field and establishes self-consistency
only.

`verify_migrated_state()` is read-only. It re-verifies A4 and A5, validates the
plan and registry, recomputes deterministic transformer output, checks receipt
integrity and exact file inventory, verifies changed/unchanged members and
Watchlist SQLite integrity when present, and enforces resource and path bounds.
The receipt's claimed outcome is not accepted without independent derivation.

## 7. Rollback

Rollback does not invert a transform. `rollback_migration()` first verifies the
migrated candidate, re-verifies A4/A5 and the plan, then copies exact retained
A4 bytes to a new isolated rollback candidate. It writes
`rollback-receipt.json` (`tw_market_rollback_receipt.v1`) bound to the migration
receipt and source checkpoint. `verify_rollback()` is read-only and rechecks
source bytes, receipt hashes, member inventory, explicit scope, and forbidden
roots. Source package and migrated candidate inventories are compared before
and after rollback. Independent exact-head review also re-derives
`checkpoint_kind=SOURCE_A4_BACKUP` and enforces integer (non-boolean)
restored-member/byte counts, so a recomputed receipt self-hash cannot relabel
rollback authority. A rollback candidate is not an A5 restore, activation, or
active installation.

## 8. Resource, network, and public boundaries

Operations require explicit total-byte, member-count, and changed-member
bounds. A4 declared sizes/counts are checked before migration member reads.
Destination parents must exist, outputs must be new isolated local paths, and
caller-provided forbidden roots are mandatory. No socket/source adapter,
Security Master refresh, or external network operation is used. The A4 package
is the only source/checkpoint. No active installation operation or public
interface is added; MCP remains exactly six tools.

## 9. Tests and limitations

Codex's original focused gate passed **127 tests, 393 warnings**. Independent
exact-head review added two bounded mutation tests and repairs: rehashed plan
operation metadata (`compatibility_contract_version`, UTC creation time, and
plan ID) must satisfy independently derived/envelope constraints, and a
rollback receipt cannot relabel `SOURCE_A4_BACKUP` by recomputing its self-hash.
The reviewer focused gate passed **129 tests, 393 warnings**; the warnings remain
the existing Watchlist `jsonschema.RefResolver` deprecation. The gate covers A6
source and plan binding, A5 direct/migration behavior, unknown/unsupported
outcomes, test-only copy-on-write apply/verify/rollback, receipt rehash
resistance, path containment, exact source/checkpoint immutability, offline
sentinels, and A5/A4/A3/A2/MCP/Watchlist regressions.

Known limitation: no authoritative production migration exists. Watchlist
v0-to-v1 stays `KNOWN_NOT_IMPLEMENTED`; therefore successful production apply,
migrated candidate, and production rollback candidate cannot currently be
produced. A6 does not authorize migration, activation, restore, deletion,
network access, or A7. A7 remains not authorized.

## 10. Stop boundary

Independent exact-head review is complete. Technical disposition is
`L2_A6_MIGRATION_AND_ROLLBACK_LIFECYCLE_ACCEPTANCE_REVIEW_PASS`. Owner acceptance
is recorded under `L2_A6_MIGRATION_AND_ROLLBACK_LIFECYCLE_OWNER_ACCEPTED_FOR_MERGE`.
PR #351 may be merged for this exact reviewed head once checks remain green; no
A7 work is authorized here.
