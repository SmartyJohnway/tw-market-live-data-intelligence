# Phase L L1 — Adapter Execution Timing

**Date:** 2026-10-13
**Base:** `main@e16303935fef75a38159c5cebfd7b74c37fd33f3`
**Disposition:** `L1_ADAPTER_EXECUTION_TIMING_ACCEPTANCE_REVIEW_PASS`
**Owner acceptance:** `L1_ADAPTER_EXECUTION_TIMING_OWNER_ACCEPTED_FOR_MERGE`
**Authority:** L0 frozen contract; A0 runtime inventory; merged L1-A1; merged Operational Correlation Foundation; selection disposition `L1_NEXT_TRANCHE_SELECTION_COMPLETE_GO_ADAPTER_EXECUTION_TIMING`.

## 1. Scope and outcome

This tranche closes the L1 **adapter timing** gap at the common controlled-dispatch boundary. It is intentionally not named `A2` and does not claim L1 completion.

`dispatch_prepared()` remains the orchestration authority. Actual single-adapter and batch-adapter callable invocations are wrapped only for operational timing and bounded diagnostic emission. Adapter return values, result validation, normalized failure semantics, routing, authorization, acquisition policy, and canonical persistence remain unchanged.

No evidence adapter or source transport was modified. No market/source acquisition was performed for implementation or acceptance.

## 2. Timing and event semantics

Elapsed time uses `time.monotonic()` around the actual adapter callable only.

- single invocation event: `adapter.execution.completed`;
- batch invocation event: `adapter.batch.completed`;
- component: `adapter_dispatch`;
- metrics: bounded `duration_ms` plus `operation_count`;
- references: executor, capability, market, batch group; a single invocation may additionally reference the existing governed operation and execution-request IDs.

A batch callable emits one event for the callable, not one event per member operation. The event does not carry an unbounded operation-ID list.

Timing ends when the adapter callable returns. Result-schema/artifact validation remains outside adapter elapsed time, so a later validation failure is not mislabeled as adapter-call failure.

`OrchestrationError` is re-raised with its existing code. `TimeoutError` and generic exceptions retain the existing outer normalization to `adapter_timeout` and `adapter_exception`. Diagnostic sink failure remains fail-open.

## 3. Trace continuity

The previous Operational Correlation Foundation already passes the parent trace through private `TW_MARKET_OPERATIONAL_TRACE_ID`. This tranche makes the fixed execute-once child bind that environment value into the operational context before controlled execution and reset it on exit.

Therefore the same diagnostic `trace_id` can correlate MCP/HTTP → execute-once parent → child → adapter invocation without adding `trace_id` to the public child result or governed Request/Result/Audit artifacts.

## 4. Deterministic acceptance

Final broad focused regression after all runtime/test changes:

`179 passed, 1 skipped, 18 warnings`.

The existing warnings are `jsonschema.RefResolver` deprecation warnings and are not introduced by this tranche. The suite covers controlled dispatch, result validation, batch execution, dependency ordering, H3 and I1 deterministic production candidates, execute-once, operational diagnostics, multi-artifact integration, A1 lifecycle, MCP contracts/errors, Unified HTTP, and real stdio MCP integration.

Earlier targeted gates were `37 passed`, `116 passed`, and after fault-path hardening `39 passed`.

Acceptance specifically proves:

- one event per actual single or batch adapter callable invocation;
- deterministic monotonic elapsed timing and non-negative real-child timing;
- batch event cardinality is one per batch callable, not one per member operation;
- timeout normalization remains `adapter_timeout`;
- generic exception normalization remains `adapter_exception`;
- adapter `OrchestrationError` remains re-raised with the original code;
- event-sink failure cannot change a successful dispatch result;
- public operation results and execute-once child output gain no timing or trace fields;
- parent operational trace reaches child adapter events unchanged.

`python -B -m compileall` over the changed runtime/test surface: PASS. `git diff --check`: PASS.

## 5. Containment and stop boundary

Changed runtime code is limited to the common dispatch instrumentation, child trace binding, and the existing operational-event allowlist. No schemas, Catalog/Route/Executor authority, evidence adapter, source transport, MCP tool definition, retry policy, timeout policy, or authorization contract is changed.

Market/source acquisition = 0; production Security Master mutation = 0; Watchlist mutation = 0; production authorization consumption = 0.

Remaining L1 candidates are source-level elapsed timing, bounded resource snapshots, `init` after state-root coupling repair, shared user-config resolution, and any later durable logging policy that remains separate from L2 retention/L6 packaging.

This tranche stops under:

`L1_ADAPTER_EXECUTION_TIMING_ACCEPTANCE_REVIEW_PASS`

Owner acceptance and merge authorization are recorded as `L1_ADAPTER_EXECUTION_TIMING_OWNER_ACCEPTED_FOR_MERGE`. Commit, push, PR, and merge are the authorized closure operations. Do not begin another L1 tranche or L2-L7 until this tranche is merged and a later Owner decision establishes the next boundary.
