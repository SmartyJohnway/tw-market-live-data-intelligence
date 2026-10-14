# Phase L L2-A1-R1 — State Classification Scope Clarification

**Date:** 2026-10-14
**Status:** FROZEN
**Disposition:** `L2_A1_R1_STATE_CLASSIFICATION_SCOPE_CLARIFICATION_FROZEN`
**Parent:** `L2_A1_REPLAY_SEMANTICS_CONTRACT_FROZEN`

## 1. Reason for clarification

L2-A1 correctly froze `MIGRATION_REQUIRED` and `UNSUPPORTED_NEWER_STATE` as L2 fail-closed
states, but its first-implementation wording placed them beside finalized-package replayability
states before an installation-state version authority existed.

A finalized evidence package can prove its own schema/projector compatibility. It cannot, by
itself, honestly prove that an installation or durable product state is migratable or newer than
the running application.

This clarification prevents the A2 package inspector from inventing migration authority merely
to populate every frozen vocabulary value.
## 2. Frozen placement of states

For one finalized governed evidence package, A2 may classify only package-local replayability:

- `EXISTING_VERIFIED`;
- `REPLAYABLE`;
- `REPLAY_UNAVAILABLE_MISSING_ARTIFACT`;
- `REPLAY_UNAVAILABLE_INTEGRITY_FAILED`;
- `REPLAY_UNAVAILABLE_UNSUPPORTED_VERSION`.

Unknown or unsupported package schema/projector versions remain
`REPLAY_UNAVAILABLE_UNSUPPORTED_VERSION`. They must not be relabeled as migration states without
an installation-state compatibility authority.

`MIGRATION_REQUIRED` and `UNSUPPORTED_NEWER_STATE` remain mandatory L2 vocabulary, but they are
reserved for the later state-compatibility / migration inspection boundary that can inspect a
versioned durable-state contract.
## 3. No weakening of L2 requirements

This R1 does not remove migration classification from Phase L. It fixes which authority is
allowed to emit it.

A later L2 compatibility tranche must establish the versioned installation/durable-state
contract before implementing `MIGRATION_REQUIRED`, `UNSUPPORTED_NEWER_STATE`, migration preview,
or migration apply.

Until then, A2 remains strictly read-only, package-local, zero-network, and zero-mutation.
