# M8R-07C Local Service Post-Merge Acceptance

## Decision

`PASS_WITH_CAVEATS`. M8R-07 is `CLOSED`. Current `main` at `60b362b9f665a2bf66445670af7a06400bd47735` independently reproduces the accepted Local-First Unified Market Evidence Service contract without production market calls.

The caveats are carried debt, not closure blockers: CORS still accepts `Origin: null`; the test environment reports one Starlette/httpx deprecation warning; and the repository still contains a pre-M8R-07 legacy `server/mcp_server.py`. No Unified Market Evidence MCP adapter over `/api/unified/*` exists yet, and the legacy MCP surface is not accepted as the M8R-08 architecture.

## Contract and route acceptance

The Local Service contract is `unified_market_evidence_local_service.v1`, and `/api/unified` is its sole transport namespace. Accepted routes are:

- GET `/api/unified/capabilities`
- POST `/api/unified/validate-request`
- POST `/api/unified/preview-request`
- POST `/api/unified/authorizations`
- POST `/api/unified/executions`
- POST `/api/unified/result-package`
- GET `/api/unified/result-package/{control_package_id}/audit.json`
- GET `/api/unified/result-package/{control_package_id}/handoff`

Repository tracing confirms one semantic stack: canonical Request and F3/Mode A → Mode B1 planner → Mode B2 authorization → 05B-03 execute-once and fixed production adapter → receipt/bundle/evidence → Mode C Result/Audit/Markdown → handoff. The Workbench uses the same FastAPI router and services; no alternate unified resolver, planner, authorization model, executor, projector, Audit builder, or Markdown renderer was introduced.

## Capability acceptance

The capability projection reads one snapshot of each established authority in strict order: capability catalog semantics → 05B routing disposition → production executor registration verification. Current governed output is:

| Capability / market | Accepted disposition |
|---|---|
| `current_observation` / TWSE | executable |
| `current_observation` / TPEX | executable |
| `official_eod_reference` / TWSE | executable |
| `official_eod_reference` / TPEX | executable |
| `official_eod_reference` / TAIFEX | provisional, non-executable |
| `recent_performance` | plan-only |
| `session_status` | blocked, not production executable |

Focused tests also prove bounded `409` behavior for missing or malformed catalog/routing authority, missing or schema-invalid production metadata (including normalized `OrchestrationError`), and selected-executor contradictions. Errors do not expose absolute local paths and malformed authority cannot upgrade a capability to executable.

## Handoff acceptance

The handoff calls the existing verified Mode C read-or-materialize path. It returns the unchanged canonical Result and AI-ready Markdown, uses the verified canonical Audit `citation_to_operation_map`, and represents both current-observation and official-EOD citations in the deterministic operator fixture. It does not expose `twse_mis_rich_facts`, parser internals, raw evidence bodies, or absolute paths.

`request_mode` remains the original canonical request field. `execution_outcome` comes from verified receipt `overall_status`; neither is inferred from the other. `additional_market_network_executed:false` describes only the handoff/read operation and makes no claim that an earlier governed execution avoided authorized market network.

## Governance and Local-First boundary

Preview does not create authorization, and authorization does not execute. The server still requires explicit authorization, execution, operator-reference, and network-confirmation fields. The 05B-03 atomic claim remains exclusive and replay is denied. These transport confirmation fields do not cryptographically attest that a human personally supplied them; client-side human-intent enforcement remains an M8R-08 design concern.

The supported launcher defaults to `127.0.0.1` and rejects hosts other than `127.0.0.1`, `localhost`, and `::1`. Startup reports `network_on_startup:false`. No remote unified service, background polling, scheduler, or M8R-08 MCP adapter is present. Existing CORS behavior—localhost/127.0.0.1 origins plus `Origin: null`—is unchanged and remains explicit hardening debt.

## Verification and network accounting

Executed on the post-merge baseline before documentation changes:

- Startup check: PASS; canonical schema, Security Master, and capability catalog loaded; host `127.0.0.1`; network on startup false.
- Focused Local Service/Mode C/operator acceptance: `24 passed, 0 failed, 1 warning` in `76.45s`.
- Relevant Local Service/Mode C/Workbench/API/operator regressions: `101 passed, 0 failed, 1 warning` in `85.48s`.
- `default-ci`: `913 passed, 0 failed, 0 skipped, 1 warning` in `270.78s`, return code `0`; sealed local Security Master candidate executed and passed.
- `compileall server scripts tests`, both Workbench JavaScript syntax checks, and `git diff --check`: PASS.
- External production market-network calls: `0`.

## Carried debt and blockers

Carried unchanged: current-observation failure observability, current-observation reliability, Mode C EOD currentness integration, AI Markdown freshness duplication, CORS `Origin: null`, and the Starlette/httpx test deprecation warning. The legacy MCP surface requires explicit separation from the future unified adapter but does not change the accepted `/api/unified/*` contract.

Blocking findings: none. M8R-07 is closed and M8R-08A may proceed; M8R-08B remains unauthorized.
