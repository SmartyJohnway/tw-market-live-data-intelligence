# Phase L L2-A1 — Replay Semantics Contract

**Date:** 2026-10-14
**Status:** FROZEN
**Disposition:** `L2_A1_REPLAY_SEMANTICS_CONTRACT_FROZEN`
**Authority:** frozen L0; L1 final closure; L2-A0 inventory.

## 1. Core semantic separation

L2 freezes three distinct operations. They must never silently substitute for one another.

### READ_EXISTING

Read and verify already persisted canonical output for one finalized governed package.

- external market/source calls: **forbidden**;
- authorization creation/consumption/reuse: **forbidden**;
- governed or derived writes: **forbidden**;
- current-source lookup: **forbidden**;
- missing canonical output: return a typed non-success state; do not reconstruct implicitly.

A successful read verifies the retained package sufficiently to establish that the persisted
Result/Audit is the governed output it claims to be.
### REPLAY_FROM_RETAINED_EVIDENCE

Deterministically reconstruct or verify a historical governed output using retained finalized
predecessors and retained evidence only.

- external market/source calls: **forbidden**;
- consumed authorization reuse or new execution authorization: **forbidden**;
- current-source fallback: **forbidden**;
- original evidence timestamps/currentness remain historical authority;
- replay time is diagnostic/reproduction metadata only, never a new observation time;
- replay must verify containment, schema/version support, hashes, lineage, and required artifacts;
- default replay output is in-memory or explicitly derived/rebuildable output, not silent mutation
  of the canonical package.

If required retained evidence is missing, corrupt, incompatible, or unsupported, replay fails
closed with a typed classification. It must not fetch replacement data.

### REFETCH_CURRENT_SOURCE

Acquire current source data only through a new governed execution:

Unified Request → validation/preview → explicit authorization → execute once → new Result/Audit.

It creates new IDs/timestamps/currentness and is never automatically invoked by read, replay,
restore, compatibility inspection, or migration.
## 2. Replayability classification

The first L2 implementation must be able to classify a finalized package without writing it:

- `EXISTING_VERIFIED` — persisted canonical Result/Audit output exists and verifies;
- `REPLAYABLE` — canonical derived output is absent, but required retained predecessors and
  evidence are present, compatible, and hash/lineage valid;
- `REPLAY_UNAVAILABLE_MISSING_ARTIFACT` — required retained bytes are absent;
- `REPLAY_UNAVAILABLE_INTEGRITY_FAILED` — hash, containment, lineage, or semantic verification fails;
- `REPLAY_UNAVAILABLE_UNSUPPORTED_VERSION` — schema/projector version cannot be reproduced;
- `MIGRATION_REQUIRED` — older supported state requires an explicit migration before the
  requested operation;
- `UNSUPPORTED_NEWER_STATE` — state is newer than this application supports and must fail closed.

These classifications describe local state only. None authorizes network activity.

## 3. Compatibility rule

Use the L0 rule: **write current, read supported history**. A persisted historical canonical
Result may be readable even when current code cannot reproduce it, provided its own governed
integrity/lineage can be verified under an explicitly supported historical reader contract.
Replayability is therefore stricter than readability.

No reader may silently rewrite historical bytes to the current schema. Migration is a separate,
explicit lifecycle operation governed later in L2.

## 4. Public-surface implication

The existing exact-six MCP surface is not changed by this contract. L2 first builds and proves
an internal read-only inspector. Public `market_read_result` semantics may only be changed after
that inspector demonstrates a safe non-writing path and regression review confirms compatibility.
## 5. Frozen non-goals

This contract does not choose a retention-day constant, final Windows state root, installer,
Docker volume mapping, or public backup format. It does not migrate any current state and does
not initialize missing production state.

It also does not revive M4 fixture replay as product authority, and it does not treat historical
acceptance scripts as runtime replay APIs.

## 6. Next bounded tranche

The first implementation tranche is a **Read-Only Finalized Package Inspector / Replayability
Classifier**. It must inspect one control package, verify retained state, classify replayability,
and perform zero writes and zero network activity.

Codex may implement that bounded tranche after receiving the companion handoff. Backup,
retention cleanup, restore, migration application, and public MCP/API changes remain out of
scope until this inspector is accepted.
