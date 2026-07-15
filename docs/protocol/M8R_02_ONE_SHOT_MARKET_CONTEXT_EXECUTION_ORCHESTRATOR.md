# M8R-02 One-Shot Market Context Execution Orchestrator

Status: `CONDITIONAL_GO`

Verified baseline: local `HEAD=85f437a0df48afdddbacb5add8df19f29f8f4767` on branch `work`; working tree was clean before M8R-02 edits. M8R-01F is accepted as `GO`, and M8R-02 was operator-provided in this task rather than inferred from repository state.

## Scope

M8R-02 adds a controlled execution layer over an already compiled `m8r_market_context_execution_plan.v1` and an exact `m8r_market_context_approval.v1`. It does not accept a raw user request as execution authority and does not add API, MCP, frontend, scheduler, polling, background, retry, ranking, prediction, recommendation, broker, cache, database, M9, or arbitrary-provider behavior.

## Executor capability matrix

| Planned operation | Existing executor/module | Accepted input | Actual output | Network behavior | Reuse | Adapter needed | Blocking gap |
|---|---|---|---|---|---|---|---|
| TWSE_MIS listed live-ish | `scripts/probe_twse_mis_rich_fields.py::fetch_twse_mis_rows` | bounded TWSE MIS symbols such as `tse_2330.tw` | raw MIS rows plus telemetry | network, timeout only; no orchestrator retry | executable_with_adapter | yes | production adapter must normalize safe observation envelope |
| TWSE_MIS OTC live-ish | same TWSE MIS bounded fetcher | bounded OTC symbols such as `otc_6488.tw` | raw MIS rows plus telemetry | network, timeout only | executable_with_adapter | yes | production adapter must preserve OTC route and bounded retention |
| TWSE_MIS TAIEX index | same TWSE MIS bounded fetcher / existing index route precedent | `tse_t00.tw` | raw MIS/index row | network, timeout only | executable_with_adapter | yes | production adapter must normalize index context |
| TWSE_OPENAPI official EOD | `scripts/m8a_twse_official_eod_adapter.py::execute_twse_official_eod_adapter` and `scripts/m8a_official_eod_execution.py::execute_official_eod_refresh` | bounded requested symbols, source `TWSE_OPENAPI` | adapter result with whole-market network scope and bounded retained symbols | network whole-market endpoint, bounded retention | executable_with_adapter | yes | M8R-02 must retain only approved symbols |
| TPEX_OPENAPI official EOD | `scripts/m8a_tpex_official_eod_adapter.py::execute_tpex_official_eod_adapter` and M8A refresh | bounded requested symbols, source `TPEX_OPENAPI` | adapter result with whole-market network scope and bounded retained symbols | network whole-market endpoint, bounded retention | executable_with_adapter | yes | M8R-02 must retain only approved symbols |
| TAIFEX_MIS monthly futures | `scripts/m8c_taifex_mis_execution.py::execute_taifex_mis_snapshot` plus context adapter | exact selector with product, contract month, monthly, regular | observations with selector/runtime identity and `raw_payload_retained=False` | bounded REST + SockJS snapshot, no orchestrator retry | executable_with_adapter | yes | adapter must declare exact-identity support; otherwise blocked before network |
| TAIFEX_MIS monthly options | same M8C execution and adapter | exact underlying/product, expiry, strike, call/put, monthly, regular | observations with exact selector/runtime identity | bounded REST + SockJS snapshot | executable_with_adapter | yes | weekly/after-hours/front-month substitution prohibited |
| TAIFEX_OPENAPI official EOD/statistical | `scripts/m8b_taifex_openapi_execution.py::execute_taifex_openapi_refresh` | requested products/contracts/sessions/trade dates | normalized derivative reference observations | network official OpenAPI endpoints | executable_with_adapter | yes | exact requested month/strike/session must be preserved |
| local_source_health_read | local source-health artifacts / M5Q precedent | approved local operation only | metadata caveated local source-health observation | no network | executable | no for M8R-02 fallback | old artifacts are not current operational proof |
| local_market_clock_evaluation | existing market-clock/session logic precedent | approved local operation only | caveated market session observation | no network | executable | no for M8R-02 fallback | unresolved session fails closed; regular session only |

## Reused modules and functions

M8R-02 consumes M8R-01/M8R-01F functions for plan hashing, internal consistency, approval binding, source eligibility, and output-scope validation. It uses `scripts.m8_multi_source_context_builder.build_multi_source_market_context` as the canonical M8 context-core builder and does not introduce a second canonical context schema.

## Preflight and network authorization

`preflight_approved_market_context_plan(...)` validates plan schema, rebuilt hash, embedded hash scope, approval schema/status/binding/expiry/consumption state, source allowlist, output scope, operation and target bounds, executor registration, network authorization, and TAIFEX exact-identity capability before any operation or artifact write. `allow_network` defaults to `False`; approval never implies network permission.

