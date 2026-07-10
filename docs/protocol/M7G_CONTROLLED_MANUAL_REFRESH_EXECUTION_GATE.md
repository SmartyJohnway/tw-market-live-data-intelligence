# M7G Controlled Manual Refresh Execution Gate

Status: controlled_manual_refresh_execution_gate_defined

## Purpose

- Execute exactly one operator-controlled bounded refresh from a valid M7G refresh request package.
- Produce a refreshed Level 2 safe context artifact.
- Load the safe artifact into existing M7G active context only after validation.
- Preserve Mode A/B/C unchanged and Level 1/2 unchanged semantics.

## Architecture

- Mode A/B/C unchanged.
- Level 1/2 unchanged.
- M7G-09 is Mode B controlled execution.
- M7G-09 feeds the resulting refreshed Level 2 safe artifact into the existing M7G active-context and Mode C handoff surface.
- Output is Level 2 temporary safe artifact.
- M7G-09 does not mutate M5F.
- M7G-09 does not promote Level 2 to Level 1.
- M7G-09 does not create Mode D or Level 3.

## Execution

- Requires prepared request package.
- Requires PREPARE_REFRESH_REQUEST_ONLY package confirmation already matched.
- Requires EXECUTE_CONTROLLED_REFRESH_ONCE execution confirmation.
- Executes once only.
- Runtime network fetch is allowed only inside the controlled execution gate.
- No auto refresh.
- No scheduler.
- No polling.
- No hidden fetch.

## Supported source families

Declared source-family taxonomy:

- Level 1 / official reference / canonical-adjacent / EOD: TWSE_OPENAPI, TPEX_OPENAPI, TAIFEX_OPENAPI.
- Level 2 / bounded live observation / temporary context: TWSE_MIS, TAIFEX_MIS.
- TWSE_MIS execution supported in M7G-09.
- TAIFEX_MIS, TWSE_OPENAPI, TPEX_OPENAPI, and TAIFEX_OPENAPI are declared but not executable in M7G-09 unless explicitly implemented and tested later.
- Unsupported or not-yet-executable source families fail closed.
- Mixed supported plus unsupported/not-yet-executable source-family requests fail closed; M7G-09 does not partially execute mixed requests.

## Safety

- No raw payload exposure.
- No raw forbidden values returned.
- No AI/model call.
- No DB write.
- No trading advice.
- No recommendation.
- No trading signal.
