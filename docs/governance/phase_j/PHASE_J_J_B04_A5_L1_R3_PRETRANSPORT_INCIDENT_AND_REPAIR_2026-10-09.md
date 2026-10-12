# J-B04-A5-L1-R3 pre-transport incident and repair

Disposition: `J_B04_A5_L1_R3_READY_FOR_EXACT_HEAD_INDEPENDENT_REVIEW`.

Session #1 remains immutable terminal incident evidence at
`acceptance_runs/j-b04-a5-session-78e1b2c1db127926`. Attempt 1 was reserved,
but `transport_attempted=false`, logical GET was 0, and HTTP dispatch was 0.
No source was contacted. Its `HARD_BLOCK` is a runner/runtime defect, not a
TWSE, network, TLS, HTTP, or TWT48U contract failure.

## Cold-start diagnosis

In a fresh Python process, directly importing `official_get_once` from the H2
executor failed with:

```text
ImportError: cannot import name 'derive_h4_for_completed_plan' from partially initialized module 'server.services.phase_h_h2_twse_exright_executor' (most likely due to a circular import)
```

In a separate fresh Python process, importing `scripts.m8r_05b_03` first and
then importing `official_get_once` succeeded and returned a callable. Separate
scratch-temp writes of `session_authorization.json` and
`transport_attempt.json` through the existing sanitized writer also passed.

Root cause: `J_B04_A5_R3_ROOT_CAUSE_CONFIRMED_COLD_START_IMPORT_ORDER`.

## Repair

The A5 runner now has a narrow production adapter resolver. It imports
`scripts.m8r_05b_03` first, then obtains the existing
`phase_h_h2_twse_exright_executor.official_get_once`, checks that it is
callable, and does not invoke it. Resolution now occurs after runtime and lease
validation but before final Git checks, session initialization, and durable
attempt reservation. Resolver failure returns
`J_B04_A5_LIVE_TRANSPORT_ADAPTER_UNAVAILABLE`, stage
`transport_adapter_resolution`, and consumes no attempt slot.

Attempt evidence uses enumerated `failure_stage` values. Pre-transport adapter
errors may include sanitized exception module/type; source-stage exception
messages and tracebacks remain excluded from durable evidence.

The Session #1 directory and its terminal receipt were not edited. The
companion JSON records each Session #1 artifact hash and the cold-start
diagnostics. R3 made no live call, prepared no new production lease, and created
no new Owner authorization. The previous external authorization and lease are
not reproduced here.

Validation results and exact base/candidate default-ci comparison are recorded
in the companion JSON. Canonical state remains H2 `INACTIVE`, selected executor
`null`, J-B04 `BLOCKING`, Phase J `NOT_STARTED`, MCP `6`. PR #326 remains Draft
and unmerged. Stop for exact-head independent review; do not start Session #2.
