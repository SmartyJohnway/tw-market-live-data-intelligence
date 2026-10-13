# Phase L L1 — Operational Correlation Foundation

**Date:** 2026-10-13
**Base:** `main@62c04d098c5f580a14617a6917880f92f78271c8`
**Disposition:** `L1_OPERATIONAL_CORRELATION_FOUNDATION_ACCEPTANCE_REVIEW_PASS`
**Owner acceptance:** `L1_OPERATIONAL_CORRELATION_FOUNDATION_OWNER_ACCEPTED_FOR_MERGE`
**Authority:** L0 `PHASE_L_L0_ARCHITECTURE_CONTRACT_FROZEN`; A0 `L1_A0_RUNTIME_OPERABILITY_INVENTORY_COMPLETE`; A1 `L1_A1_ACCEPTANCE_REVIEW_PASS`; N0 `L1_NEXT_TRANCHE_SELECTION_COMPLETE_GO_OPERATIONAL_CORRELATION_FOUNDATION`.

## 1. Scope and outcome

This tranche implements the smallest cross-component operational correlation substrate after A1. It is intentionally not named `A2` and does not claim L1 completion.

The implementation adds one operational `trace_id` across MCP tool dispatch, the loopback Local Service, and the execute-once parent/child boundary. It adds bounded diagnostic events without changing governed Request, Result, Audit, authorization, capability, routing, or evidence-family semantics.

`Audit` remains governed truth. Operational events answer runtime diagnostic questions only and are not accepted as evidence, authorization, or replay authority.

No market/source acquisition was performed by this tranche or its acceptance smoke.

## 2. Correlation semantics

Operational correlation uses a dedicated UUID `trace_id`.

- MCP generates one trace per tool call.
- MCP passes the trace only through private loopback header `X-TW-Market-Trace-ID`.
- Direct `/api/unified/*` calls accept a valid private trace or generate a new one.
- Local Service error bodies that already expose `trace_id` reuse the active request trace.
- Execute-once passes the active trace to the fixed child through private environment `TW_MARKET_OPERATIONAL_TRACE_ID`.
- The fixed child public protocol is unchanged and does not return the operational trace.
- A1 lifecycle `operation_id` remains a lifecycle invocation identifier; it is not redefined as governed operation identity.

Canonical `request_id`, `execution_request_id`, governed `operation_id`, `authorization_id`, and `execution_receipt_id` remain canonical identifiers and may appear only as bounded references in operational events.

## 3. Event and sink contract

Shared substrate: `server/operational_diagnostics.py`.

The event schema is `tw_market_operational_event.v1`. Required fields are schema version, UTC timestamp, level, component, event code, trace ID, and status. Optional fields are allowlisted references, reason code, and fixed-key metrics.

Implementation bounds are explicit:

- string fields: 256 characters;
- serialized event: 4096 bytes maximum;
- ephemeral JSONL file: 256 KiB maximum before bounded reset;
- unknown reference and metric keys are dropped;
- oversized manually constructed events are rejected deterministically;
- sink I/O failure is contained and cannot fail an otherwise valid product operation.

Raw evidence, raw HTTP bodies, full Request/Result/Audit objects, authorization bodies, environment dumps, credentials, tokens, DPAPI data, and unbounded exceptions are not accepted event fields.

Managed Native startup places the JSONL sink under the existing A1 OS-temp runtime namespace. This is ephemeral runtime state, not the final durable `LOG_ROOT`. `doctor` reports sink readiness without creating or repairing the path. MCP events are one-line JSON on stderr; protocol stdout remains reserved for MCP.

## 4. Integration surfaces

- `scripts/tw_market_lifecycle.py`: adds separate `trace_id`, event sink path reporting, read-only doctor sink check, and start/stop events.
- `server/main.py`: adds request-wide correlation middleware only for `/api/unified/*`; health/static requests are excluded.
- `server/unified_workbench_router.py`: handled error responses reuse the active trace.
- `server/unified_mcp/`: per-tool trace creation, private header propagation, same-trace error mapping, bounded stderr event.
- `server/services/unified_mode_b2_execution.py`: monotonic child duration, bounded success/failure event, private trace environment propagation.

## 5. Deterministic acceptance

Final focused regression after all implementation and test changes:

`80 passed, 1 skipped, 18 warnings`.

The one skip is pre-existing test selection behavior. The 18 warnings are the existing `jsonschema.RefResolver` deprecation warnings from persistent Watchlist tests and are not introduced by this tranche.

The focused set covers the diagnostics substrate, A1 lifecycle, MCP error mapping, exact-six MCP tool contracts, fixed execute-once parent protocol, Unified HTTP API, and real stdio MCP integration.

Specific acceptance evidence includes:

- MCP tool calls generate distinct UUID traces and propagate them by private loopback header without changing request bodies.
- real stdio MCP retains clean protocol stdout while structured operational events appear on stderr;
- direct HTTP success returns the operational trace as response header without adding it to the canonical success payload;
- handled HTTP error body trace equals the response-header trace;
- HTTP trace reaches the execute-once child private environment while the fixed child public result remains byte-shape compatible;
- event fields are allowlisted, strings are bounded, oversized events fail deterministically, and sink I/O failures fail open.

`python -B -m compileall` over the changed runtime/test surface: PASS. `git diff --check`: PASS.

## 6. Native Windows local-only smoke

A managed Native Windows smoke used alternate loopback port 18766 with a fresh `NOT_INITIALIZED` installation.

- `start`: PASS; managed service reached `STARTED`.
- local `/api/unified/capabilities`: HTTP 200; caller-supplied valid trace returned unchanged in the private response header; capability count 14.
- ephemeral event file contained bounded lifecycle and Local Service events with the expected trace correlation.
- `status`: service alive, identity `NOT_INITIALIZED`, route projection `READY`, MCP `READY`.
- `doctor`: expected setup WARNs only; operational event sink PASS, exact-six MCP contract PASS, MCP startup check PASS.
- `stop`: PASS / `STOPPED`.
- post-stop `status`: `NOT_RUNNING`; no managed service remained.

All smoke traffic was loopback/local. Market/source acquisition count = 0; Security Master mutation = 0; Watchlist mutation = 0; authorization consumption = 0.

## 7. Containment and non-goals

Changed implementation surfaces are limited to lifecycle diagnostics, Local Service correlation, MCP delegation/error mapping, execute-once parent diagnostics, and their tests. Canonical Request/Result/Audit schemas, authorization contracts, Catalog/Route/Executor configuration, evidence adapters, and MCP tool definitions were not modified. MCP remains exactly six tools.

No durable `LOG_ROOT`, retention-days policy, background sampler, polling loop, CPU interval sampling, Prometheus/OpenTelemetry stack, service supervisor, Docker work, migration/backup/replay work, source-drift work, or new evidence family is included.

## 8. Deferred L1 gaps and stop boundary

This foundation does not complete all L1 obligations. Remaining candidates include source/adapter elapsed timing, broader bounded resource telemetry, the product `init` path after initialization/state-root coupling is resolved, shared user-config resolution, and any later durable logging policy that can remain separate from L2 retention and L6 packaging.

The current implementation stops here under:

`L1_OPERATIONAL_CORRELATION_FOUNDATION_ACCEPTANCE_REVIEW_PASS`

Owner acceptance and merge authorization are recorded as `L1_OPERATIONAL_CORRELATION_FOUNDATION_OWNER_ACCEPTED_FOR_MERGE`. Commit, push, PR, and merge are the authorized closure operations. Do not begin another L1 tranche or L2-L7 until this tranche is merged and a later Owner decision establishes the next boundary.
