# V1.0.0-rc.1 release notes draft

This is a release-candidate draft, not a tag or published GitHub Release.

## Current product path

- The installation-local Security Master supplies governed identity resolution.
- Persistent Watchlists preserve user-owned, versioned watchlist state.
- The Unified Workbench and six-tool MCP surface provide bounded preview and
  explicit execute-once market-evidence workflows.
- Mode C produces canonical Result, audit, citation, and AI-handoff outputs.

## Installation and migration

Install the locked dependencies, verify the environment, and check Security
Master status before running an explicit initialization update. A fresh
installation reporting `NOT_INITIALIZED` is an expected fail-closed state.
See [V1 Release Candidate](V1_RELEASE_CANDIDATE.md) and
[V1 Migration](V1_MIGRATION.md).

## Compatibility and limits

V1 preserves governed historical evidence for audit without treating it as a
current runtime fallback. It does not add a scheduler, background refresh,
trading, order routing, model-selected URLs, or model-selected executors.

## Upgrade guidance

Existing local installations retain immutable Security Master releases and
watchlist revisions. Operators should export user data before an upgrade and
use the documented explicit migration path when a future persisted-schema
change requires one.
