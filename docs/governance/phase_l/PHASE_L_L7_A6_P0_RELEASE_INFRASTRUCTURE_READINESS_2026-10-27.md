# Phase L / L7-A6-P0 — Release Infrastructure Readiness

Disposition: `L7_A6_P0_RELEASE_INFRASTRUCTURE_READINESS_CANDIDATE`
Independent review: **PENDING**. This is readiness infrastructure only.

Owner authorities: `USER_CHAT_2026-10-27_L7_A6_P0_RELEASE_INFRASTRUCTURE_READINESS_AUTHORIZATION_1` and `USER_CHAT_2026-10-27_L7_A6_P0_R1_LEGACY_DISABLED_ACCEPTANCE_HARNESS_REALIGNMENT_AUTHORIZATION_1`.

Entry main `ddae25ee4c0539edc7f43073708113795a56e58b`, tree `32b833d8adf101f9e7711b0a8dae769568fcda2f`. P0 implementation `dc8062b7185094697a96d34d86fc063a322c3634`, tree `e2b6dc1596cafc337fb839843156a1171cc55c24`; R1 repair `7baec9fe252be364f0014a1a08b546dcf5c8a3a8`, tree `2f94f190985bf2d0dd975a1aff569969eca52691`.

## Accepted release contract

ProductVersion `1.5.0` is selected and unpublished; published stable is `v1.0.0`. Canonical build Python is CPython 3.13 and MCP remains pinned to `mcp==1.29.0`. A3 dependency authority and its explicit reproducibility, signing/SBOM and hosted-runner boundaries remain accepted. A4 public/state compatibility and EXIT-08/09/10/14/15 remain PASS. A5 bounded-live acceptance and post-merge reconciliation are merged; GAP-15 is CLOSED and EXIT-19 is PASS.

## Findings and bounded repairs

- D1: A6 validation scope was absent; A6 was added while preserving A2/A3/A4 containment.
- D2: canonical CI launcher lacked startup bytecode suppression; it now starts the deterministic runner with `-B`.
- D3: release readiness treated historical diagnostics and browser as unconditional blockers; canonical release-blocking CI is blocking, default/full remain truthful diagnostics, browser is conditional, and output roots must be fresh.
- D4: typed release manifest and final artifact/path hygiene remain **A6-R1 work**. The existing V1 manifest smoke does not close GAP-16.
- D5: M6E/M6G expected obsolete 400/200 behavior on the disabled legacy route. R1 checks the current 410 `legacy_live_observation_execution_disabled` contract and zero historical executor calls. Product route/runtime was not changed. M6E Mode A failure was derivative of its stale FastAPI check. M6G historical live fallback is not a current L7 live authority and was not executed.

P0 implementation files: `scripts/accept_l7_a2_docker.py`, `scripts/run_l7_a2_release_validation.py`, `scripts/run_test_profile.py`, `scripts/run_v1_release_readiness.py`, `tests/unit/test_l7_a6_p0_release_infrastructure.py`. R1 files: `scripts/run_m6e_operator_acceptance.py`, `scripts/run_m6g_browser_operator_e2e.py`, `tests/test_m6e_operator_acceptance.py`, `tests/test_m6g_browser_operator_e2e.py`, `tests/unit/test_l7_a6_p0_release_infrastructure.py`. No A1 selection configuration changed.

## Validation and retained limits

Initial readiness replay was blocked at operator preflight; its original report and M6E evidence remain immutable and are bound by hash in `initial_readiness_blocker.json`. R1 focused tests: **93 passed, 0 failed, 1 browser-marker deselected**; no browser was executed. Canonical CI on R1: **1895 passed, 0 failed, 4 contracted skips, 20 deselected, 386 guard events, 0 denials**; member ledger equals the initial P0 run. Portable validator: **205 passed, 0 failed**; compileall and diff check passed.

Fresh readiness replay: **PASS**. Operator preflight passed; M6E is `pass_with_caveats`, FastAPI and Mode A are `pass`. Existing V1 manifest generation, JavaScript syntax and source archive smoke passed. Browser E2E: `NOT_REQUESTED_BY_RELEASE_PLAN`. Diagnostic `default-ci` remains **FAIL** (12 historical/governance assertions); `full-non-network` remains **FAIL** on Windows collection due to missing Unix `fcntl`. Diagnostics are not canonical blocking gates.

The prior P0 read-only GitHub snapshot recorded main `ddae25ee4c0539edc7f43073708113795a56e58b`, protection disabled, no rulesets, no required checks and no v1.5.0 release. No GitHub setting was changed. R1 did not refresh that snapshot. Release Validation remains manual; Windows Compatibility Smoke is manual or opt-in label.

No market acquisition, live browser, final native/Docker artifact build, source freeze, final SBOM, publication, tag, push or PR occurred. Source archive and V1 manifest are readiness smokes only. Python guard coverage is not an OS firewall claim.

## Remaining A6 work

`L7-GAP-16`, `L7-GAP-17`, `L7-GAP-18` remain **OPEN**. `L7-EXIT-16/20/21/22/23/24` remain **NOT_YET_PASS**. A6 acceptance is not complete; source and artifacts are not frozen. A7, stable publication and Phase M are not authorized; Phase L is not closed. A6-R1 must decide typed publication manifest and artifact/path hygiene, followed by the remaining authorized release work.

Evidence: [l7-a6-p0-release-infrastructure-readiness-20261027T032514Z](acceptance_runs/l7-a6-p0-release-infrastructure-readiness-20261027T032514Z/manifest.json); members 25, mismatches 0, self-digest `6abd16204cb856b86b1fbdc33c9ed7edfd4213365993f7b04546d6b30bf34f04`. External run artifacts are referenced by absolute path, byte count and SHA-256 in that evidence.
