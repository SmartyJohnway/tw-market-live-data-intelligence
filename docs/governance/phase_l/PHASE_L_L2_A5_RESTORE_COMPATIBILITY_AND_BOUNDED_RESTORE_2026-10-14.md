# Phase L L2-A5 — Restore Compatibility & Bounded Restore

**Date:** 2026-10-14
**Base:** `origin/main@7ec872d7a72a22993917e4413d4c640a35f53e4e`
**Predecessor:** L2-A4 implementation PR #347 (`fb2fef0c50c3ee50581bc62af534b36116b332e7`) and governance closure PR #348; A4 is Owner-accepted and merged.
**Technical disposition:** `L2_A5_RESTORE_COMPATIBILITY_AND_BOUNDED_RESTORE_ACCEPTANCE_REVIEW_PASS`
**Owner acceptance:** `L2_A5_RESTORE_COMPATIBILITY_AND_BOUNDED_RESTORE_OWNER_ACCEPTED_FOR_MERGE`.
**Merged:** PR #349 / `97386f756f2dcc6dbf4d3ee7934a41066fa1b0c2`.

## 1. Authority and boundary

This tranche uses frozen L0, completed L2-A0, frozen A1/A1-R1, accepted A2/A3, and Owner-accepted A4 as binding input. A5 is internal only. It reuses `server.services.unified_backup.verify_backup`; it does not change A4 manifest semantics, A2 replay semantics, A3 classification, public APIs, schemas, authorization behavior, or the exact-six MCP surface.

`BACKUP_VERIFIED` means the explicitly declared A4 member set is internally complete and hash-valid. A5 preserves `selection_scope=EXPLICIT_DECLARED_MEMBERS_ONLY` into the restore receipt. Neither inspection nor restore asserts whole-installation completeness.

## 2. Versioned compatibility contract

`tw_market_restore_contract.v1` identifies the target contract. It declares supported product identity, A4 backup formats, A4 manifest schemas, and explicit supported versions by canonical state family. The internal API accepts a `CompatibilityAttestation` with `backup_manifest_sha256` and `state_family_versions` keyed by logical member ID. The binding must equal the SHA reported by A4 verification. Governed evidence members are copied as opaque retained bytes; Result/Audit/F3 schema versions are never used to infer installation-state version.

Current direct family-version support is version `1` for Security Master active pointer state, Security Master release/history state, and Persistent Watchlist state. Watchlist version is checked against the retained SQLite `schema_migrations` table. Security Master family version is supplied by the trusted source-specific internal caller; A5 does not parse arbitrary filenames or claim A4 self-hash proves caller attestation authenticity. Missing, extraneous, mismatched, or unknown version facts produce `RESTORE_COMPATIBILITY_UNKNOWN`.

The explicit Watchlist source version `0` rule reports `MIGRATION_REQUIRED` with classification identifier `watchlist-schema-v0-to-v1`. It is informational only; no conversion implementation is invoked. A numeric version greater than the highest explicitly supported version reports `UNSUPPORTED_NEWER_STATE`. No date, branch, Result version, or best-effort trial determines compatibility.

## 3. Outcome vocabulary

Inspection and restore use these bounded outcomes. Inspection also returns declared source family versions, supported target family versions, and migration identifiers where a contract rule supplies one:

