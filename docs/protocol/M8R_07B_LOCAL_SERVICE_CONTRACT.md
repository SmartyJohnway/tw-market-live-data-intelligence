# M8R-07B Local-First Unified Market Evidence Service Contract

## Purpose and boundary

`/api/unified/*` is the Local-First Unified Market Evidence Service transport, version `unified_market_evidence_local_service.v1`. It is localhost-only through the existing launcher and preserves one runtime: Request → F3 → B1 → B2 authorization → execute-once → evidence/receipt/bundle → Mode C → canonical Result, Audit, and Markdown. This contract adds no remote access, MCP server, scheduler, background work, or alternate source/runtime path.

The existing routes remain authoritative: POST `validate-request`, `preview-request`, `authorizations`, `executions`, and `result-package`; GET `result-package/{control_package_id}/audit.json`. They map respectively to validation, preview, authorization, execution, verified read-or-materialize Result, and Audit read. Existing request and response shapes are unchanged.

## Conceptual operations and autonomy

| Operation | Transport | Classification |
|---|---|---|
| `describe_capabilities` | GET `/api/unified/capabilities` | autonomous-safe; no market network or writes |
| `validate_request` | existing POST validation route | autonomous-safe; no market network or writes |
| `preview_request` | existing POST preview route | autonomous-safe; no market network or writes |
| `authorize_request` | existing POST authorization route | explicit-approval boundary |
| `execute_request` | existing POST execution route | explicit-execution boundary |
| `read_result` | existing POST result-package route | safe only for finalized governed artifacts; may materialize deterministic local outputs |
| `export_ai_handoff` | GET `/api/unified/result-package/{control_package_id}/handoff` | safe only for finalized governed artifacts; no new market request |

The server enforces explicit confirmation fields. It cannot cryptographically prove a human personally supplied them; a future client or MCP adapter is responsible for obtaining genuine human approval before calling authorization or execution.

Authorization is never inferred from validation or preview. Execution keeps the existing control-package scope, `confirm_execution`, operator confirmation reference, network confirmation where needed, fixed runtime adapter, atomic single-use claim, and replay denial.

## Capability description

`GET /api/unified/capabilities` has no request body. It returns `409` with a bounded error and trace ID if an authority is unavailable, malformed, or a selected resolved executor cannot be verified. It never returns local absolute paths.

The deterministic response contains `service_contract_version`, catalog/routing schema versions, and sorted catalog-order `capabilities`. Every capability includes semantic support, target and parameter rules, approval/network/batching policy, caveats, blocking reasons, selected executor, and market entries. Each market entry has `market`, `disposition` (`executable`, `plan_only`, `blocked`, or `provisional`), and `production_executor_available`.

It reuses exactly three authorities, in precedence order: capability catalog semantic universe; 05B routing-matrix disposition; then registered production-executor verification. Metadata absence is never interpreted as plan-only. This retains `current_observation` and `official_eod_reference` as executable for TWSE/TPEX, `recent_performance` as plan-only, `session_status` as blocked, and catalog-provisional TAIFEX behavior as provisional/non-executable.

## Verified AI handoff

`GET /api/unified/result-package/{control_package_id}/handoff` invokes the existing Mode C verified read-or-materialize behavior for a finalized package. It returns `409` with existing bounded Mode C errors for invalid, unfinalized, or tampered lineage. It does not execute sources, create/consume authorization, modify canonical Result/Audit/Markdown semantics, or expose raw evidence, rich facts, parser internals, or absolute paths.

The stable response contains: service version, control package/result IDs and hash, result status, canonical `request_id`, `request_mode`, verified receipt-derived `execution_outcome`, `additional_market_network_executed:false`, canonical Result, existing AI-ready Markdown, complete Audit-derived citation references, Result/Audit references, and materialization status. The network field describes this handoff/read only; it does not reinterpret whether the prior governed execution used authorized market network. `request_mode` is the original request field; `execution_outcome` is the verified receipt `overall_status`, never inferred from Result status.

Citation references are complete for materialized evidence represented by the governed package and are deterministically sorted. Each item contains only `citation_id`, `canonical_target_id`, `capability_id`, `executor_id`, `artifact_relative_path`, and `artifact_hash`; authority is the verified Audit `citation_to_operation_map`, not Markdown display text.

## Failure, security, and future adapter rules

All body-bearing legacy routes retain their 1 MiB limit and malformed/privileged-envelope handling. Existing filesystem containment and server-owned control IDs continue to govern artifacts. CORS and its `Origin: null` hardening debt are unchanged; this contract does not broaden binding, authentication, or remote reachability.

A future MCP adapter may only validate/translate tool transport, call this Local Service, and translate the result. It must not own market logic, an alternate planner, authorization, execution, source adapter, projector, or Markdown renderer.

Non-goals: MCP implementation, remote access, new artifact schemas, source retries/polling, changed canonical Result/Audit/Markdown, and any change to Phase D semantics.
