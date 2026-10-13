# Phase L L1 — Bounded Resource Snapshots

**Date:** 2026-10-13
**Base:** `main@ea0f4683e662b8d3f89c032ea94dd1ab139cebe2`
**Disposition:** `L1_BOUNDED_RESOURCE_SNAPSHOTS_ACCEPTANCE_REVIEW_PASS`
**Owner acceptance:** `L1_BOUNDED_RESOURCE_SNAPSHOTS_OWNER_ACCEPTED_FOR_MERGE`
**Authority:** frozen L0; A0 runtime inventory; merged A1; merged Operational Correlation Foundation; merged Adapter Execution Timing; selection record `L1_NEXT_TRANCHE_SELECTION_COMPLETE_GO_BOUNDED_RESOURCE_SNAPSHOTS`.

## 1. Outcome

This tranche fills the smallest remaining L1 resource-usage gap with instantaneous, best-effort snapshots only.

The Local Service now adds its current process working-set/RSS bytes to bounded `/api/unified/*` operational events when available. Lifecycle `status`/`doctor` report the owned managed-service process memory plus application-root and runtime-root disk-free bytes.

Resource observations are operational diagnostics only. They do not become Audit, Result, evidence, authorization, replay, or migration authority.
## 2. Snapshot contract

The implementation is deliberately snapshot-only and best-effort:

- `process_memory_bytes`: current process working-set bytes on Windows; RSS-equivalent resident bytes on `/proc` platforms when available;
- `application_root_disk_free_bytes`: free bytes on the filesystem containing the current application root;
- `runtime_root_disk_free_bytes`: free bytes on the filesystem containing the existing A1 ephemeral runtime namespace;
- unavailable observations return `None` / partial diagnostic state rather than changing product execution semantics.

No CPU interval sampling, background sampler, polling loop, threshold policy, capacity alarm, historical metrics store, Prometheus/OpenTelemetry collector, or L4 resource-limit enforcement is introduced.

## 3. Integration surfaces

- `server/operational_diagnostics.py`: adds stdlib-only process-memory and disk-free snapshot helpers.
- `server/main.py`: adds current process memory to bounded `/api/unified/*` operational events when available.
- `scripts/tw_market_lifecycle.py`: adds read-only resource snapshots to `status` and a `resource_snapshot` doctor check.

The existing operational event allowlist is reused; no public Request, Result, Audit, authorization, MCP tool, Catalog, Route, Executor, evidence-family, or source-transport contract changes.

## 4. Deterministic acceptance

Resource-focused gate: `27 passed`.

Central controlled-dispatch regression: `98 passed`.

Lifecycle/MCP/HTTP/execute-once regression: `86 passed, 1 skipped, 18 warnings`.

The warnings are the existing `jsonschema.RefResolver` deprecation warnings from persistent Watchlist tests and are not introduced by this tranche.

Acceptance proves:

- current-process memory snapshot is a positive integer on the Tier-1 Windows host;
- invalid/unavailable process observations fail open to `None`;
- disk-free snapshots are non-negative integers for existing application/runtime filesystems;
- a governed Local Service request event can carry `process_memory_bytes` without changing the HTTP success payload;
- lifecycle `status` reports owned-service memory only for a verified running owner;
- `doctor` reports resource snapshot readiness without creating or repairing product state;
- resource snapshot failure cannot change normal market/evidence execution semantics.

`python -B -m compileall` over the changed runtime/test surface: PASS. `git diff --check`: PASS.

## 5. Native Windows local-only smoke

A managed Native Windows smoke used alternate loopback port 18767 with no market/source acquisition.

Observed smoke values:

- managed-service working set: approximately 63.8 MB;
- application-root free space: approximately 343 GB;
- runtime-root free space: approximately 75.9 GB;
- `/api/unified/capabilities`: HTTP 200 with caller-supplied private trace preserved;
- corresponding operational event included `process_memory_bytes`;
- `doctor` `resource_snapshot`: PASS;
- `stop`: PASS; post-stop status `NOT_RUNNING`; port 18767 had no remaining listener and no owner file remained.

The overall doctor status remained WARN only because the fresh installation identity was intentionally `NOT_INITIALIZED`; the resource snapshot check itself was PASS.

Market/source acquisition = 0; Security Master mutation = 0; Watchlist mutation = 0; authorization consumption = 0.

## 6. Containment and stop boundary

Changed runtime code is limited to operational diagnostics helpers, Local Service event metrics, lifecycle status/doctor resource reporting, and focused tests. No schema, Catalog/Route/Executor authority, evidence adapter, source transport, retry policy, timeout policy, authorization contract, or six-tool MCP definition is changed.

Source-level elapsed timing remains a separate L1 candidate because the current product has multiple source-specific transport seams rather than one common transport boundary. `init` remains deferred until initialization/state-root coupling is resolved. Shared user-config resolution remains a larger cross-cutting portability/configuration tranche.

This tranche stops under:

`L1_BOUNDED_RESOURCE_SNAPSHOTS_ACCEPTANCE_REVIEW_PASS`

Owner acceptance / merge authorization is recorded as `L1_BOUNDED_RESOURCE_SNAPSHOTS_OWNER_ACCEPTED_FOR_MERGE`. Commit, push, PR, exact-head review, and merge are the authorized closure operations. Do not begin another L1 tranche or L2-L7 until this accepted tranche is merged and a later Owner decision establishes the next boundary.
