# Phase L L2-A2 — Codex Handoff: Read-Only Replayability Inspector

**Date:** 2026-10-14
**Base:** `main@4508fd6ee1d82e528b40a9adbda1a01a6d4bafe7`
**Prerequisites:** L2-A0 inventory complete; L2-A1 replay semantics frozen.
**Implementation role:** Codex bounded coding worker; ChatGPT remains reviewer/governor.

## Objective

Implement a pure read-only inspector for one finalized Unified control package. The inspector
must verify retained local state and classify whether the package has existing verified outputs,
is replayable from retained evidence, or is unavailable/incompatible.

The tranche must perform **zero external market/source calls, zero authorization creation or
consumption, and zero filesystem/database writes**.

Do not implement replay materialization yet. Do not change `market_read_result`, any public HTTP
route, MCP tool contracts, the exact-six tool surface, backup/restore, retention cleanup, or
migration application.
## Required classifications

Return one bounded structured inspection result with one primary state:

- `EXISTING_VERIFIED`
- `REPLAYABLE`
- `REPLAY_UNAVAILABLE_MISSING_ARTIFACT`
- `REPLAY_UNAVAILABLE_INTEGRITY_FAILED`
- `REPLAY_UNAVAILABLE_UNSUPPORTED_VERSION`
- `MIGRATION_REQUIRED`
- `UNSUPPORTED_NEWER_STATE`

The result should include only bounded identifiers/version facts needed to explain the state:
control package id, detected Request/Result/Audit schema versions, detected projector version
when available, persisted-output presence, and typed reason code. Do not return raw evidence or
entire Request/Result/Audit bodies.

## Verification requirements

Reuse or safely factor the existing package-verification substrate where possible:

- control package id/path containment;
- control manifest membership and SHA-256 verification;
- finalized claim state;
- receipt and bundle lookup;
- F3 reconstruction **in memory only**;
- `load_projection_inputs` schema, lineage, containment and evidence-hash verification;
- detection of complete/partial/multiple persisted Result/Audit/Markdown triplets;
- supported Request/Result/Audit/projector versions.

If factoring private helpers from `server/services/unified_mode_c.py`, preserve current Mode C
behavior exactly in this tranche. Do not make Mode C more or less writable yet.
## Mandatory non-goals

- no market/source/network call;
- no Security Master or Watchlist initialization/mutation;
- no authorization create/claim/consume;
- no Result/Audit/F3/Markdown materialization;
- no temp/cache/package write as part of inspection;
- no migration, backup, restore, cleanup, pin/delete implementation;
- no physical state-root redesign;
- no public route, MCP schema, or seventh tool;
- no change to current exact-six tool behavior;
- no adoption of the historical Phase C 30-day retention value as Phase L authority.

## Tests required

Use temporary deterministic packages and assert both return value and filesystem immutability.
At minimum cover:

1. finalized package with complete current persisted outputs → `EXISTING_VERIFIED`;
2. finalized package with no derived outputs but intact predecessors/evidence → `REPLAYABLE`;
3. missing required retained evidence → missing-artifact classification;
4. evidence/control hash tamper → integrity-failed classification;
5. partial Result/Audit/Markdown triplet → integrity/inconsistent fail-closed;
6. unsupported projector/schema version → unsupported-version classification;
7. invalid/out-of-root control package id → fail closed;
8. before/after file inventory and hashes identical for every inspection case;
9. monkeypatched network/acquisition seams are never invoked.

Do not initialize production state to make tests pass. Historical tests may remain historical.
## Suggested implementation shape

Prefer a small internal module such as `server/services/unified_replay_inspector.py` with one
pure inspection entry point. Internal naming may differ if an existing module offers a cleaner
boundary.

Do not duplicate cryptographic rules when a current verified helper can be factored safely.
However, avoid calling helpers that materialize F3 or Mode C derived outputs. Any refactor must
have regression tests proving existing Mode C behavior is byte/semantic compatible.

The inspector may accept an internal `control_root` override for deterministic tests. Public
callers must not gain arbitrary-path selection.

## Acceptance handoff back to ChatGPT

Return:

- exact changed-file list and diff summary;
- implementation design note;
- focused test commands/results;
- proof of zero writes using before/after file inventory/hash comparison;
- proof of zero network/acquisition invocation;
- any compatibility ambiguity discovered rather than silently choosing a migration policy.

Stop after this tranche. Do not commit, push, open a PR, modify governance status, or start the
next L2 tranche unless separately instructed.