| Outcome | Meaning |
|---|---|
| `DIRECT_RESTORE_COMPATIBLE` | All declared canonical family versions are explicitly supported; byte copy needs no rewrite. |
| `MIGRATION_REQUIRED` | An explicit contract rule identifies a state version requiring later transformation; restore does not start. |
| `UNSUPPORTED_NEWER_STATE` | A declared numeric family version exceeds the supported maximum; restore does not start. |
| `UNSUPPORTED_BACKUP_FORMAT` | A4 backup/manifest version is not supported by the target contract. |
| `PRODUCT_IDENTITY_MISMATCH` | Backup product identity differs from the A5 product identity. |
| `RESTORE_COMPATIBILITY_UNKNOWN` | Required compatibility facts are absent, unbound, inconsistent, or unsupported. |
| `RESTORE_SCOPE_INCOMPLETE_FOR_REQUEST` | Declared member scope does not match the A4 explicit-member contract. |
| `RESTORE_TARGET_NOT_EMPTY` | Destination or staging target already exists. |
| `RESTORE_TARGET_UNSAFE` | Destination/member path is unsafe, escapes containment, or overlaps a protected root. |
| `RESTORE_RESOURCE_LIMIT_EXCEEDED` | Explicit byte/member bounds would be exceeded. |
| `RESTORE_SOURCE_INVALID` | A4 package is invalid or unsupported by its own verifier. |
| `RESTORE_MEMBER_INTEGRITY_FAILED` | A member is missing, changed, or does not match A4 size/hash. |
| `RESTORE_VERIFICATION_FAILED` | Receipt or restored tree fails independent verification. |
| `RESTORE_COMPLETED` | Exact bytes were restored and verified in a new isolated tree. |
| `RESTORED_STATE_VERIFIED` | Read-only restored-tree verification passed; this is not activation. |

Only `DIRECT_RESTORE_COMPATIBLE` proceeds to restore execution. `MIGRATION_REQUIRED`, `UNSUPPORTED_NEWER_STATE`, and unknown compatibility return without creating destination/staging state.

## 4. Bounded restore and containment

`restore_backup`, `inspect_restore`, and `verify_restored_state` are internal functions. All require explicit byte and member bounds. Restore also requires an explicit `forbidden_roots` argument (an empty list only when the trusted caller has no known live roots). It preflights A4 declared size/member count before member hashing/copying, verifies A4, checks the compatibility attestation, and accepts only a new destination whose parent already exists. It rejects `..`, existing targets, reparse/symlink components, UNC/device-root destinations before filesystem probing, and paths overlapping the backup, repository, or caller-provided forbidden/live roots. The trusted caller must provide every known active/durable source root; canonical physical installation roots remain deferred under L0/L6.

Restore stages in a sibling `.<name>.staging-<restore_id>` directory, copies each verified member's exact bytes, writes a receipt, independently verifies staging, checks the A4 package inventory and SHA-256 values remain unchanged, then renames staging to the absent final path. A failed attempt can leave a non-final staging directory. It never overwrites, merges, activates, registers, or points the product at restored state. It never changes the backup package or active installation.

Relative member validation reuses A4's strict path rules and is repeated against the restore root: POSIX/Windows absolute paths, drive/UNC forms, `..`, ADS colons, reserved Windows device names, trailing dot/space, case-fold collisions, file/directory prefix collisions, and symlink/reparse traversal fail closed. No source/network lookup occurs.

## 5. Receipt and verification

`restore-receipt.json` uses schema `tw_market_restore_receipt.v1`. Fields are:

`restore_receipt_schema_version`, `restore_id`, `backup_id`, `backup_manifest_sha256`, `backup_format_version`, `source_state_identity`, `restore_scope`, `compatibility_outcome`, `target_contract_version`, `target_contract_sha256`, `state_family_versions`, `restored_member_count`, `restored_total_bytes`, `members`, `created_at`, and `receipt_integrity`.

Each member records logical ID, A3 artifact family, backup-relative path, restore-relative path, byte size, and SHA-256. Receipt SHA-256 covers canonical UTF-8 JSON excluding the entire `receipt_integrity` field. It proves receipt self-consistency only, not signer identity or external provenance authenticity.

`verify_restored_state` is read-only. It re-verifies A4, recomputes compatibility from the supplied target contract plus manifest-bound caller attestation, checks receipt bindings/scope/integrity, exact expected files and directories, no extra members, sizes/hashes/aggregate bounds, path containment, and Watchlist SQLite integrity. The independent reviewer tightened the receipt envelope so `restore_id`, UTC `created_at`, integer counts/sizes, member IDs/hashes, state-family version facts, and the exact `receipt_integrity` object shape are validated in addition to the self-hash. A receipt's claimed compatibility outcome is never accepted by itself. Rehashing a receipt after changing outcome, compatibility metadata, restore scope, or malformed operation metadata does not pass without matching the independently supplied contract/attestation and strict receipt schema.

