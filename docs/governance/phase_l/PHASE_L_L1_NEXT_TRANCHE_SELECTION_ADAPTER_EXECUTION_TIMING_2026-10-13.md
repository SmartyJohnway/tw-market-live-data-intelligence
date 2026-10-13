# Phase L L1 — Next Tranche Selection: Adapter Execution Timing

**Date:** 2026-10-13
**Base:** `main@e16303935fef75a38159c5cebfd7b74c37fd33f3`
**Disposition:** `L1_NEXT_TRANCHE_SELECTION_COMPLETE_GO_ADAPTER_EXECUTION_TIMING`
**Authority:** L0 frozen contract; A0 runtime inventory; merged A1 lifecycle tranche; merged Operational Correlation Foundation.

## 1. Selection decision

The next smallest L1 operability tranche is **Adapter Execution Timing**. It is intentionally not named `A2`.

Roadmap L.1 still requires source timing, adapter timing, resource usage, and network-attempt observability. The previous tranche already established cross-component `trace_id`, bounded events, MCP/HTTP/execute-once duration, reason codes, and an ephemeral diagnostic sink.

The remaining adapter-timing gap can be closed centrally at `scripts/m8r_05b_03/dispatch.py::dispatch_prepared()`, which is the common invocation boundary for approved single and batch runtime adapters. Therefore this tranche does not require touching each evidence adapter or source transport.

## 2. Why the other candidates are not selected first

- **Source timing:** still required, but there is no single common source-transport boundary across all active evidence families. Instrumenting it now would widen the tranche across multiple adapters/transports.
- **Bounded resource usage:** useful and still required, but it is orthogonal to request/adapter causality and provides less diagnostic value than the now-available central adapter boundary.
- **`tw-market init`:** remains blocked by checkout-local Security Master materialization/state-root coupling; wrapping it now would hide a portability defect.
- **Shared user-config resolver:** remains broader because host/port, Security Master, Watchlist, control root, service URL, and future state roots currently use separate seams.

## 3. Frozen scope

This tranche may:

1. measure monotonic elapsed time around each approved adapter or batch-adapter invocation;
2. emit one bounded operational event per actual adapter invocation;
3. preserve the existing operational `trace_id` inside the execute-once child process;
4. reference existing executor/capability/market/batch or operation identifiers only as bounded diagnostic metadata;
5. add deterministic tests proving timing, correlation, error-path emission, and no public artifact changes.

It must not:

- modify Request/Result/Audit/authorization schemas or bytes;
- add fields to adapter return objects;
- change retry, timeout, acquisition, routing, or executor selection semantics;
- introduce source-specific timing in this tranche;
- add background sampling, CPU polling, durable retention, or a new logging framework;
- change the six MCP tools.

## 4. Event semantics

The invocation event is operational-only. It records monotonic `duration_ms`, status, reason code when the callable raises, and bounded route identifiers. Single-operation calls may reference the governed operation/execution-request IDs already present in the approved request. Batch calls record batch identity and operation count rather than an unbounded list of operation IDs.

Adapter return validation remains a separate orchestration concern. The timing event measures the adapter callable itself; a later result-schema validation error must not be misrepresented as adapter latency failure.

Telemetry write failure remains fail-open and must not affect dispatch outcome.

## 5. Acceptance gates

Acceptance must prove:

- single and batch adapter calls emit exactly one invocation event per actual callable invocation;
- `duration_ms` uses monotonic elapsed time and is non-negative;
- timeout, orchestration error, and generic exception paths preserve existing dispatch semantics while emitting bounded reason codes;
- the same operational trace survives parent → execute-once child → adapter event;
- no adapter result object or canonical persisted artifact gains timing fields;
- event-sink failure cannot alter adapter success/failure semantics;
- focused dispatch, execute-once, correlation, and MCP/HTTP regressions remain green;
- market/source acquisition count remains zero for this tranche acceptance.

## 6. Deferred after this tranche

Source-level elapsed timing, bounded resource snapshots, `init` state-root repair, shared user-config resolution, and durable logging policy remain separate L1 candidates. No automatic continuation to L2-L7 is authorized.
