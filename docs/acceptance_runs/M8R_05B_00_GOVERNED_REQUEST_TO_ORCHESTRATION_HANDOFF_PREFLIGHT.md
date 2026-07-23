# M8R-05B-00 governed request-to-orchestration handoff preflight acceptance

## Decision

**GO_TO_M8R_05B_01_WITH_CAVEATS.** This preflight defines only the deterministic, offline planning handoff. It does not implement a planner, authorise execution, retrieve market data, or make the unified orchestrator runtime-ready.

## Verified boundary

The handoff contract preserves F3's uncomputed operation-count boundary and makes no operation status authorising. It binds the original request, normalized request, F3 validation result, evidence artifacts, catalog, routing matrix, contract, and planner version. Canonical plan identity includes machine-readable warning and optional-omission semantics; plan IDs derive from the same digest as plan hashes.

The policy is required-fail-closed with optional omission warnings. Provisional and contract-supported/non-runtime routes remain plan-only. `session_status` remains blocked because supplied-evidence local calculators do not establish a complete governed current closure-evidence route. Only `current_observation` and `official_eod_reference` have selected adapter-required candidates.

## Verification

- Four design JSON artifacts parsed successfully.
- Focused M8R-05B checks: **5 passed, 0 failed** in 0.22 seconds.
- Upstream F3 regressions: **39 passed, 0 failed** in 1.26 seconds.
- Full non-network profile: **1872 passed, 7 failed, 1 skipped, 1 deselected** in 175.392 seconds. The failure set exactly matches the established seven M5D/M5E nodes; novel failures are empty.
- The profile made no network execution (`network_may_have_occurred=false`). Its generated runtime changes were explicitly restored/removed; no runtime-observation artifacts remain in the final diff.

## Next task

`M8R-05B-01-DETERMINISTIC-ORCHESTRATION-PLAN-PROJECTION` remains pending owner acceptance. Its scope is offline, pure, deterministic, non-authorizing, non-network, and non-executing.
