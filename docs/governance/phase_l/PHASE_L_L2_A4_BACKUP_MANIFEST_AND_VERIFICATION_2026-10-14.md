# Phase L L2-A4 — Backup Manifest & Verification

**Date:** 2026-10-14
**Base:** `main@b36a11c26590c6b00745cbb66e17ec55c81cbbf0`
**Technical disposition:** `L2_A4_BACKUP_MANIFEST_AND_VERIFICATION_ACCEPTANCE_REVIEW_PASS`
**Owner acceptance:** `L2_A4_BACKUP_MANIFEST_AND_VERIFICATION_OWNER_ACCEPTED_FOR_MERGE`
**Authority:** frozen L0; L2-A0; frozen L2-A1 and A1-R1; accepted A2; Owner-accepted A3 in PR #345 and merge-closure PR #346; current A4 candidate.

## 1. Scope and implementation

`server/services/unified_backup.py` adds internal `plan_backup`, `create_backup`, and read-only `verify_backup`. There is no public HTTP/MCP route. The caller must provide explicit source roots, explicit artifact members, a source-state identity, a bounded maximum byte count, and an authority-binding ID plus verification attestation for each member. The implementation never scans a root or infers artifact family from a path/name.

The planner reuses `classify_artifact` / `classify_artifact_family` from A3. Unknown/unbound families fail closed; `NONE`/ephemeral families are omitted with a bounded disposition only when the caller proves no governed reference; `DERIVED` is omitted by default; `CORE` includes only A3 `CORE`; `FULL_GOVERNED` includes A3 `CORE` and `FULL_GOVERNED`. Derived members are optional by explicit `include_derived=True` and do not affect either correctness tier. A3's unestablished user-settings authority is recorded as `NO_CURRENT_CANONICAL_AUTHORITY`, not treated as a source.

## 2. Backup tiers and selection

- **CORE:** caller-declared A3 `CORE` members: active Security Master release pointer, qualified release/history material, and Persistent Watchlists/revisions/tombstones. User settings are omitted because A3 established no current canonical settings store.
- **FULL_GOVERNED:** CORE plus caller-declared A3 `FULL_GOVERNED` members, including finalized control/evidence packages and their Request/plan, authorization/consumption binding, claim, receipt, bundle, F3, operation/source evidence, selection provenance, Result, and Audit bytes.
- **DERIVED:** omitted unless explicitly requested; A3 `NONE`, `UNDETERMINED`, and unknown families cannot become candidates.

Completeness is bounded to the explicit declared member set. The manifest records both `member_count` and `declared_member_count`, and every omission has a reason. A4 does not enumerate or claim a whole installation root was backed up. The trusted internal caller remains responsible for establishing complete member selection and the binding attestation from the applicable Security Master or governed package authority; the generic planner verifies the member bytes against its supplied SHA-256 but does not invent or discover that authority.

## 3. Manifest and integrity

Manifest: `backup-manifest.json`; schema: `tw_market_backup_manifest.v1`; format: `tw_market_backup.v1`. Package fields are:

`manifest_schema_version`, `backup_format_version`, `backup_id`, `backup_tier`, `created_at`, `product_identity`, `source_state_identity`, `selection_scope`, `authority_binding_model`, `member_count`, `declared_member_count`, `total_size_bytes`, `max_total_bytes`, `members`, `omitted_members`, `manifest_integrity`.

A4 fixes `selection_scope=EXPLICIT_DECLARED_MEMBERS_ONLY` and `authority_binding_model=TRUSTED_INTERNAL_CALLER_ATTESTED`. The verifier requires both exact values even when a manifest self-hash has been recomputed. This makes the caller/completeness boundary machine-readable: `BACKUP_VERIFIED` cannot be re-labeled as whole-installation completeness or self-proven authority.

Each included member records:

`logical_member_id`, `artifact_family`, `state_class`, A3 `backup_tier`, `source_authority_id`, `source_relative_path`, `backup_relative_path`, `source_kind`, `size_bytes`, `sha256`, `integrity_binding`, `replay_required`, and `audit_required`.

