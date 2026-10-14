# Phase L L2-A3 — Retention Classification & Policy

**Date:** 2026-10-14
**Base:** `main@7b5f0fdca04dcd1ac5847f4582309a48e1984682`
**Technical disposition:** `L2_A3_RETENTION_CLASSIFICATION_AND_POLICY_ACCEPTANCE_REVIEW_PASS`
**Owner acceptance:** `L2_A3_RETENTION_CLASSIFICATION_AND_POLICY_OWNER_ACCEPTED_FOR_MERGE`
**Merged:** PR #345 / `378acb454a4e1e4e82e2be14b5957dc7d912f751`
**Authority:** frozen L0; L2-A0 inventory; frozen L2-A1; frozen A1-R1; A2 acceptance at PR #343; current implementation on the A3 branch.

## 1. Scope and implementation

A3 adds the internal read-only family registry at `server/services/unified_retention_inventory.py`. It returns deterministic bounded metadata and classifies only an explicitly supplied family. It does not scan, read, write, move, delete, archive, back up, restore, migrate, or mutate product state. It has no network or database operations.

Family identity is supplied by a caller that has established authority binding and lineage. Path names, extensions, “derived” appearance, and the word “cache” are not classification authority. Unknown or unbound input returns `UNCLASSIFIED_REQUIRES_POLICY`. An ephemeral family is classified as such only when family binding is verified and the caller proves there is no governed reference. This module does not itself establish those proofs.

## 2. Bounded vocabulary

- `state_class`: `CANONICAL_USER_STATE`, `GOVERNED_EVIDENCE`, `REBUILDABLE_DERIVED`, `EPHEMERAL`, `UNCLASSIFIED_REQUIRES_POLICY`.
- `rebuildable`: `NOT_REBUILDABLE`, `DETERMINISTIC_FROM_RETAINED_AUTHORITY`, `REQUIRES_CURRENT_MUTABLE_AUTHORITY`, `REQUIRES_REFETCH`, `UNKNOWN`.
- required/authority facts: `YES`, `NO`, `CONDITIONAL`, `UNKNOWN`.
- `deletion_eligible`: `PROHIBITED`, `NOT_YET_ELIGIBLE`, `POTENTIALLY_ELIGIBLE`, `EPHEMERAL`.
- `backup_tier`: `CORE`, `FULL_GOVERNED`, `DERIVED`, `NONE`, `UNDETERMINED`.

Missing proof remains `UNKNOWN` or `UNCLASSIFIED_REQUIRES_POLICY`. `RETENTION_DURATION_POLICY_DEFERRED` applies to every family: L0/A0 has no accepted duration or release-count authority. No number of days or versions is set here.

## 3. Retention matrix

All rows and all requested machine fields are provided by the deterministic Python registry. This summary highlights the classification and deletion decision; the registry is the full matrix authority for this candidate.

| Artifact family | Class | Replay / audit | Rebuild | Deletion eligibility | Backup |
|---|---|---|---|---|---|
| Security Master active release pointer | Canonical user state | No / Yes | Not rebuildable | Prohibited | Core |
| Security Master release history and rollback artifacts | Canonical user state | Conditional / Yes | Not rebuildable | Prohibited | Core |
| Persistent Watchlists and revision database | Canonical user state | No / Yes | Not rebuildable | Prohibited | Core |
| User/product settings | Canonical user state, inventory incomplete | No / Conditional | Unknown | Not yet eligible | Core |
| Finalized control package | Governed evidence | Yes / Yes | Not rebuildable | Prohibited | Full governed |
| Request and plan | Governed evidence | Yes / Yes | Not rebuildable | Prohibited | Full governed |
| Authorization and consumption binding | Governed evidence | Yes / Yes | Not rebuildable | Prohibited | Full governed |
| Execution claim | Governed evidence | Yes / Yes | Not rebuildable | Prohibited | Full governed |
| Execution receipt | Governed evidence | Yes / Yes | Not rebuildable | Prohibited | Full governed |
| Evidence bundle | Governed evidence | Yes / Yes | Not rebuildable | Prohibited | Full governed |
| Historical F3 validation artifact | Governed evidence | Yes / Yes | Not rebuildable | Prohibited | Full governed |
| Operation evidence and source snapshots | Governed evidence | Yes / Yes | Not rebuildable | Prohibited | Full governed |
| Selection provenance | Governed evidence | Conditional / Yes | Not rebuildable | Prohibited | Full governed |
| Persisted Result JSON / Markdown | Governed evidence | No / Yes | Deterministic from retained authority | Not yet eligible | Full governed |
| Persisted Audit package | Governed evidence | Yes / Yes | Deterministic from retained authority | Prohibited | Full governed |
| Persisted AI handoff | Rebuildable derived | No / Conditional | Deterministic from retained authority | Potentially eligible after prerequisites | Derived |
| Finalized package indexes | Rebuildable derived | No / No | Deterministic from retained authority | Potentially eligible after prerequisites | Derived |
| Cache with unproven ownership or lineage | Unclassified | Unknown / Unknown | Unknown | Not yet eligible | Undetermined |
| Proven preview-only temporary material | Ephemeral | No / No | Unknown / not assumed | Ephemeral class | None |
| Proven test/acceptance runtime material | Ephemeral | No / No | Unknown / not assumed | Ephemeral class | None |
| Operational JSONL diagnostics | Ephemeral if unreferenced | No / No | Unknown | Ephemeral class if proven unreferenced | None |
| Lifecycle ownership/runtime files | Ephemeral if no live owner | No / No | Unknown / not assumed | Ephemeral class if ownership proof passes | None |
| Any unknown artifact | Unclassified | Unknown / Unknown | Unknown | Not yet eligible | Undetermined |

