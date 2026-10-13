# Phase L L1 — Next Tranche Selection: Operational Correlation Foundation

**Date:** 2026-10-13
**Base:** `main@62c04d098c5f580a14617a6917880f92f78271c8`
**Disposition:** `L1_NEXT_TRANCHE_SELECTION_COMPLETE_GO_OPERATIONAL_CORRELATION_FOUNDATION`
**Authority:** L0 `PHASE_L_L0_ARCHITECTURE_CONTRACT_FROZEN`; A0 `L1_A0_RUNTIME_OPERABILITY_INVENTORY_COMPLETE`; A1 `L1_A1_ACCEPTANCE_REVIEW_PASS` / Owner-accepted and merged.

## 1. Selection decision

The next smallest L1 implementation tranche is **Operational Correlation Foundation**. It is narrower than a general logging/telemetry project and does not pre-name the tranche `A2`.

A1 already provides lifecycle `start/status/stop/doctor`, stable JSON, typed reason codes, an invocation UUID named `operation_id`, and monotonic `duration_ms`. The remaining gap is not “no structured diagnostics”; it is the absence of a consistent cross-component operational correlation and event substrate across MCP, Local Service, and execute-once boundaries.

`tw-market init` is not selected next. The current explicit Security Master `update --live` path still drives `m8r_06_01b_materialize_production_inputs.py`, whose acquisition bundle base is checkout-local `data/security_master/input_bundles`. Wrapping that directly as product `init` would hide an unresolved application/state portability coupling.

Persistent product log retention, physical `LOG_ROOT`, user-config resolution, durable state relocation, source drift, Docker, migration/backup/replay, and installer/service-supervisor work remain outside this tranche.

## 2. Current-substrate findings

| Surface | Current evidence | Decision |
|---|---|---|
| A1 lifecycle | invocation `operation_id`, UTC start, monotonic `duration_ms`, reason codes | REUSE; do not break A1 JSON |
| HTTP Local Service | error-only random `trace_id`; no request-wide correlation middleware | ADD shared operational trace |
| MCP adapter | stdout reserved for protocol; startup diagnostics on stderr; no per-tool trace/duration | WRAP with structured stderr events |
| MCP HTTP client | fixed loopback, request/response byte bounds, no retry, bounded deadlines | REUSE; add private trace propagation only |
| execute-once parent | fixed child protocol and 130s bound; no elapsed/event metadata | WRAP operationally; do not change child public payload |
| source/Audit telemetry | governed IDs, source timestamps/currentness, attempt/network evidence already exist | REFERENCE ONLY; never mirror into logs |
| resource telemetry | no current product sampler; historical baseline uses optional `resource` only | ADD only bounded best-effort samples; no monitoring loop |
| current product log root | none | do not invent durable retention in this tranche |
## 3. Correlation contract

Operational correlation uses a dedicated `trace_id`; it does **not** reuse canonical governed identifiers.

- `trace_id`: runtime-diagnostic UUID generated once per MCP tool call or direct unified HTTP request and propagated across internal boundaries.
- A1 lifecycle `operation_id`: preserved for backward compatibility as the lifecycle invocation identifier; it is not reinterpreted as the canonical evidence `operation_id`.
- canonical `request_id`, `execution_request_id`, governed `operation_id`, `authorization_id`, and `execution_receipt_id`: optional references only when already known; their semantics and values remain unchanged.
- operational events must not create substitute canonical IDs or write governed truth.

The MCP adapter should generate a `trace_id` per tool call and pass it to the loopback Local Service through a private bounded header. Direct Local Service calls generate a new trace when no valid operational trace is supplied. The same trace should be used for service errors instead of generating unrelated error-only UUIDs.

Trace propagation into the fixed execute-once child must use private runtime context (for example a controlled environment value or explicit internal function parameter), not a new public request field and not a change to Request/Result/Audit/MCP schemas.

## 4. Operational event contract

The first event schema is intentionally small. Required semantics are:

```text
schema_version
timestamp_utc
level
component
event_code
trace_id
status
```

Optional bounded fields may include `duration_ms`, `reason_code`, `lifecycle_operation_id`, canonical ID references already known at that boundary, and a fixed-key `metrics` object. Arbitrary nested payloads are forbidden.

Events must never contain raw evidence, raw HTTP bodies, full Request/Result/Audit objects, authorization contents, environment dumps, credentials, tokens, DPAPI data, source HTML/JSON payloads, or unbounded exception/stack text.

