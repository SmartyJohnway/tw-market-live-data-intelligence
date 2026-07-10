# M7G-07 Operator Refresh Workflow Policy and Preflight

Status: `operator_refresh_workflow_policy_preflight_defined`

## Purpose

- Define the operator-controlled manual refresh workflow.
- Define preflight checks before any refresh request can be prepared.
- Preserve local-first, bounded-watchlist, operator-controlled semantics.
- Prepare for mandatory downstream M7G-09 controlled manual refresh execution.

## Policy

- M7G-07/08 does not execute refresh.
- M7G-07/08 does not fetch live data.
- M7G-07/08 does not call backend/API/MCP.
- M7G-07/08 does not perform network operations.
- M7G-07/08 does not call AI/model.
- M7G-07/08 creates a safe request package only.

## Preflight

- Active context must be explicit.
- Active context can be `static_demo` or `loaded_safe_artifact`.
- If `static_demo` is active, refresh request package is preview-only and not execution-eligible.
- If `loaded_safe_artifact` is active and validation is accepted, request package may be execution-eligible for future M7G-09, but not executable in M7G-07/08.
- Requested symbols must be bounded to active context observations or explicit operator selection from the active context.
- Source families must be declared.
- Refresh scope must be `bounded_watchlist`.
- Raw payload request must be false.
- Raw forbidden values request must be false.
- Trading advice request must be false.
- AI/model call request must be false.
- Operator confirmation is required.

## Operator confirmation phrase

- `PREPARE_REFRESH_REQUEST_ONLY`

## Downstream

- M7G-09 controlled manual refresh execution remains mandatory.
- M7G-09 is the earliest task allowed to execute refresh.