Member SHA-256 covers the exact bytes stored at the backup path. Manifest SHA-256 covers canonical UTF-8 JSON (sorted keys, compact separators, no NaN) with the entire `manifest_integrity` property excluded, avoiding self-hash recursion. Member order is sorted by backup-relative path and logical ID. Clock and backup ID are injected by the caller, enabling deterministic tests. No machine-specific absolute source path is stored in the manifest.

## 4. Path containment and finalization

Source and destination roots must be explicit, existing, non-overlapping directories. Source roots, path components, members, and verified package entries reject symlinks and Windows reparse points. Relative paths reject absolute POSIX paths, drive-qualified paths, backslashes, empty/dot/parent components, NTFS alternate-stream colons, trailing dot/space, reserved Windows device names, and case-fold collisions. Duplicate logical IDs and duplicate/case-colliding backup paths fail closed.

Creation writes only to a new caller-selected destination. It creates a sibling `.staging-<backup_id>` directory, writes members and manifest there, verifies that staged package, then renames it to the absent destination on the same parent/filesystem. Existing final/staging paths fail with `BACKUP_DESTINATION_EXISTS`; no overwrite mode exists. If creation fails, the hidden staging directory remains visibly non-final and is rejected by public `verify_backup`. It contains only bytes created by this attempt. No source is moved, renamed, touched intentionally, rewritten, or deleted.

## 5. Source consistency and state-family handling

- **Ordinary files:** plan captures source identity and requires the caller-supplied expected SHA-256 to match it. Creation opens and reads one byte stream, checks descriptor/path identity before and after, verifies those same captured bytes against the expected authority hash, writes those exact bytes, then hashes the destination bytes and size. A detected change fails as `SOURCE_CHANGED_DURING_BACKUP`.
- **Watchlists:** raw copying of a live SQLite file is not used. A read-only source connection uses SQLite's Online Backup API to make a coherent in-memory planning snapshot and a destination snapshot. The existing Watchlist `verify_integrity()` contract is reused with read-only connections for the source and snapshot; source `PRAGMA data_version` is checked across each snapshot. A deterministic logical fingerprint binds the plan to the same Watchlist content at creation; output `size_bytes`/SHA-256 bind the exact destination SQLite bytes. Planning records the snapshot size, not the raw `.sqlite3` source-file size, so WAL/uncheckpointed layout differences are not misclassified as state mutation. No store constructor/init, schema migration, or source write is invoked. SQLite documents that the Online Backup API produces a consistent snapshot while allowing concurrent database users; commits detected during a snapshot fail closed.
- **Security Master:** only caller-declared existing state is copied. No refresh, activate, rollback, or rewrite occurs. The caller must use the current release/pointer hash authority to supply the binding and complete set of retained files; no release discovery or policy expansion occurs in this generic layer.
- **Finalized evidence:** bytes are copied as retained. The module does not invoke A2 replay, Mode C materialization, F3 reconstruction, current Security Master lookup, authorization, or source adapters. F3, Result and Audit are not regenerated.
- **Sensitive integration state:** DPAPI/Secure Tunnel credentials, environment dumps, and other unclassified/private integration data cannot pass A3's bounded family policy and are outside the backup boundary.

The Watchlist snapshot uses SQLite's documented Online Backup API, whose successful completion produces a consistent database snapshot; it is not a raw file copy. [SQLite Online Backup API](https://www.sqlite.org/backup.html).

## 6. Verification semantics and failure outcomes

`verify_backup(path, max_total_bytes=...)` is read-only and requires an explicit positive caller byte limit. It verifies supported manifest/format versions, manifest integrity, schema and field bounds, member counts/order, duplicate identities, path normalization/containment/reparse safety, A3 family/tier consistency, member existence, exact file inventory (missing and extra files/directories), size, aggregate size against both the manifest and caller limit, and SHA-256. It does not connect to source roots or modify/repair the backup.

Bounded failure codes include:

