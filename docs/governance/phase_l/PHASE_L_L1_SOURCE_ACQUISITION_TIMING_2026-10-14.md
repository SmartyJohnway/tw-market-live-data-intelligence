# Phase L L1 — Source Acquisition Timing Coverage

**Date:** 2026-10-14
**Base:** `main@42ca42d8bbe12b591a266e1ea6637a70477a6e22`
**Disposition:** `L1_SOURCE_ACQUISITION_TIMING_ACCEPTANCE_REVIEW_PASS`
**Owner acceptance:** `L1_SOURCE_ACQUISITION_TIMING_OWNER_ACCEPTED_FOR_MERGE`
**Authority:** frozen L0; A0 runtime inventory; merged A1; merged Operational Correlation Foundation; merged Adapter Execution Timing; merged Bounded Resource Snapshots; selection record `L1_NEXT_TRANCHE_SELECTION_COMPLETE_GO_SOURCE_ACQUISITION_TIMING`.

## 1. Outcome

This tranche closes the explicit A0/L1 gap for monotonic source-acquisition elapsed timing without turning operational diagnostics into governed evidence.

A shared `timed_source_call()` observes one source-acquisition callable, emits one bounded `source.acquisition.completed` operational event, and returns or raises exactly as the wrapped callable did.

Event status is deliberately `returned` or `raised`. It describes the acquisition-call boundary only; it does not claim HTTP, source-contract, normalization, binding, currentness, or evidence success.

## 2. Event contract

Operational source timing uses the existing `tw_market_operational_event.v1` sink and current `trace_id`.

Allowed source timing fields are bounded `source_id`, market, capability reference, monotonic `duration_ms`, call-boundary status, and exception class name as `reason_code` when the callable raises.

Raw URL, query parameters, request/response headers, request/response body, authorization content, credentials, environment values, evidence bodies, and exception messages are not emitted.

The helper is fail-open for telemetry. A diagnostic sink failure cannot change an otherwise successful source call, and a source exception is re-raised unchanged after the timing observation is attempted.

No background sampler, timer thread, polling loop, durable retention policy, or second logging framework is introduced.

## 3. Current production coverage

The shared timing helper is applied to the current production acquisition seams for Phase G research source families, TWSE MIS current observation, TWSE/TPEx official EOD, H1 TPEx attention, H1 composite sources, H2 TWSE ex-right pre-open data, H3 TWSE stock-day acquisition, I1 market-state sources, I2 TAIFEX futures context, and I3 cash institutional-flow sources.

Where one governed capability performs multiple actual source calls, timing is emitted per actual wrapped acquisition call. Batch execution that shares one acquisition emits one source timing observation for that acquisition rather than one per target.

I1 is a special preservation case. `server/services/phase_i_i1_production_candidate.py` remains byte-for-byte unchanged relative to its accepted live-tested baseline `0f556ca79134fd8338406ba3299eea83deab3e88`.

Current production I1 registration now uses Phase L timing wrappers that inject a timed transport into the unchanged candidate. The historical implementation freeze guard remains active; the current activation validator was updated only to recognize the explicit observability wrapper at the registry boundary.

## 4. Deterministic acceptance

Final accepted deterministic gates on the completed design are:

- operational helper + source timing coverage + I1 frozen/wrapper acceptance: `52 passed`;
- Phase G/H production and batch regressions: `197 passed`;
- I2 transport/A2 offline + I3 + execute-once regressions: `76 passed`;
- central dispatch/result validation + MCP error/tool contracts: `50 passed`.

These four non-overlapping final groups total `375 passed`.

An additional attempted I2-A4 stateful suite produced `28 failed, 78 passed` because this fresh worktree is intentionally `NOT_INITIALIZED`; every failure occurred at Security Master loading before I2 source transport. No durable state was initialized or mutated to force those tests to run, and those environment-state failures are not accepted as source-timing regressions.

No live market/source request was authorized or performed for this tranche. All source-timing acceptance used deterministic or injected transport paths.

## 5. Containment and quality gates

`python -B -m compileall` over the changed runtime/test surface: PASS. `git diff --check`: PASS. UTF-8/trailing-whitespace audit: PASS.

Changed production behavior is limited to operational timing around already selected source acquisition callables. Schemas, configuration authority, capability catalog/routing authority, MCP tool definitions, source endpoints, TLS policy, retry policy, timeout policy, redirect policy, response-size ceilings, authorization semantics, and governed Result/Audit contracts are unchanged.

The current exact-six MCP surface remains unchanged. Operational timing does not enter Request, Result, Audit, evidence artifacts, citations, authorization, replay, or migration state.

No new dependency, source family, MCP tool, scheduler, polling loop, background thread, or persistent state class is introduced.

## 6. L1 stopping point

This tranche stops under:

`L1_SOURCE_ACQUISITION_TIMING_ACCEPTANCE_REVIEW_PASS`

Owner acceptance is recorded under `L1_SOURCE_ACQUISITION_TIMING_OWNER_ACCEPTED_FOR_MERGE`. Commit, push, PR, exact-head review, and merge are authorized closure operations.

With this tranche technically passing, the explicit L1 operability obligations identified by A0 are covered by the merged/accepted lifecycle, structured diagnostics/correlation, adapter timing, bounded resource snapshots, and this source-acquisition timing tranche. This record does not itself declare L1 complete.

After Owner acceptance and merge, the next correct action is a separate L1 exit review against L0/A0 obligations and deferred boundaries, not an implicit start of L2-L7 or a new implementation tranche.
