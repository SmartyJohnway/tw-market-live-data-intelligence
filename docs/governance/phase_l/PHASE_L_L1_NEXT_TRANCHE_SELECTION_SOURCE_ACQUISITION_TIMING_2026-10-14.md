# Phase L L1 — Next Tranche Selection: Source Acquisition Timing

**Date:** 2026-10-14
**Base:** `main@42ca42d8bbe12b591a266e1ea6637a70477a6e22`
**Disposition:** `L1_NEXT_TRANCHE_SELECTION_COMPLETE_GO_SOURCE_ACQUISITION_TIMING`

## Selection

After merged A1 lifecycle/status/doctor, Operational Correlation Foundation, Adapter Execution Timing, and Bounded Resource Snapshots, the remaining explicit L1 operability gap is monotonic source-acquisition elapsed timing.

`init` and durable-state physical relocation are not selected because L0/A0 defer physical state mapping, migration/backup, and portability acceptance to later Phase L work. Shared user-config resolution is also not selected because it would force a physical user-config path decision that L0 deliberately deferred.

The existing operational JSONL sink already satisfies the lean structured-diagnostics role; no second logging framework or durable retention policy is needed in this tranche.

## Bounded contract

The tranche adds a shared `timed_source_call()` operational helper and applies it only to current production source-acquisition seams.

Each event uses `source.acquisition.completed`, current operational `trace_id`, bounded `source_id`/market/capability references, monotonic `duration_ms`, and a call-status distinction of `returned` versus `raised`.

`returned` means the acquisition callable returned control; it does not claim semantic source success. Existing HTTP/source validation remains authoritative. Exceptions are re-raised unchanged after timing is emitted.

The helper must not record raw URL, headers, request/response bodies, credentials, environment, or evidence content. Telemetry failure must remain fail-open.

No source endpoint, retry, timeout, TLS, redirect, response-size, Result/Audit, authorization, Catalog/Route/Executor, or MCP six-tool contract changes are authorized.