## 6. State-family behavior

- **Watchlists:** A4's coherent SQLite Online Backup snapshot is copied byte-for-byte. A5 opens only the restored DB read-only, requires `PRAGMA integrity_check=ok`, then reuses A4's read-only Watchlist integrity verifier. It does not construct/init a store, migrate schema, open the active product DB, or mutate the backup.
- **Security Master:** restore copies only the A4-declared accepted bytes. It does not fetch, refresh, activate, rollback, or rewrite pointers/releases. Family-version facts require the trusted source-specific caller attestation.
- **Governed evidence:** Result, Audit, F3, Request/plan, authorization/consumption, claim/receipt, bundles, source snapshots, and provenance are exact byte copies. No replay, Mode C materialization, authorization execution/consumption, claim issuance, F3 reconstruction, or current Security Master lookup occurs. Restored authorization remains historical data.
- **Derived/omitted members:** A5 restores only members actually declared and verified in A4. It neither discovers nor fills omissions.

## 7. Tests and containment

Focused command:

```text
python -m pytest -q tests/unit/test_unified_restore.py tests/unit/test_unified_backup.py tests/unit/test_unified_retention_inventory.py tests/unit/test_unified_replay_inspector.py tests/unit/test_m8r_08b_mcp_tool_contracts.py tests/unit/test_m8r_09_persistent_watchlists.py
```

Codex's original focused gate passed **109 tests, 393 warnings**. Independent exact-head review added two bounded contract tests and repairs: malformed receipt operation metadata can no longer be laundered by recomputing the receipt self-hash, and UNC/device-root restore destinations are rejected before filesystem probing. The reviewer focused gate after repairs passed **111 tests, 393 warnings**. The warnings are the existing Persistent Watchlist `jsonschema.RefResolver` deprecation. The gate covers direct compatibility, migration-only classification, newer/unknown versions, attestation binding, exact-byte restore, A4 member/manifest tamper, receipt/outcome/scope/version-metadata/operation-metadata rehash attempts, isolated/existing/protected/UNC targets, path safety vocabulary, resource bounds before member hashing, read-only restored verification, backup and declared source inventory immutability, offline socket sentinels, Watchlist SQLite integrity, and existing A4/A3/A2/MCP/Watchlist regressions. No default/full CI or live acceptance was run.

No HTTP/MCP route, MCP tool, schema, Catalog/Route/Executor, authorization mode, A2/A3/A4 implementation, or public `market_read_result` field is changed. No market/source acquisition or external network is used.

## 8. Limitations and deferred authority

- A4 proves the integrity of caller-declared members, not whole-installation completeness or attestation authenticity. A5 inherits both boundaries.
- Security Master version facts need a trusted source-specific internal caller; A5 does not establish an external signature/trust anchor.
- Known active/durable roots must be supplied by the trusted caller because L0 physical state-root mapping is deferred.
- A5 classifies migration need only. Migration graph/execution, rollback, activation, and installation initialization remain deferred; A6+ are not authorized by this record.
- Successful restore means an isolated declared-member tree was created and verified. It does not mean `ACTIVE_INSTALLATION`, `READY_TO_SERVE`, `MIGRATION_COMPLETE`, or `PRODUCTION_ACTIVATED`.

## 9. Stop boundary

Technical disposition: `L2_A5_RESTORE_COMPATIBILITY_AND_BOUNDED_RESTORE_ACCEPTANCE_REVIEW_PASS`. Owner acceptance is recorded under `L2_A5_RESTORE_COMPATIBILITY_AND_BOUNDED_RESTORE_OWNER_ACCEPTED_FOR_MERGE`, and merge closure completed through PR #349 at `97386f756f2dcc6dbf4d3ee7934a41066fa1b0c2`. A5 is CLOSED. Do not apply migration, activate state, or begin A6.
