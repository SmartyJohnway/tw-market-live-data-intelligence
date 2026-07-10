# M7G Final Acceptance Report: Local Safe Context Artifact Load & Operator Refresh Workflow

- **Status**: `final_acceptance_pass_with_caveats`
- **Milestone Identifier**: M7G-11
- **HEAD Commit**: 93b96216e9dfd73297c2502b8e91f18210f509e6

---

## 1. Purpose

The purpose of M7G-11 is to close the milestone for local safe context artifact loading and the operator-controlled manual refresh workflow. This document records validation evidence ensuring that the controlled manual refresh gate is operator-explicit, bounded to an active watchlist, safe-artifact-only, and non-canonical.

## 2. Upstream Dependencies & Compatibility

The following upstream developments and regressions have been verified and accepted:
- **PR #117 / M7G-09**: Controlled manual refresh execution gate.
- **PR #118 / M7G-10**: Refresh workflow security regression & TWSE_MIS market route semantics.
- **WIN-COMPAT-01**: Cross-platform Path separator compatibility fix (implemented in `test_inventory_final_closure` via `.as_posix()`).

## 3. Evidence Summary

### Core Clean Baseline & CI Verification
- **Clean-main Alignment**: Passed. Active workspace is fully aligned to the PR #118 merge commit `93b96216`.
- **M7G Focused Tests**: All 25 M7G unit and integration tests passed.
- **Compile & Diff Checks**: `compileall` successfully compiled all python files without errors. `git diff --check` reported no format or trailing whitespace violations.
- **Empty Request Endpoint Smoke**:
  - Sending an empty POST request package to `/api/m7g/controlled-refresh/execute` returns HTTP 200.
  - The execution status is correctly set to `rejected_invalid_request_package`.
  - No python traceback is exposed.
  - No raw payload or depth values are leaked.

### Phase 2 Bounded Live Smoke Evidence
- **2330 / TWSE Listed Route**:
  - Automatically mapped to source route: `TWSE_MIS` with `ex_ch` format `tse_2330.tw`.
  - Successfully observed and converted into accepted safe artifact format.
- **8069 / TPEx-OTC Route**:
  - Automatically mapped to source route: `TWSE_MIS` with `ex_ch` format `otc_8069.tw` (not using TPEX_MIS or rotc_).
  - Successfully observed and converted into accepted safe artifact format.
- **Controlled Refresh Executor Output**:
  - `execution_status`: `executed_safe_artifact_ready`
  - `safe_artifact_returned`: `true`
  - `safe_artifact_validation_status`: `accepted`
  - `network_fetch_performed`: `true`
  - `raw_payload_exposed`: `false`
  - `raw_forbidden_values_returned`: `false`
  - `trading_advice_generated`: `false`
  - `ai_model_call_performed`: `false`

### User Manual UI Acceptance Evidence
Verified in the local browser at `http://127.0.0.1:8080/index.html`:
- **UI Elements Visibility**:
  - Rich Fact Browser is visible.
  - Controlled Refresh Request Package is visible.
  - Controlled Manual Refresh Execution panel is visible.
  - Refresh execution result block is visible.
  - Load refreshed safe artifact button is visible.
  - No `TPEX_MIS` or `rotc_` routes are present.
- **No Hidden Behavior**:
  - Initial page load does not trigger any POST requests.
  - No repeated polling, WebSockets, EventSource, or background AI model calls.
- **Prepare Package Gate**:
  - Build request package with `TWSE_MIS` using confirmation phrase `PREPARE_REFRESH_REQUEST_ONLY`.
  - Under `static_demo` mode, execution eligibility is safely evaluated as `false` and blocked with status `execution_eligible_for_m7g09_invalid`.
- **Execute Gate**:
  - Load valid safe context artifact to switch the active context to `loaded_safe_artifact`.
  - Build package and execute refresh with phrase `EXECUTE_CONTROLLED_REFRESH_ONCE`.
  - Exactly one POST request to `/api/m7g/controlled-refresh/execute` is sent.
  - Response is HTTP 200, containing no python traceback.
  - Raw payload, bid/ask ladders, and source investigation notes are correctly hidden. No trading advice is generated.
- **Load Gate**:
  - The refresh execution does not auto-update the Rich Fact Browser or AI handoff state.
  - Clicking `Load refreshed safe artifact` manually updates the Rich Fact Browser, Source health panel, and updates the AI Handoff source mode to `loaded_safe_artifact`.

---

## 4. Source Semantics & Taxonomy Final Accepted

The finalized data sources and runtime route mapping for M7G are:
- **TWSE Listed (Live)**: `TWSE_MIS` / `tse_{symbol}.tw`
- **TPEx/OTC (Live)**: `TWSE_MIS` / `otc_{symbol}.tw`
- **Futures (Live)**: `TAIFEX_MIS` (declared but not executable in M7G)
- **TWSE Reference/EOD**: `TWSE_OPENAPI` (reference only)
- **TPEx Reference/EOD**: `TPEX_OPENAPI` (reference only)
- **TAIFEX Reference/EOD**: `TAIFEX_OPENAPI` (reference only)
- **TPEX_MIS**: Absent / Not introduced.
- **rotc_ / Emerging Stocks**: Absent / Not introduced.

## 5. Hard Boundaries

The runtime and safety boundaries are strictly enforced:
- **Mode A/B/C and Level 1/2**: Unchanged. No new Mode D or Level 3 introduced.
- **M5F/Level 1 Artifacts**: Left unmutated.
- **No Automation**: No auto-refresh, scheduler, polling, startup fetch, or hidden fetches.
- **No Forbidden Content**: No AI/model calls, no database writes, no raw payload exposure, and no trading advice/recommendations/signals.

## 6. Caveats

- **Windows default-ci Environment**: Requires `$env:PYTHONUTF8="1"` and `$env:PYTHONIOENCODING="utf-8"` due to standard Windows CP950 decoding limitations, unless explicit UTF-8 encoding parameters are added to all project file-read methods.
- **Frontend Serving**: The frontend UI is designed to be opened from `frontend/public/index.html` via the local static server; the FastAPI root serves JSON status indicators rather than rendering the frontend assets.
- **Watchlist Coverage**: Manual UI acceptance directly verified the `2330` TWSE route; the `8069` OTC route was verified using the controlled API package executor. Future milestones may expand the static watchlist demo to include upper-bound OTC coverage.

---

## 7. Recommended Next Track

- **Task**: `M7H-SOURCE-FAMILY-ROUTE-GOVERNANCE-AND-CONTROLLED-EXPANSION`
- **Initial Candidates**:
  - Incorporate a richer loaded safe artifact fixture containing both 2330 and 8069.
  - Implement TAIFEX_MIS controlled manual execution behind a separately scoped future gate.
  - Hardening of overall source-family route governance.