## Dispatch model and one-shot guarantees

The registry is a narrow static mapping keyed by `(operation_class, source_family)`. Dependency injection is required for tests and source-specific production adapters. Each invocation makes exactly one pass over approved logical operations. There is no orchestrator retry, polling loop, scheduler, daemon, background task, second refresh, startup fetch, or automatic refresh.

## TAIFEX exact-identity decision

The orchestrator passes the approved TAIFEX target identity to the executor and requires the executor to declare `supports_exact_derivative_identity=True`. Returned derivative identity is verified against the approved expiry/month, strike, call/put, contract type, and regular session where applicable. If support is absent, the operation is blocked before network with `executor_exact_identity_not_supported`. If returned identity mismatches, the target fails closed with `source_identity_mismatch`. Front-month substitution is prohibited.

## Operation result schema

Each logical operation produces one terminal result with schema `m8r_market_context_operation_result.v1`, including operation ID, target, context type, source family, operation class, route, status, timestamps, network-attempt flag, adapter invocation count, normalized source observation, source health, currentness, issues, returned identity, retained artifacts, and grouping metadata.

## Missing context and partial completion

Every requested target/context pair without usable context emits `m8r_market_context_missing_context.v1` with a reason code, operation status, source family, null fallback, and forbidden interpretations list. Package status is `ready`, `ready_with_caveats`, `partial`, or `blocked`; partial success is never described as complete or full-market.

## Execution receipt

Receipts use `m8r_market_context_execution_receipt.v1` and record approved target/operation counts, logical operations, adapter invocations, network/local attempted counts, successful and missing contexts, one-shot flags, no polling/scheduler/background/retry flags, bounded retention, no full-market retained output, no raw payload retained, package status, approval consumption, and returned derivative identities.

## Approval consumption

A single-use approval is consumed only after all preflight gates pass and execution begins. Failed preflight does not consume approval. The original approval object is not mutated silently; execution returns an explicit consumed approval-state artifact. Reusing a consumed approval is blocked before operation attempts.

## Artifact retention

`write_execution_artifacts(...)` writes only under a validated relative artifact root and creates a receipt-scoped directory containing execution plan, approval record, execution receipt, operation results, missing context, and M8 context core. Raw payload and full-market retained output are forbidden. No frontend/public, traversal, absolute, generated, credential, or secret path is accepted.

## Follow-up hardening

Single-use replay protection is store-backed. The returned `approval_state` is informational; the injected approval-consumption store is authoritative across independent invocations and may be filesystem-backed under the approved artifact root. Consumption is recorded after global preflight passes and before the first operation; if consumption recording fails, execution blocks with zero operation attempts.

Artifact writing now enforces approved output-scope fidelity: the production writer uses `plan.output_scope.artifact_root`, and any test override must exactly equal the approved root or fail with `approved_output_scope_mismatch`. The execution receipt records `approved_output_scope`.

Expected executor operational exceptions (`TimeoutError`, `ConnectionError`, `OSError`, and bounded orchestration/value/key errors) become failed operation results with sanitized `source_execution_failed` diagnostics. Unexpected executor exceptions become `internal_executor_error` operation results. Canonical M8-core builder failure is contained separately as `m8_context_core_status=build_failed` with `m8_context_core=null`; operation results and receipts are preserved.

Local source-health and market-clock observations now use `LOCAL_SOURCE_HEALTH` / `LOCAL_MARKET_CLOCK` and `LOCAL_CONTEXT`, preserve target market, and are retained outside canonical M8 core rather than being falsely attributed to `TWSE_MIS`.

Global preflight blockers are invalid plan/hash, invalid approval, approval replay, unsafe output scope, forbidden source, structurally invalid registry, and missing network permission. Per-operation blockers such as one adapter unavailable or one exact-identity capability missing produce terminal blocked operation results so unrelated compatible operations can proceed and package status can be `partial`.

## Tests and live validation

Unit tests are non-network and use injected fake executors. They cover global preflight failures, network-disabled blocking, one-shot/no-retry behavior, approval consumption/reuse blocking, partial completion, complete source families, TAIFEX futures/options exact-identity gates, retention, artifact writing, and M8 builder integration. No live validation was run for this implementation.

## Known caveats

The default production registry is intentionally fail-closed for network adapters until narrow source-specific adapters are wired and reviewed in M8R-02A. This is why the M8R-02 acceptance is `CONDITIONAL_GO`: approval integrity, replay protection, one-shot execution, exact identity, partial completion, canonical M8 core construction, output-scope fidelity, and artifact retention are safe, but live production network adapters remain explicit follow-up work rather than silently invoked.

Recommended successor: `M8R-02A-PRODUCTION-SOURCE-EXECUTOR-ADAPTER-INTEGRATION` before M8R-03, because production network adapters remain intentionally deferred.
