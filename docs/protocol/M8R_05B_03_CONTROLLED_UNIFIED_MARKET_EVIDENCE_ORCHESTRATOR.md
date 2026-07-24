# M8R-05B-03 controlled unified market evidence orchestrator

M8R-05B-03 is the first layer permitted to claim a valid M8R-05B-02 authorization, dispatch its exact approved operations, and write a final consumption state. It remains an explicit, finite callable integration surface; it is not a scheduler, polling loop, daemon, automatic retry mechanism, generic router, or market-data recommendation surface.

## Reused contracts and boundaries

- `scripts.m8r_05b_02.consumption_binding.evaluate_consumption_preflight` validates the immutable plan, owner authorization, consumption binding, expiry, and supplied unused state before any filesystem mutation.
- `scripts.m8r_05b_02.validator.validate_execution_authorization` verifies plan, input, operation, batch, capability, executor, and evidence bindings.
- `scripts.m8r_filesystem_safety.atomic_create_text_exclusive` supplies the atomic single-use claim, while `atomic_write_text` supplies contained receipt/bundle/final-state replacement.
- `scripts.m8r_03d_watchlist_controlled_executor` is the only currently routeable M8R-05B executor family. Its M8R-03D request/authorization contract is different, so this task does not pass a 05B authorization to it directly. A product-specific adapter must be explicitly registered through `ExecutorRegistry` and may receive only `ExecutionContext.bounded_request`.
- `docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.json` remains the source of the plan-selected executor IDs. The M8R-05B-03 registry never discovers modules or expands this set.

## Execution sequence

`execute_controlled_plan` receives explicit local artifacts, a caller-supplied evaluation timestamp, an explicit output root, and an injected `ExecutorRegistry`. It validates all bindings, atomically creates `consumption/<authorization_id>.json` with `state=claimed`, then dispatches approved operations sequentially. A claim is intentionally fail-closed: a crash after claiming cannot be retried as a fresh authorization.

Each adapter receives one immutable `ExecutionContext` per approved operation. It must return `status=success`, the exact `expected_evidence_contract`, and a nonempty `evidence` object. Evidence containing raw payload, cookie, token, authorization, or session fields is rejected. Adapter exceptions, unsupported executors, contract mismatch, and incomplete evidence become explicit operation omissions; they never trigger retry or scope expansion.

The resulting governed bundle retains only successful contained evidence plus omission reason codes. The receipt records all per-operation outcomes and the deterministic bundle hash. Receipt and bundle are written under the explicit contained root, then the consumption record is finalized to `state=consumed`. A filesystem failure after claim remains replay-blocking.

## Operator surface

`python -m scripts.m8r_05b_03.cli --check-only ...` validates supplied local artifacts and does not write or execute. The CLI intentionally has no default adapter registry and refuses execution, so a command cannot accidentally consume an authorization without a reviewed product integration. Execution is available only through the callable API with an explicit allowlisted registry.

## Explicit non-goals

No autonomous network access, executor auto-discovery, adapter import from user input, authorization creation, authorization reissue, consumption reset, scheduling, polling, background execution, full-market scan, raw payload retention, trading recommendation, or legacy M8R-03D authorization bypass is implemented.