The full registry includes `network_required_to_rebuild`, `current_mutable_authority_required_to_rebuild`, `deletion_prerequisites`, and `integrity_binding` for every row. Governed evidence is never reclassified as temporary because it appears generated or derived. In particular, retained historical F3 is replay-critical and cannot be reconstructed from current Security Master state.

## 4. Deletion and backup rules

A3 performs no deletion or cleanup. `PROHIBITED`, `NOT_YET_ELIGIBLE`, and `POTENTIALLY_ELIGIBLE` are policy classifications, not execution authorization. Potential eligibility is conditional on family-specific prerequisites, a future explicit retention policy, verified backup manifest and hashes when required, proof of lineage/reference closure, and proof that rebuild does not require refetch or current mutable authority. The family record enumerates its prerequisites.

L0 D11-D12 distinguish core backup (Security Master, Watchlists, user configuration, required pointers/metadata) from full governed backup (also Results, Audits, authorization records and retained source snapshots/artifacts). A3 records these tiers but creates no backup or backup manifest; backup/restore and manifest/hash verification remain a later authorized tranche.

## 5. Replay and audit implications

`READ_EXISTING`, `REPLAY_FROM_RETAINED_EVIDENCE`, and `REFETCH_CURRENT_SOURCE` remain distinct. The registry never initiates any of them. Result/Markdown and Audit stay non-disposable; required retained predecessors and evidence stay governed. Existing A2 remains package-local and read-only. A2's finding that missing historical F3 is not safely rebuildable from current Security Master is represented directly in the F3 row.

## 6. Evidence, tests, and containment

Codex focused gate: `python -m pytest -q tests/unit/test_unified_retention_inventory.py tests/unit/test_unified_replay_inspector.py tests/unit/test_m8r_08b_mcp_tool_contracts.py tests/unit/test_m8r_09_persistent_watchlists.py` → **59 passed, 393 warnings**. Warnings are the existing Watchlist `jsonschema.RefResolver` deprecations.

Independent ChatGPT reviewer found one conservative-policy repair: preview-only temporary material, test/acceptance runtime material, and lifecycle ownership/runtime files are ephemeral only after their proof prerequisites, but current authority does not prove deterministic rebuild from retained state. Their `rebuildable` field was therefore tightened from `DETERMINISTIC_FROM_RETAINED_AUTHORITY` to `UNKNOWN`; no deletion eligibility was relaxed. Reviewer also added an assertion that all machine policy fields remain inside the frozen bounded vocabularies. Reviewer focused rerun → **60 passed, 393 warnings**.

The tests cover deterministic complete rows, bounded vocabulary, protected governed families and F3, unknown/unbound fail-closed behavior, positive ephemeral proof requirements, and before/after file hashes with SQLite/network sentinels. Existing A2 inspector tests and exact-six MCP tool-contract tests are included. Public HTTP/MCP contracts, schemas, authorization semantics, and the six-tool list are unchanged by the candidate diff.

No market/source acquisition is performed. Classifier invocation has no filesystem, SQLite, socket, or product acquisition dependency. Test inventory/hash comparison demonstrates unchanged fixture files around classification; sentinels demonstrate no SQLite/network call.

## 7. Limitations and deferred authority

- No canonical installation settings store was confirmed in the inspected current substrate; its family remains conservative and inventory-incomplete.
- The classifier does not crawl product state or identify artifact ownership. Callers must supply verified family and lineage facts; otherwise the answer is unclassified.
- Cache semantics remain unknown unless ownership and predecessor/reference closure are proven.
- L0 retention durations and release counts remain deferred: `RETENTION_DURATION_POLICY_DEFERRED`.
- No migration policy is created. `MIGRATION_REQUIRED` and `UNSUPPORTED_NEWER_STATE` remain reserved for a versioned installation-state compatibility authority under A1-R1.
- No A2 replay semantics were changed; no replay defect was found in this scoped review.

## 8. Stop boundary

Technical disposition: `L2_A3_RETENTION_CLASSIFICATION_AND_POLICY_ACCEPTANCE_REVIEW_PASS`. Owner acceptance is recorded under `L2_A3_RETENTION_CLASSIFICATION_AND_POLICY_OWNER_ACCEPTED_FOR_MERGE`, and merge closure completed through PR #345 at `378acb454a4e1e4e82e2be14b5957dc7d912f751`. A3 is closed. No deletion, cleanup, backup, restore, migration, live acquisition, or A4/later tranche is authorized by this closure.
