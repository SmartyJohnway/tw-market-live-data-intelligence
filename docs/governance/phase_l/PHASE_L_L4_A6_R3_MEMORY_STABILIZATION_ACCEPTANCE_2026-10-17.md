# L4-A6-R3 Memory Stabilization Acceptance — 2026-10-17

## Authority and preserved history

This is an offline continuation of the L4-A6 resource/load/concurrency acceptance. No A7 work was started. The entry commit remains `330e84891a1a3b83a79d73806b4543fb1704c2fc` with entry tree `6c9681ae891652dd62f14a1a65c15083c1cf5728`; `origin/main` was `c8c23e2c1c47d7695ee63c3c527b8461a9cf16b2`.

The initial A6 run and both earlier holds remain immutable. R1 preserved its `HOLD_RUNAWAY_GROWTH` memory matrix (`a9ef54629c28de13132310ff0afe9eaa982eeb7c8678f70996bf854d4b84ac01`). R2 preserved its sampler-repair PASS, memory HOLD (`ce55533ea845db477d586410eabedb77023c520922c2caffe08893e11d221e5a`), and 30-cycle diagnostic (`83fba3cc5c8d4bcb0a1bd8868d0ee0bf2484e51303e1baf9506cca07a51f533f`). The historical chain is hash-bound in `acceptance_runs/l4-a6-r3-20261017T150419Z/historical_hold_chain.json`.

## R3 memory acceptance

R3 run: `l4-a6-r3-20261017T150419Z`. The same bounded M8 planning workload was measured for 1,000 cycles after 30 warm-up cycles. Tracemalloc began after warm-up. GC and memory/object observations were taken at deterministic checkpoints. Four equal 250-cycle retained-growth slopes were `223.72`, `-36.904`, `-105.86`, and `-118.696` bytes/cycle. RSS observation slopes were `3244.032`, `1818.624`, `1572.864`, and `622.592` bytes/cycle; RSS is observational, not a hard threshold.

Functional output hashes remained identical. No product-defined request/result/schema type showed proportional live-object growth. Generic built-in container counts are disclosed in the object matrix: tracked `dict` deltas from warm-up were 0, 33, 65, and 97; those generic counts alone do not identify domain ownership. Product-associated retained traceback bytes declined by equal window (17,000; 3,950; 1,600; 500), and allocation counts at the highlighted product-containing trace declined (1.36; 0.316; 0.164; 0.04 per cycle). The full traceback frames and per-checkpoint object counts are preserved in the R3 evidence package. RSS showed no independently demonstrated fixed per-request linear pattern.

M8 is classified `PASS_BOUNDED_CACHE_STABILIZATION`. The former five-sample monotonic rule is retained as historical evidence but is insufficient for final classification; it correctly triggered the longer investigation. No RSS cap, watchdog, periodic GC, cache clearing, restart, recycling, or eviction behavior was added. The final policy is `EXPLICIT_NO_HARD_RUNTIME_LIMIT_WITH_STRUCTURAL_BOUND`; no machine-independent maximum RSS is claimed.

## R1 repairs and timeout envelope

The Watchlist low-disk regression passed: an existing current-schema store reopened and served reads while disk admission failed; a new DB failed before SQLite file creation; preview/commit writes failed closed without changing version/history. Automatic revision truncation remains `NO`; each new persistent write is subject to dynamic fail-closed disk admission.

The middleware order test passed with outer-to-inner `LocalNetworkBoundaryMiddleware`, `LocalControlPlaneBoundaryMiddleware`, `ResourceAdmissionMiddleware`, `CORSMiddleware`. Cross-origin privileged browser requests were rejected before acquiring the resource slot. The resource-intensive ceiling remains one, fail-fast, with no queue.

The exhaustive R3 timeout matrix contains 17 active network-required executor registry entries, each with finite positive timeout authority, plus MCP ordinary/action calls, both Local Service action endpoints, the Mode B2 execute-once parent/child, and supported lifecycle subprocess/readiness/cleanup paths. The Mode B2 child ceiling is 130 seconds and the Local Service action timeout is 145 seconds (`130 < 145`). Automatic retry count is zero in the reviewed matrix. `WHOLE-SERVER GLOBAL HARD DEADLINE = NOT_USED_BY_DESIGN`: network/action work is bounded at transport/executable boundaries; local deterministic work uses structural bounds, and unsafe forced ASGI cancellation is not introduced.

## Finding reconciliation and gate outcome

R3 evidence supports `RES-001`, `RES-002`, `RES-003`, `LOAD-001`, and `LOAD-004` as `COVERED`. A3 resource residuals are reconciled as requested: `IN-003` is resolved by dynamic write admission with no auto-truncation; `OUT-002` and `OUT-003` are accepted under structural bounds and long-horizon memory evidence; `LOAD-002` and `LOAD-003` are accepted with the A6 resource policy.

The focused gate passed: 57 passed, 0 failed. The bounded integrated gate reported 308 passed, 1 existing explicit fixture skip, and 2 failures. The two failures were independently reproduced in the historical Mode C tamper-helper tests:

- `test_existing_result_semantic_tamper_with_rewritten_hash_is_rejected`
- `test_existing_audit_semantic_tamper_with_rewritten_hash_is_rejected`

Both attempt to read a `.v1` result/audit path after the current fixture builder, which does not create those paths. Neither failure was deselected or modified. This is the reason the complete R3 disposition remains `L4_A6_RESOURCE_LOAD_CONCURRENCY_ACCEPTANCE_HOLD`, despite the memory, timeout, low-disk, middleware, and finding-specific evidence passing. No commit was made.

All offline validators passed: dependency supply-chain verification, environment verification, `pip check`, source registry, Portable Catalog sync, runtime/Skill exact-six, V1 exact-six, Unified contracts, Phase H V3, compileall, py_compile, and `git diff --check`. The external network sentinel recorded zero external socket attempts; provider requests, live acquisition, production user-state mutations, disk-fill tests, and OOM tests were zero.

L4-A7 remains unauthorized. L5-L7 remain unauthorized.
