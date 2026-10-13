# Phase L L1 — Next Tranche Selection: Bounded Resource Snapshots

**Date:** 2026-10-13
**Base:** `main@ea0f4683e662b8d3f89c032ea94dd1ab139cebe2`
**Disposition:** `L1_NEXT_TRANCHE_SELECTION_COMPLETE_GO_BOUNDED_RESOURCE_SNAPSHOTS`
**Authority:** frozen L0; A0 runtime inventory; merged A1 lifecycle; merged Operational Correlation Foundation; merged Adapter Execution Timing.

## 1. Selection decision

The next smallest remaining L1 operability gap is **Bounded Resource Snapshots**. It is not pre-named `A2`.

Roadmap L.1 explicitly requires resource usage. The current product has no runtime process-memory sampler and only historical performance-baseline use of `resource.getrusage`. The merged operational event contract already allowlists `process_memory_bytes` but does not populate it.

Source-level elapsed timing remains valid, but current production source paths do not share one transport seam. H1/H2/H3/I2/I3 retain separate source functions/transports, so source timing would require a broader multi-source tranche.

`init` remains blocked by checkout-local initialization/state coupling. Shared user-config resolution still spans several root/default/precedence seams and is larger than a bounded resource snapshot tranche.
## 2. Minimum scope

This tranche may add only best-effort, instantaneous resource snapshots:

- current Local Service process working-set/RSS bytes on governed `/api/unified/*` operational events;
- managed service process memory in `status` / `doctor` when an owned service is running;
- disk-free bytes for fixed application/runtime roots in read-only `doctor` output.

The implementation must use only the Python standard library and existing Windows ctypes seams; no `psutil` or monitoring dependency may be added.

Unavailable resource data must be represented as unavailable/omitted and must never fail a valid product operation.

## 3. Explicit non-goals

No CPU-percentage interval sampling, background thread, polling loop, alert threshold, capacity-planning policy, process history, durable metric store, Prometheus/OpenTelemetry integration, L4 load-ceiling work, or source acquisition is authorized.

This tranche does not change Request/Result/Audit, authorization, evidence adapters, source transports, routing, MCP tool schemas, or retry/timeout semantics.