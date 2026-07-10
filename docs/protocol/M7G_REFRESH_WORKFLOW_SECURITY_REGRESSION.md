# M7G Refresh Workflow Security Regression

Status: `refresh_workflow_security_regression_defined`

## Purpose

- Harden M7G-09 controlled manual refresh execution with regression tests.
- Prove execution remains explicit, bounded, fail-closed, non-canonical, safe-artifact-only.
- Prove returned artifacts cannot render or reach AI handoff unless validated.
- Prove runner failures and raw-forbidden injection fail closed.
- Preserve Mode A/B/C and Level 1/2 semantics.

## Regression targets

- missing request package
- wrong package_status
- missing execution confirmation
- wrong execution confirmation
- execution_authorized=true in request package
- execution_performed=true in request package
- raw_payload_requested=true
- raw_forbidden_values_requested=true
- ai_model_call_requested=true
- trading_advice_requested=true
- unsupported source family
- mixed supported and unsupported source families
- runner exception
- runner result contains raw forbidden keys
- safe artifact validator rejection
- frontend cannot auto-load returned artifact
- frontend cannot render rejected execution result
- frontend cannot handoff rejected artifact
- successful execution still requires explicit Load refreshed safe artifact

## Boundary

- M7G-10 adds no new execution source family.
- No auto refresh.
- No scheduler.
- No polling.
- No hidden fetch.
- No startup fetch.
- No AI/model call.
- No DB write.
- No raw payload exposure.
- No trading advice.

## Fail-closed expectations

Runner exceptions and network failures return a structured safe execution result with no `safe_context_artifact`, no raw exception stack trace, no raw payload fields, and `safe_artifact_returned = false`.
Rejected execution results and rejected safe artifacts are not renderable, not handoff eligible, and cannot update Mode C until an operator explicitly clicks **Load refreshed safe artifact** after validation acceptance.
