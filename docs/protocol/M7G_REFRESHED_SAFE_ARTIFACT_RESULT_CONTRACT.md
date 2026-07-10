# M7G Refreshed Safe Artifact Result Contract

Status: refreshed_safe_artifact_result_contract_defined

## Execution result schema

- m7g_controlled_refresh_execution_result.v1

## Safe artifact schema

- m7g_safe_context_artifact.v1

## Required result states

- executed_safe_artifact_ready
- rejected_invalid_request_package
- rejected_missing_execution_confirmation
- rejected_unsupported_source_family
- execution_failed_no_safe_artifact
- execution_failed_safe_artifact_rejected

## Returned artifact

- Level 2 only.
- Level 2 temporary safe artifact.
- safe_for_frontend = true
- safe_for_ai_handoff = true
- raw_payload_exposed = false
- raw_rich_facts_exposed = false
- raw_full_ladder_exposed = false
- raw_forbidden_values_present = false
- Mode A/B/C unchanged.
- Level 1/2 unchanged.
- does not mutate M5F.
- does not create Mode D or Level 3.

## Frontend

- Returned artifact must pass frontend validator before render.
- Rejected artifact must not reach Rich Fact Browser.
- Rejected artifact must not reach AI handoff.
- Operator must explicitly click Load refreshed safe artifact.
- EXECUTE_CONTROLLED_REFRESH_ONCE is required for execution.
- TWSE_MIS execution supported.
- Level 1 / official reference / canonical-adjacent / EOD source families: TWSE_OPENAPI, TPEX_OPENAPI, TAIFEX_OPENAPI.
- Level 2 / bounded live observation / temporary context source families: TWSE_MIS, TAIFEX_MIS.
- TAIFEX_MIS, TWSE_OPENAPI, TPEX_OPENAPI, and TAIFEX_OPENAPI declared but not executable in M7G-09.
- Mixed supported plus unsupported/not-yet-executable source-family requests fail closed with no partial execution.
- No auto refresh.
- No scheduler.
- No polling.
- No hidden fetch.
- No raw payload exposure.
- No AI/model call.
- No trading advice.
