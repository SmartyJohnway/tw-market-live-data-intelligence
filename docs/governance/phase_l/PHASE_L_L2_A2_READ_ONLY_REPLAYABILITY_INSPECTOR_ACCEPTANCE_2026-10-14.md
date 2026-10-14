# Phase L L2-A2 — Read-Only Replayability Inspector Acceptance

**Date:** 2026-10-14
**Base:** `main@2398e1fa4c3501ccd9e65efdfa428beaad05117d`
**Disposition:** `L2_A2_READ_ONLY_REPLAYABILITY_INSPECTOR_ACCEPTANCE_REVIEW_PASS`
**Owner acceptance:** `L2_A2_READ_ONLY_REPLAYABILITY_INSPECTOR_OWNER_ACCEPTED_FOR_MERGE`
**Merged:** PR #343 / `bdd9588bc34ab25af8e22ba7cd7900160a56abf5`
**Authority:** L2-A0 inventory; frozen L2-A1 semantics; L2-A1-R1 scope clarification.

## 1. Outcome

The bounded A2 implementation adds an internal read-only inspector for one finalized Unified
control package. It does not change `market_read_result`, HTTP routes, MCP contracts, or the
exact-six tool surface.

The inspector verifies retained control-package containment, manifest/member SHA-256 integrity,
finalized execution lineage, predecessor/evidence schemas and hashes, persisted Result/Audit
compatibility, projector support, and exact persisted-output reproduction when outputs exist.

It returns bounded metadata only; raw Request/Result/Audit/evidence bodies are not returned.
## 2. Accepted package-local states

A2 emits the package-local states authorized by L2-A1-R1:

- `EXISTING_VERIFIED` when one persisted supported Result/Markdown/Audit triplet exactly matches
  deterministic reproduction from retained verified predecessors;
- `REPLAYABLE` when persisted derived output is absent but the retained finalized package is
  sufficient for deterministic in-memory reproduction;
- missing-artifact, integrity-failed, and unsupported-version states for fail-closed outcomes.

Historical F3 is mandatory retained evidence for A2. A missing F3 is not reconstructed from the
current Security Master because the retained package contains only its binding hash, not the
historical identity authority needed to reproduce F3 honestly.

`MIGRATION_REQUIRED` and `UNSUPPORTED_NEWER_STATE` remain frozen L2 vocabulary but are not
emitted by A2. L2-A1-R1 reserves them for a later versioned installation-state compatibility
boundary rather than letting A2 guess migration policy from an artifact schema.
## 3. Zero-write / zero-network proof

The A2 tests install write/network/state sentinels around the inspector invocation and compare a
before/after inventory of every package file and directory with SHA-256 for all files.

During inspection, the tests forbid filesystem write modes and mutation methods, SQLite connect,
socket connect, production acquisition adapters, Mode B2 package/ticket writers, Mode C F3 and
materialization helpers, and current Security Master lookup.

All accepted cases report zero sentinel calls and identical before/after package inventory.
Test fixture setup may materialize synthetic outputs before inspection; those setup writes are
outside the guarded inspector call and are not product behavior.

No market/source acquisition, production state mutation, or authorization creation/consumption
was performed during A2 implementation or review.

## 4. Focused and static verification

Codex final focused gate: `37 passed, 4 historical deselected`.
Independent ChatGPT reviewer rerun: `37 passed, 4 historical deselected`.

`py_compile` for the new module/test: PASS. `git diff --check`: PASS.
Runtime Skill guide sync: PASS / exact six tools. Portable Catalog sync: PASS.
No existing runtime module, HTTP route, MCP module, schema, Catalog/Route/Executor authority, or
Mode C implementation was modified.
## 5. Default-CI disposition

Codex also ran the repository `default-ci` profile in the fresh A2 worktree:

`1244 passed, 41 failed, 4 skipped, 5 deselected, 18 warnings`.

None of the 41 failures is the new A2 inspector/test. The failures are confined to existing
current-main authority debt: 28 state-dependent I2-A4 tests that fail before transport on fresh
`NOT_INITIALIZED` identity; 8 I3 historical/frozen transport-shape containment assertions; one
Phase H compatibility assertion in the same historical-shape family; and four Phase J readiness
assertions that still expect the older Roadmap Phase J unchecked state.

A2 adds only two runtime/test files and no existing code imports the new inspector outside its
new focused test. Therefore these failures are recorded, not repaired or reclassified inside A2.
They remain separate test-authority cleanup work and do not establish an A2 regression.

## 6. Stop boundary

A2 stops under:

`L2_A2_READ_ONLY_REPLAYABILITY_INSPECTOR_OWNER_ACCEPTED_FOR_MERGE`

Owner acceptance is recorded and merge closure completed through PR #343 at `bdd9588bc34ab25af8e22ba7cd7900160a56abf5`. Do not start backup/restore,
retention cleanup, migration apply, public `market_read_result` semantic changes, or the next L2
implementation tranche without separate Owner authorization.
