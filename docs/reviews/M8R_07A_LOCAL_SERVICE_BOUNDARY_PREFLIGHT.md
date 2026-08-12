# M8R-07A — Local-First Unified Market Evidence Service Preflight

## Decision

`PASS_WITH_CAVEATS`. The accepted M8R-06 server runtime is already the sole semantic stack. M8R-07B can expose a stable local-service contract as a thin client-neutral facade without changing canonical request, planning, authorization, execution, Result, Audit, or AI-projection semantics.

## Baseline and accepted upstream state

- Expected and actual `main`: `bdf1b76cf860e2a390b22c0874b297d07298799d` (PR #193 merge).
- Phase D / M8R-06: `PASS_WITH_CAVEATS`; accepted post-merge human production E2E remains upstream evidence, including TWSE/TPEX current observation and official EOD, plan-only preservation, controlled Standard/Top-5 context, file-only rich facts, Result/Audit integrity, and AI-ready Markdown.
- This preflight made no market request and does not reopen Phase D source or projection decisions.

## Authoritative stack and current service inventory

The one permitted stack is: Unified Request → `validate_mode_a_request()` (F3) → `build_mode_b1_preview()` → `build_mode_b2_authorization()` → `execute_mode_b2_once()` / fixed 05B-03 child and production registry → `build_mode_c_result_package()` → canonical Result, Audit, and Markdown. `unified_workbench_router.py` is transport only; the browser is a client, not an authority.

| Route | Method / envelope | Authority invoked | Network / writes | Confirmation / replay | Response / artifact | Classification |
|---|---|---|---|---|---|---|
| `/api/unified/validate-request` | POST `{request}` | Mode A / F3 | no market network; no write | none | canonical validation | `CANONICAL_REUSABLE` |
| `/api/unified/preview-request` | POST `{request}` | Mode B1 | no market network; no write | none | Preview + orchestration plan | `CANONICAL_REUSABLE` |
| `/api/unified/authorizations` | POST request + matching preview/plan IDs + `confirm_authorization:true` | Mode B2 | no market network; writes server-selected control package | explicit approval; pre-execution only | authorization, binding, preflight, control package | `CANONICAL_REUSABLE` |
| `/api/unified/executions` | POST control ID + explicit execution/network confirmations | Mode B2 execute-once | approved source calls possible; receipt/bundle/evidence writes | explicit operator ref; atomic single-use claim; replay denied | receipt/bundle execution summary | `CANONICAL_REUSABLE` |
| `/api/unified/result-package` | POST `{control_package_id}` | Mode C | no new market network; may materialize/verify Result, Audit, Markdown | finalized governed package; deterministic reread | canonical Result, Markdown, citations, Audit reference | `THIN_TRANSPORT_WRAPPER` |
| `/api/unified/result-package/{id}/audit.json` | GET path ID | verified Mode C audit reader | no market network; no write except first materialization | finalized package required | canonical Audit | `THIN_TRANSPORT_WRAPPER` |
| Workbench HTML / frontend state | GET/static/browser JS | browser presentation only | no market network by itself | button state only | UI | `WORKBENCH_SPECIFIC` |

Every unified route limits bodies to 1 MiB and rejects malformed/privileged transport inputs. `control_package_id` is validated as a constrained server-owned identifier and Mode C re-verifies hashes, final claim, receipt, bundle, F3 reconstruction, and output equality. `safe_destination`/contained roots protect server-selected artifact writes; client payloads cannot choose paths, commands, adapters, URLs, or executables.

## Seven conceptual service operations

| Operation | Current implementation | Classification | Network / side effect | Recommended M8R-07B contract |
|---|---|---|---|---|
| `describe_capabilities` | committed capability catalog + `load_production_executor_metadata()` | `THIN_FACADE` | no / none | deterministic safe projection of markets, capabilities, executable vs plan-only disposition, approval/network requirements, executor availability, and caveats; `EXISTING_CAPABILITY_AUTHORITY_REUSABLE` |
| `validate_request` | POST validate → `validate_mode_a_request()` | `REUSE_AS_IS` | no / none | preserve `{request}` envelope and F3 response |
| `preview_request` | POST preview → `build_mode_b1_preview()` | `REUSE_AS_IS` | no / none | preserve offline preview, deterministic planning, plan-only records and estimates |
| `authorize_request` | POST authorizations → `build_mode_b2_authorization()` | `REUSE_AS_IS` | no market network / control package write | require explicit `confirm_authorization:true`, matching preview/plan identity, and current scope rules; preview never authorizes |
| `execute_request` | POST executions → `execute_mode_b2_once()` | `REUSE_AS_IS` | approved market network possible / governed execution writes | require control ID, explicit execution confirmation, operator reference, network confirmation, fixed runtime, atomic single use and replay denial |
| `read_result` | Mode C result package plus verified audit reader | `THIN_FACADE` | no new market request / may first materialize deterministic local outputs | expose a verified `read_or_materialize_result` operation; do not split public semantics unless later needed |
| `export_ai_handoff` | Mode C response fields | `THIN_FACADE` | no new market request / none after verified materialization | stable subset of Result, Markdown, citations, Result/Audit references; reuse renderer and raw-fact exclusion |

## Side-effect and authority matrix

| Operation | Market network | Filesystem write | Creates / consumes authorization | Human / network confirmation | Replay sensitive | Autonomous-safe preflight |
|---|---|---|---|---|---|---|
| describe | no | no | neither | no / no | no | yes |
| validate | no | no | neither | no / no | no | yes |
| preview | no | no | neither | no / no | no | yes |
| authorize | no | yes | creates | explicit human/operator / no | authorization uniqueness | no |
| execute | approved scope only | yes | consumes | explicit execution / network where required | yes, atomic single-use | no |
| read result | no additional | first materialization only | neither; finalized package required | no / no | verified deterministic reread | yes |
| export handoff | no additional | none after read/materialization | neither | no / no | verified deterministic reread | yes |

## Client-neutral and local-first boundaries

Route naming, APIRouter tag (`unified-workbench-mode-a`), Workbench phrasing, buttons, preview state, and download UX are `COSMETIC_ONLY` or `TRANSPORT_ONLY`; none is a semantic authority or blocker. `control_package_id`, explicit confirmation fields, body bounds, and Result/Audit references are `SERVICE_CONTRACT_RELEVANT`, and should be retained with client-neutral wording. No examined coupling is an `ARCHITECTURAL_BLOCKER`.

The launcher defaults to `127.0.0.1`, rejects non-local hosts (only `127.0.0.1`, `localhost`, `::1`), and reports `network_on_startup:false`. CORS is limited to localhost/127.0.0.1 origins. There is no remote-access or authentication protocol because the service is local-first only. Market network is possible only in governed execute-once production transport, never startup, validation, preview, read, or export. Existing containment, identifier checks, 1 MiB body limits, privileged-field rejection, no client path selection, and safe evidence writing remain mandatory. No secrets, headers, cookies, or raw rich facts are service output.

## Contract options and recommendation

**Option A — adopt `/api/unified/*` directly:** lowest migration and browser-compatibility cost, but its Workbench-named namespace/tag is less clear as a long-lived client-neutral surface.

**Option B — add `/api/market-evidence/*` thin facade:** delegates 1:1 to the existing Mode A/B/C functions and returns the same objects. It has a small transport-test cost, preserves the Workbench as an unchanged client, clearly supports a future MCP adapter, and avoids divergence if no business logic is placed in the facade.

Recommendation: `OPTION_B`. M8R-07B should add only the capability-description projection and thin facade routes needed to name the seven operations. The existing `/api/unified/*` surface remains backward-compatible. No second semantic stack, schema, resolver, planner, authorization model, runtime adapter, projector, or Markdown renderer is permitted.

## MCP readiness and versioning

`MCP_THIN_ADAPTER_FEASIBLE = true`. A later MCP adapter can validate tool transport input, call the recommended local service, and translate output; it need not own market business logic. No obstacle requires duplication.

Keep current v1 request, authorization, receipt, bundle, Result, and Audit schemas authoritative. Give only the future HTTP facade a lightweight transport identifier (for example `service_contract_version`); do not version internal Python names or create v2 artifacts without a real break.

## Carried debt

| Debt | Classification | Rationale |
|---|---|---|
| `CURRENT_OBSERVATION_FAILURE_OBSERVABILITY_DEBT` | `DOES_NOT_BLOCK_M8R_07` | future richer bounded diagnostics are separate |
| `CURRENT_OBSERVATION_RELIABILITY_UNRESOLVED` | `DOES_NOT_BLOCK_M8R_07` | source reliability is not a facade-contract blocker |
| `MODE_C_EOD_CURRENTNESS_INTEGRATION_DEBT` | `SHOULD_BE_DEFERRED` | no service-boundary change required |
| `AI_MARKDOWN_FRESHNESS_DUPLICATION` | `SHOULD_BE_DEFERRED` | retain accepted renderer |
| `AI_HANDOFF_CITATION_COMPLETENESS` | `SHOULD_BE_HANDLED_DURING_M8R_07B` | define stable export subset without changing citation semantics |
| `REQUEST_MODE_VS_EXECUTION_OUTCOME_WORDING` | `SHOULD_BE_HANDLED_DURING_M8R_07B` | client-neutral transport wording belongs at facade documentation level |

## Verification, blockers, and exact next scope

The startup check and existing no-network Mode A/B1/B2/execute-once/Mode C/Workbench/API/handoff tests are recorded in this PR. No market network call was made. There are no architectural blockers.

M8R-07B, if authorized, may implement Option B only: a localhost-only facade, deterministic capability-description projection from the committed catalog and executor metadata, explicit thin route contracts for the seven operations, contract-level no-network/confirmation/replay tests, and client-neutral documentation. It must not implement MCP, source retries, remote exposure, new schemas, or any Phase D semantic change.