`BACKUP_VERIFIED`, `BACKUP_MANIFEST_INVALID`, `BACKUP_UNSUPPORTED_VERSION`, `BACKUP_MEMBER_MISSING`, `BACKUP_MEMBER_UNEXPECTED`, `BACKUP_MEMBER_HASH_MISMATCH`, `BACKUP_MEMBER_SIZE_MISMATCH`, `BACKUP_PATH_UNSAFE`, `BACKUP_CLASSIFICATION_MISMATCH`, `UNCLASSIFIED_SOURCE_STATE`, `SOURCE_CHANGED_DURING_BACKUP`, `BACKUP_DESTINATION_EXISTS`, `BACKUP_RESOURCE_LIMIT_EXCEEDED`, `OUTSIDE_BACKUP_BOUNDARY`, and `BACKUP_DESTINATION_FAILED`.

`BACKUP_VERIFIED` means only that this package is internally complete and hash-valid under A4. It does not mean `RESTORE_ALLOWED`, migration is unnecessary, or the current application is compatible. No `MIGRATION_REQUIRED` or `UNSUPPORTED_NEWER_STATE` installation classification is emitted.

## 7. Tests and containment

Codex focused gate was **81 passed, 393 warnings**. Independent reviewer inspection found and repaired four bounded contract issues before acceptance: (1) a rehashed `FULL_GOVERNED` manifest could previously launder a required governed family such as historical F3 into an invalid omission disposition; verifier omission semantics now re-derive the allowed disposition from A3 family tier plus package tier; (2) Watchlist planning now records Online Backup snapshot size instead of raw source-file size; (3) manifest completeness/authority limitations are now machine-readable through fixed `selection_scope` and `authority_binding_model` fields; and (4) planner/verifier byte-limit gates now reject known oversize inputs before full hashing/snapshot I/O where size metadata already proves the bound would be exceeded. New mutation/contract tests cover all four repairs. Independent reviewer focused gate after repairs: **86 passed, 393 warnings**.

Focused A4 tests cover CORE/FULL selection and explicit omissions, unknown/unverified classification, exact byte copy, manifest fields and deterministic order, injected timestamp/ID, source change after planning, size/hash checks, rehashed semantic tampering, missing/extra members, existing destination, traversal/absolute/drive paths, duplicate IDs/case-fold collisions, symlink escape (when available), Watchlist Online Backup with before/after source file hashes, and verifier read-only/network sentinels. Existing A2/A3, exact-six MCP, and Watchlist deterministic tests are run alongside the A4 suite. No live acceptance or source acquisition is run.

Public HTTP/MCP surfaces, exact-six MCP tools, schemas, Catalog/Route/Executor, authorization, A2 semantics, and A3 policy files are not modified. A4 candidate does not implement restore, migration, cleanup, pruning, or deletion.

## 8. Limitations and stop boundary

- `plan_backup` is intentionally not a machine/root scanner. Exact whole-state completeness requires a future trusted caller/source-specific selection authority.
- Generic file-family authority is explicitly attested by the internal caller and byte-checked against its supplied expected SHA-256. Source-specific readers remain responsible for obtaining that expected digest from Security Master manifests or finalized control/evidence manifests. A4's manifest self-hash proves package self-consistency, not external provenance authenticity; no signature or independent trust anchor is introduced in this tranche.
- Physical state-root mapping remains deferred under L0/L6. A4 accepts roots and destination from the caller and does not name a canonical installation path.
- Watchlist backup is a DB snapshot, including its current database contents; expired preview rows are not separately filtered or rewritten.
- Restore, migration, compatibility inspection, retention-duration policy, backup rotation, and deletion remain deferred to separately authorized tranches. A valid hash proves byte integrity, not restore compatibility.

Technical disposition: `L2_A4_BACKUP_MANIFEST_AND_VERIFICATION_ACCEPTANCE_REVIEW_PASS`. Owner acceptance is recorded under `L2_A4_BACKUP_MANIFEST_AND_VERIFICATION_OWNER_ACCEPTED_FOR_MERGE`. Commit, push, PR, and merge may proceed for this exact A4 tranche only. Restore, migration, deletion, cleanup, or A5 implementation are not authorized by this closure.
