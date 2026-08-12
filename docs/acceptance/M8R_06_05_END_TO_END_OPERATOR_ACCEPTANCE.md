# M8R-06-05 End-to-End Operator Acceptance

## Decision

`PASS_WITH_CAVEATS`

- baseline_sha: `411402dc958de6f01d2abe8c5ede53f94bb44825`
- implementation_code_head: `b07d6d17a7f9260c701a5ba283210bc817edf1f2`
- external_market_network_calls: `0`
- browser_e2e: `NOT_RUN` (no browser dependency was installed or required)

The accepted Workbench chain was exercised through the supported localhost launcher with the fixed child subprocess and deterministic test transport. No canonical Request, Result, planner, executor route, or service layer was added.

## Acceptance matrix

| Scenario | Result | Evidence |
| --- | --- | --- |
| TWSE + TPEX happy path | PASS | Four approved operations (current observation and official EOD for each market), one authorization, one claim, one receipt, one bundle, and one Mode C package. |
| Partial coverage and source failure | PASS | Deterministic official-EOD empty response produces `partial_success` and Mode C `partially_failed`; the failed evidence remains failed/missing. |
| Plan-only | PASS | `recent_performance` appears as `plan_only_not_executable` beside executable current observation and never enters executable scope. |
| Blocked capability | PASS | Required `session_status` previews as `unsupported_capability`; authorization is rejected before claim/dispatch. |
| Identity ambiguity | PASS | Repository-owned deterministic F3 collision fixture yields `requires_clarification` / `ambiguous`; the sealed production candidate deliberately has no collision, so no production identity was guessed. |
| Authorization refusal | PASS | Missing explicit confirmation returns `authorization_confirmation_required`; stale preview identity returns `mode_b2_preview_stale`. |
| Network confirmation refusal | PASS | `confirm_network_execution=false` is rejected before a claim or source marker; authorization remains usable for the subsequent confirmed execution. |
| Replay rejection | PASS | Second execution is rejected and invocation count remains unchanged. |
| Currentness caveat | PASS | Deterministic `current_observation` evidence carries `current_observation_not_guaranteed_realtime` into canonical Result and authoritative Markdown. |
| Stale UI state and AI handoff | PASS | Static state-machine assertions cover edit/import/clear invalidation and authoritative Markdown, canonical Result, and separate Audit download bindings. |

## Localhost vertical lineage

`GET /workbench/mode-a/` → `POST validate-request` → `POST preview-request` → `POST authorizations` → `POST executions` → `POST result-package` → `GET audit.json` all succeeded.

The acceptance test cross-checks request hash → plan/preview → authorization → claim → receipt → bundle → Result/Audit identifiers. The deterministic transport reported `external_market_network_executed=false` and created only process-local invocation markers.

## Test closure

- Focused M8R-06-05 suite: `2 passed in 47.18s`.
- Focused Mode A/B1/B2/Mode C/05C/Workbench regressions: `93 passed, 1 warning in 111.93s`.
- Sealed local Security Master candidate: `2 passed, 1 warning in 46.99s`; executed, not skipped.
- Default CI: `902 passed`, `0 failed`, `0 deselected`, return code `0`, duration `295.672s`.
- `python -m compileall scripts server tests`: PASS.
- `node --check frontend/unified-workbench/unified-workbench.js`: PASS.
- `git diff --check`: PASS.

The only warnings were the pre-existing FastAPI/Starlette TestClient deprecation warning. The optional historical package `umea-v1-b723c9ae498a6a7fab68` was present and verified read-only as `existing_verified` with an AI-ready Markdown handoff; no source execution occurred.

## Caveat

`current_observation` remains bounded current/live-ish evidence, not a guaranteed real-time feed. M8R-07 and M8R-08 remain unauthorized and untouched.
