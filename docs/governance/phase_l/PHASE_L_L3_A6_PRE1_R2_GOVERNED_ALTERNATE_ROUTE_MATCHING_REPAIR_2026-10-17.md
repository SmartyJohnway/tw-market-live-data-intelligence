# Phase L L3-A6 PRE1-R2 — Governed Alternate Route Matching Repair

## Authority and scope

This offline-only repair follows the PRE2 offline E2E finding on the reviewed
PRE1-R1 candidate. PRE1-R1 remains historically accepted as
`PASS_READY_FOR_FINAL_LIVE_RESERVATION` at its reviewed contract state and is
superseded for live-readiness by the deterministic guard defect recorded here.
Its commit and evidence are unchanged.

The defect was that `_match_request()` checked the planned primary hostname
before deciding whether the request URL exactly matched the source's governed
alternate route. Consequently, valid cross-host alternates for P04-P07 were
rejected before dispatch. The repair resolves route role first, derives the
expected host from the exact primary or alternate route, and then validates the
hostname. Alternate matching requires exact URL equality. Ordinary primary
routes remain exact; P01 and P12 retain their existing path/query bindings.
`reserve_before_dispatch()` continues to independently verify the alternate
host and route.

The A6 orchestrator also blocks a research JSON alternate after primary HTTP
429, so rate limiting cannot be evaded by switching hosts. It preserves a
degraded primary outcome when an alternate succeeds, and preserves a
deterministic CSV contract-drift observation across alternate recovery. No
Phase G production fallback code was changed.

## Verification

- All four P04-P07 primary/alternate host pairs were exercised.
- Negative tests reject wrong hosts, non-exact URLs, borrowed routes,
  alternate-before-primary, and per-source overflow.
- Offline orchestrator tests cover 27 physical dispatches, degraded primary
  history, 429 suppression without alternate dispatch, and contract-drift
  preservation.
- Focused guard/orchestrator tests: 59 passed.
- Normalized combined source/offline gate: 595 passed, 1 deselected, 0 failed.
  The only deselection is the prior-governed
  `test_lifecycle_drift_failure_report_preserves_code_without_retry_authority`.
  It is not represented as passing.
- Source registry, Portable Catalog sync, runtime/Skill sync (six MCP tools),
  V1 public contracts (six tools), and Phase H V3 validators passed.
- `compileall` and `git diff --check` passed. External socket attempts: 0.
- A separate unscoped `default-ci` exploration was not the frozen PRE1 gate and
  did not pass on this Windows environment (including missing local Security
  Master state and platform-dependent legacy tests); it is not used as
  acceptance evidence and no new deselection was added to the PRE1 gate.

No production source runtime, source registry, Catalog, Route, or activation
state was changed. No provider request was made, no live reservation was
created, and A6 live authority remains unconsumed.

PRE1-R2 disposition: `PASS_GUARD_REPAIRED_FOR_PRE2_RESUME`.
This is an offline technical checkpoint, not live authorization or Owner
acceptance.
