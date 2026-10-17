# Phase L L3-A6 PRE2-R1 — Reservation Creator Launch Contract Repair

## Authority and boundary

This is an offline-only deterministic startup repair on the existing A6
candidate branch. Entry HEAD was
`c8261ddc7cab12de6b465a55f3156efc64d4dd6c`, tree
`d52a262e17c86f49eb9efeae09dba83c22633204`; canonical `origin/main` was
`7b3e73b2f3e2c2bec167b6d66f1846846fe4ec4c`.

No live reservation was created, the one-shot A6 authority remains unconsumed,
and no provider request was made.

## Chronology and finding

- PRE2 passed offline orchestration, dispatch accounting, and reservation
  semantics review at its candidate state. Its retained evidence remains
  immutable under `acceptance_runs/l3-a6-pre2-20261017T021753Z/` with canonical
  manifest SHA-256
  `74de7917887f180c2f5c1b083c693bbc4c3b57da37c88a1feca0968020fd3ca6`.
- The later final pre-live command attempted to invoke the reservation creator
  directly. It stopped before reservation creation because Python could not
  import `scripts.phase_l_a6_live_dispatch_guard`; the creator had not added the
  repository root to `sys.path`.
- The failed pre-live event is retained in
  `acceptance_runs/l3-a6-pre2-r1-20261017T023918Z/launch_failure_record.json`.
  Reservation creation did not start, no reservation or consumed receipt was
  written, the live runner did not start, and provider requests were zero.
- PRE2-R1 adds the same repository-root bootstrap used by the reviewed live
  runner before importing the dispatch guard. It changes no reservation
  binding or creation semantics.

## Launch verification

Subprocess smoke tests require normal argparse help from all four paths:

1. reservation creator direct script from repository root;
2. reservation creator direct script by absolute path from an external working
   directory with `PYTHONPATH` removed;
3. reservation creator module invocation from repository root;
4. live runner direct script by absolute path from an external working
   directory.

All passed. These tests invoke only `--help`; no reservation creator write path
or live runner execution path is invoked.

## Verification

- PRE1-R2 guard and PRE2 focused tests: **79 passed**.
- Normalized integrated offline gate: **594 passed, 1 deselected, 0 failed**.
  The sole deselection is the previously governed
  `test_lifecycle_drift_failure_report_preserves_code_without_retry_authority`;
  it is not represented as passing.
- External socket attempts: **0**.
- Source registry, Portable Catalog sync, runtime/Skill exact-six, V1
  contracts exact-six, Phase H V3, compileall, reservation creator py_compile,
  and `git diff --check`: **PASS**.
- No production runtime, dispatch guard, live runner, resolver, source
  contract, Catalog, Route, activation, or persistent user state changed.

PRE2-R1 disposition: `PASS_LAUNCH_CONTRACT_REPAIRED_READY_FOR_FINAL_LIVE_REVIEW`.
This is a technical candidate result, not live execution, Owner acceptance, or
L3 closure.