Exact byte/string ceilings are implementation constants to be proven by deterministic tests before acceptance; they are not guessed in this selection record. Every event and every diagnostic tail must have a finite tested bound.
## 5. Sink and lifecycle boundary

This tranche must not freeze the final durable Windows `LOG_ROOT` or retention-days policy.

For the first implementation candidate:

- Local Service operational events may use an **ephemeral, size-bounded JSONL sink** in the existing A1 OS-temp runtime namespace so A1's managed service does not lose diagnostics to `DEVNULL`.
- MCP operational events remain structured one-line stderr output; MCP protocol stdout must remain pristine.
- Lifecycle `--json` remains the user-facing command result, not a duplicate event stream.
- `doctor` may report sink availability/path and a strictly bounded diagnostic tail, but must remain read-only.
- event-sink write/rotation failure must not convert a valid market operation into failure; telemetry is diagnostic, not canonical execution authority.

No background logger thread, polling loop, Prometheus/OpenTelemetry collector, Elasticsearch/Grafana dependency, or second Audit store is authorized.

Health polling and static Workbench asset requests are excluded from per-request event emission to prevent startup/status checks from creating event floods. The first HTTP integration scope is the governed `/api/unified/*` product surface.

## 6. Timing and bounded telemetry

- Use monotonic clocks for elapsed runtime duration; evidence `retrieved_at`, `observed_at`, publication time, and currentness timestamps remain evidence semantics and must not be repurposed as latency.
- MCP-to-Local-Service request duration and execute-once child duration are in scope.
- CPU percentage sampling is out of scope for this tranche because it requires an interval/sampler and adds no immediate diagnostic value.
- A bounded best-effort process-memory sample may be added where available without introducing a new mandatory dependency; unavailable metrics remain explicitly unavailable rather than failing execution.
- Disk/resource checks belong primarily in `doctor`; no recurring resource monitor is authorized.

Source/adapter elapsed timing is still a valid L1 obligation, but instrumenting every evidence adapter is **not** part of this smallest foundation tranche. It should be selected separately after the correlation/event substrate exists.

## 7. Minimum implementation surfaces

The implementation should remain bounded to shared operational-diagnostics support plus the narrow integration points needed for:

1. A1 lifecycle correlation/event sink wiring;
2. MCP tool-call trace creation and structured stderr events;
3. Local Service unified-route trace acceptance/generation and bounded events;
4. fixed execute-once parent duration/correlation propagation;
5. deterministic tests for ID propagation, size/redaction bounds, failure isolation, and stdout cleanliness.

It must not alter the six MCP tool schemas, governed Request/Result/Audit schemas, authorization semantics, capability routing, source acquisition policy, or evidence-family behavior.
## 8. Acceptance gates for the implementation tranche

Acceptance must prove all of the following:

- one operational `trace_id` survives MCP → Local Service → execute-once parent where those boundaries are traversed;
- direct HTTP requests receive/generated correlation without requiring MCP;
- existing A1 lifecycle JSON and six-tool MCP contracts remain backward compatible;
- governed Request/Result/Audit/authorization artifacts are byte/semantic unchanged except where tests already permit nondeterministic timestamps unrelated to this tranche;
- error responses reuse the active operational trace instead of generating unrelated trace IDs;
- durations use monotonic elapsed time and are non-negative/bounded;
- event serialization rejects or truncates over-bound fields deterministically;
- raw evidence, credentials, full environment, authorization body, and unbounded exceptions never appear in events;
- MCP stdout protocol remains clean under success and failure paths;
- event-sink failure is contained and does not fail an otherwise valid product operation;
- no startup market/source acquisition, no new retry, no polling/background telemetry loop, and no new persistent governed state;
- tests remain deterministic and non-network unless a separately authorized bounded live gate is later required.

## 9. Deferred L1 gaps after this tranche

This selection does not claim L1 completion. Remaining candidates include source/adapter elapsed timing, broader bounded resource telemetry, the product `init` path after initialization/state-root coupling is resolved, shared user-config resolution, and any final durable logging policy that can be separated cleanly from L2 retention and L6 packaging.

The next implementation must stop after the Operational Correlation Foundation is accepted. A later tranche is selected from the remaining L1 gaps; no automatic continuation to L2-L7 is authorized.

## 10. N0 closure

Current runtime code was read only during selection. No market/source acquisition, Security Master or Watchlist mutation, authorization consumption, runtime daemon launch, MCP/tool schema change, or product code modification occurred.

The only worktree change from this selection is this governance record. Implementation is **not yet performed**.
