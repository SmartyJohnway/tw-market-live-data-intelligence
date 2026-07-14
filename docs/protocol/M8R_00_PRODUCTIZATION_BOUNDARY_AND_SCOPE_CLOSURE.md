# M8R-00 Productization Boundary and Scope Closure

Status: `m8r_00_productization_boundary_scope_closure_conditional_go`

Decision: `CONDITIONAL_GO`

Exact immediate next task: `M8R-01-BOUNDED-MARKET-CONTEXT-REQUEST-CONTRACT`

## 1. Task identity and verified baseline

Task: `M8R-00-PRODUCTIZATION-BOUNDARY-AND-SCOPE-CLOSURE`.

This task closes the productization boundary for the next repository phase. It does not implement M8R-01 or later runtime behavior.

Verified local audit before edits:

| Item | Observed value |
|---|---|
| Repository path | `/workspace/tw-market-live-data-intelligence` |
| Branch | `work` |
| HEAD | `8b377abf4befecc52daaa80e4d9b2ed8851b1918` |
| Latest commit | `8b377ab Merge pull request #133 from SmartyJohnway/codex/integrate-m8c-01-into-m8c-02` |
| Working tree before edits | clean |
| Applicable AGENTS.md | `AGENTS.md` only |
| Implemented-through track | `M8C` |
| Next task state | `next_task=null`, `next_task_status=awaiting_operator_prioritization` |

Baseline conclusion: the checked-out repository matches the expected baseline and remains at PR #133 / M8C acceptance state.

## 2. Repository evidence inspected

Inspection covered these current authority areas:

- Governing instructions: `AGENTS.md`.
- Product and architecture docs: `README.md`, `docs/INDEX.md`, `docs/PROJECT_HISTORY.md`, `docs/architecture/SOURCE_AND_CAPABILITY_MODEL.md`, `docs/architecture/ai_watchlist_workflow.md`, `docs/reference/API_REFERENCE.md`, `docs/reference/MCP_REFERENCE.md`, `docs/operator/*`, `docs/release/*`, and `docs/reviews/*`.
- M8 contracts and acceptance: `docs/protocol/M8_00_FINAL_ACCEPTANCE_AND_CLOSURE.md`, `docs/protocol/M8_MULTI_SOURCE_MARKET_CONTEXT_SCHEMA.md`, `docs/protocol/M8_MULTI_SOURCE_CONTEXT_BUILDER.md`, `docs/protocol/M8_SOURCE_FRESHNESS_EVALUATOR.md`, `docs/protocol/M8_CONTROLLED_CONVERSATION_CONTEXT_INTEGRATION.md`, `docs/protocol/M8_THROUGH_M8B_CONSOLIDATED_FINAL_ACCEPTANCE.md`, `docs/protocol/M8_THROUGH_M8C_CONSOLIDATED_ACCEPTANCE.md`, `docs/protocol/M8A_OFFICIAL_EOD_CONTEXT_FINAL_ACCEPTANCE.md`, `docs/protocol/M8B_01_TAIFEX_OPENAPI_OFFICIAL_DERIVATIVES_EOD_FINAL_ACCEPTANCE.md`, `docs/protocol/M8C_01_TAIFEX_MIS_BOUNDED_RUNTIME_FINAL_ACCEPTANCE.md`, and `docs/protocol/M8C_02_TAIFEX_MIS_M8_CONTEXT_INTEGRATION_FINAL_ACCEPTANCE.md`.
- Source registries and contracts: `docs/data_capabilities/m8_source_capability_registry.json`, `docs/data_capabilities/m8a_official_eod_endpoint_contract_registry.json`, `docs/data_capabilities/m8b_taifex_openapi_endpoint_contract_registry.json`, `docs/data_capabilities/twse_mis_rich_field_inventory.json`, `docs/source_registry/source_authority_registry.json`, `config/m5l_live_source_adapter_matrix.json`, and `config/m5k_default_watchlist.json`.
- Runtime code: `scripts/m8*.py`, `scripts/m5k_common.py`, `scripts/build_m5n_conversation_context.py`, `scripts/m5q_source_health.py`, `scripts/market_clock_session_state.py`, `scripts/m7g_refresh_request_package.py`, `scripts/m7g_controlled_refresh_executor.py`, `server/main.py`, and `server/mcp_server.py`.
- Product surfaces: FastAPI routes in `server/main.py`, MCP tools in `server/mcp_server.py`, readonly frontend/workbench files under `frontend/readonly-preview/`, and operator docs under `docs/operator/`.
- Tests and fixtures: M8 builder/projection tests, M8A/M8B/M8C tests, source-health tests, FastAPI/MCP tests, watchlist tests, governance guards, and representative fixtures under `tests/fixtures/` and `research/probe_runs/`.

## 3. Current capability map

| Layer | Current source or component | Current status | Evidence |
|---|---|---|---|
| Listed cash intraday observation | `TWSE_MIS` | Runtime executable bounded live-ish context; AI context allowed with caveats | `docs/data_capabilities/m8_source_capability_registry.json`, `scripts/m5k_common.py`, `scripts/m8_multi_source_context_builder.py` |
| TPEx/OTC intraday observation | `TWSE_MIS` `otc_{symbol}.tw` route | Runtime executable bounded live-ish context; no `TPEX_MIS` source family | `docs/data_capabilities/m8_source_capability_registry.json`, `docs/protocol/M7G_TWSE_MIS_MARKET_ROUTE_SEMANTICS.md`, `scripts/m5k_common.py` |
| Listed official EOD | `TWSE_OPENAPI` | Runtime executable official EOD/reference; not current price | `scripts/m8a_twse_official_eod_adapter.py`, `scripts/m8a_official_eod_execution.py`, `docs/protocol/M8A_OFFICIAL_EOD_CONTEXT_FINAL_ACCEPTANCE.md` |
| TPEx official EOD | `TPEX_OPENAPI` | Runtime executable official EOD/reference; classification remains bounded without complete security master | `scripts/m8a_tpex_official_eod_adapter.py`, `scripts/m8a_official_eod_instrument_classifier.py`, `docs/protocol/M8A_OFFICIAL_EOD_CONTEXT_FINAL_ACCEPTANCE.md` |
| TAIFEX official derivatives EOD/statistical/reference | `TAIFEX_OPENAPI` | Runtime executable through M8B selected adapters and bounded retention | `scripts/m8b_taifex_openapi_execution.py`, `scripts/m8b_taifex_*_adapter.py`, `docs/protocol/M8B_01_TAIFEX_OPENAPI_OFFICIAL_DERIVATIVES_EOD_FINAL_ACCEPTANCE.md` |
| TAIFEX derivatives live-ish observation | `TAIFEX_MIS` | Controlled bounded regular-session initial-state context, fail-closed currentness, no after-hours/weekly/delta | `scripts/m8c_taifex_mis_execution.py`, `scripts/m8c_taifex_mis_context_adapter.py`, `docs/protocol/M8C_02_TAIFEX_MIS_M8_CONTEXT_INTEGRATION_FINAL_ACCEPTANCE.md` |
| Freshness classification | M8 freshness evaluator | Pure helper, no network | `scripts/m8_source_freshness_evaluator.py`, `tests/unit/test_m8_source_freshness_evaluator.py` |
| Source-specific currentness | M8A/M8B/M8C currentness helpers | Implemented per source family, including TAIFEX MIS bridge | `scripts/m8a_market_day_currentness_resolver.py`, `scripts/m8b_taifex_currentness.py`, `scripts/m8_taifex_mis_currentness_bridge.py` |
| Canonical M8 market-context core | M8 multi-source builder | Pure builder over caller-provided observations and registry | `scripts/m8_multi_source_context_builder.py`, `docs/protocol/M8_MULTI_SOURCE_CONTEXT_BUILDER.md` |
| Controlled conversation projection | M8 conversation projector | Pure projection with raw-field and wording guards | `scripts/m8_controlled_conversation_context.py`, `tests/unit/test_m8_controlled_conversation_context_integration.py` |
| Legacy/current local product surfaces | M5/M7 FastAPI, MCP, frontend, conversation package | Existing product surfaces expose M5K/M5N/M7G capabilities but not a unified M8R AI context product | `server/main.py`, `server/mcp_server.py`, `frontend/readonly-preview/*`, `scripts/build_m5n_conversation_context.py` |

Capability conclusion: the repository has enough source adapters, source semantics, currentness/freshness logic, M8 builder, controlled projection, and local surfaces to support a productization track. The primary gap is one-shot product orchestration and AI handoff, not source discovery.

## 4. Actual runtime and product call-flow map

### Existing M8A official EOD path

`validate_m8a_official_eod_live.py` or future caller -> `scripts/m8a_official_eod_execution.execute_official_eod_refresh` -> `execute_twse_official_eod_adapter` / `execute_tpex_official_eod_adapter` -> parse rows into `m8a_official_eod_observation.v1` -> `observation_to_context_observation` -> `build_multi_source_market_context` -> `build_controlled_conversation_context` when projected.

Reusable for M8R: adapters, observation conversion, execution boundary, currentness resolver. Missing for M8R: unified request model, source plan, execution receipt, and product package wrapper.

### Existing M8B TAIFEX OpenAPI path

`validate_m8b_taifex_openapi_live.py` or future caller -> `scripts/m8b_taifex_openapi_execution.execute_taifex_openapi_refresh` -> selected M8B adapters (`futures`, `options`, `final_settlement`, `large_trader_oi`, `put_call_ratio`, `block_trade`) -> `m8b_taifex_derivatives_observation.create_observation` -> `build_multi_source_market_context` -> controlled conversation projection.

Reusable for M8R: selected endpoint adapters, bounded selectors, row-limit handling, currentness application, M8 context observations. Missing for M8R: request-level optional derivatives context policy and target-level missing-context reporting.

### Existing M8C TAIFEX MIS path

Future or validation caller -> `scripts/m8c_taifex_mis_execution.execute_taifex_mis_snapshot` -> selector validation and bounded SockJS/REST collection -> `scripts/m8c_taifex_mis_observation.build_observation` -> `scripts/m8c_taifex_mis_context_adapter.adapt_taifex_mis_snapshot_to_m8_observations` -> `build_multi_source_market_context` with TAIFEX MIS source-specific currentness bridge -> controlled projection.

Reusable for M8R: runtime selector, execution limits, context adapter, fail-closed currentness. Missing for M8R: product-level decision about when TAIFEX MIS is requested, how unsupported sessions/products become missing-context objects, and how fallback EOD reference is surfaced.

### Existing M5K/M5N product path

FastAPI/MCP/frontend/operator caller -> `scripts/m5k_common.validate_watchlist` / `plan_live_observation` -> optional explicit `execute_live_observation` -> latest observation artifact -> `scripts/build_m5n_conversation_context.py` or `scripts.m5k_common.build_conversation_context` -> temporary conversation context markdown/JSON.

Reusable for M8R: watchlist shape, route planning concepts, explicit execution gate, conversation handoff UX pattern, source-health coupling. Limitation: M5N conversation package is not the canonical M8 core and predates M8A/M8B/M8C full multi-source context.

### Existing M7G controlled refresh path

`build_m7g_controlled_refresh_request_package` -> validation -> `execute_m7g_controlled_manual_refresh` -> safe artifact result. Reusable for M8R approval design concepts, but not sufficient as the M8R one-shot orchestrator because M7G is TWSE_MIS-centered and not the M8 multi-source product package.

## 5. Canonical-truth matrix

| Truth area | Canonical file/module | Enforced? | Duplicate representations | Drift risk | M8R treatment |
|---|---|---:|---|---|---|
| Source authority | `docs/data_capabilities/m8_source_capability_registry.json` for M8; legacy `docs/source_registry/source_authority_registry.json` for older M5/MCP docs | Partly runtime via M8 builder registry lookup | README tables, source registry, capability inventory | Medium | Use M8 registry for M8R; cite legacy registry only as historical/compatibility |
| Source type | M8 source registry and endpoint registries | Partly | `docs/source_catalog.md`, legacy generated snapshot code | Medium | Do not create new source-type registry |
| Timing class | M8 source registry and source-specific contracts | Yes for M8 builder inputs | Older M5 freshness fields (`freshness_status`) | Medium | Preserve M8 timing class in core and views |
| Runtime availability | M8 registry plus adapter modules | Partly | README/M5 matrix | Medium | Treat registry as policy and adapters as implementation evidence |
| Runtime executability | M8 registry plus `execute_*` functions | Yes when caller invokes explicit validators/adapters | M5L adapter matrix | Medium | M8R source set must be derived from M8 registry and existing executable functions |
| AI context eligibility | M8 registry plus builder/projection | Yes | M5N guidance, source registry | Medium | Preserve `ai_context_allowed` and `ai_exposure_level`; do not override in product views |
| AI exposure level | M8 registry | Yes in builder/projection policy | Docs and tests | Low/medium | Use as canonical field in `m8_context_core` |
| Freshness policy | `scripts/m8_source_freshness_evaluator.py`, M8 registry `freshness_evaluator_policy` | Yes | M5 freshness strings | Medium | Preserve M8 freshness; map legacy only as derived if needed |
| Currentness policy | M8A/M8B/M8C currentness helpers and contracts | Yes | Market clock context | Medium | Keep source-specific; no global replacement |
| Instrument context schema | `docs/protocol/M8_MULTI_SOURCE_MARKET_CONTEXT_SCHEMA.md`, `scripts/m8_multi_source_context_builder.py` | Yes | M5F/M5N snapshot structures | Medium | `m8_context_core` must reuse M8 builder output |
| Safe-field policy | M8 builder scrubber and M8 controlled conversation projector | Yes | M5N filtering | Low/medium | Product views must derive only from safe fields |
| Conversation projection | `scripts/m8_controlled_conversation_context.py` | Yes | `scripts/build_m5n_conversation_context.py` | Medium | Reuse M8 projector for M8R handoff; M5N is UX precedent |
| Forbidden interpretations | M8 registry, M8 schema, controlled projector, forbidden scanners | Partly | Many docs/tests | Medium | Top-level M8R package must carry forbidden interpretations and no-signal flags |
| Source health | `scripts/m5q_source_health.py` for M5Q reports; M8 has source freshness summaries but no unified M8R source-health object | Partly | M5F source health, M5Q latest, API summaries | High | M8R must keep source health separate from freshness/currentness and define exact reuse in M8R-01/02 |
| Output artifact semantics | M5F/M5N/M7G artifacts and M8 context builder outputs | Partly | `research/generated`, staging, live observation artifacts | High | M8R needs a wrapper artifact; M8 core remains canonical inside wrapper |

No single canonical object currently covers the full future AI product package. The smallest remediation is a future M8R package wrapper that embeds the existing M8 multi-source context output as `m8_context_core` and places all product summaries under derived `product_views`.

## 6. Duplicate and drift-risk analysis

| Representation | Classification | Reuse decision |
|---|---|---|
| `docs/data_capabilities/m8_source_capability_registry.json` | Current M8 source policy authority | Reuse as canonical M8R policy input |
| `docs/source_registry/source_authority_registry.json` | Older authority registry still used by compatibility/read-only MCP | Do not replace; do not use as M8R canonical source policy |
| `config/m5l_live_source_adapter_matrix.json` | M5/M5L adapter metadata | Reuse route/adapter planning ideas only; not canonical M8 source registry |
| `config/m5k_default_watchlist.json` and `m5n_watchlist.v1` | Current watchlist shape | Adapt for M8R request contract; add stricter explicit market/instrument validation in M8R-01 |
| `research/staging/m5f/*` | Historical/reviewed canonical package artifacts | Historical product precedent; not M8R output canonical |
| `research/live_observation_runs/current_conversation_context/*` | Current M5N conversation package | Reuse handoff UX concepts; not M8R canonical core |
| M8 builder output | Current canonical multi-source market context core | Reuse directly as `m8_context_core` |
| M8 controlled conversation projection | Current AI-safe projection | Reuse for M8R markdown/handoff derivation |
| M7G refresh request/execution packages | Approval/safe artifact precedent | Reuse approval invariants; do not make M7G the M8R orchestrator |
| Generated `research/generated/*` | Legacy generated artifacts | Do not write from M8R MVP; avoid path per governance guard |

Key drift risks:

1. M8R could accidentally create a second source registry.
2. M8R package summaries could override M8 authority/timing/currentness fields.
3. Legacy M5 freshness/source-health strings could be mistaken for M8 currentness.
4. M9/research-only sources are represented as metadata in registries but not yet guarded by an M8R-specific package exclusion test.

## 7. Verified product gap

The working hypothesis is supported with caveats. The repository has source adapters, contracts, currentness/freshness helpers, M8 context builder, controlled conversation projection, product surfaces, watchlist UX, and source-health components. The missing product capability is a unified one-shot M8 product flow:

`bounded target request -> immutable execution plan -> explicit approval -> exactly one execution -> M8 context core -> product wrapper/views -> AI handoff`.

Current product surfaces either predate full M8 (`M5K/M5N`) or are source/task-specific validators (`M8A`, `M8B`, `M8C`). They do not yet produce a single AI Taiwan market-context product package over all accepted M8 source families.

## 8. M8R definition

`M8R` is conditionally approved as `M8 Runtime Productization / Release Track`, with `R` meaning `Runtime Productization / Release`, not a new architecture generation.

M8R is accepted in principle, subject to the stated pre-runtime conditions, as a productization track over the existing canonical M8/M8A/M8B/M8C contracts and implementations. It may orchestrate, package, project, render, and expose existing M8 context.

## 9. M8R non-definition

M8R is not:

- a new M8 schema family;
- a second source registry;
- a second source authority model;
- a second freshness/currentness model;
- a second AI exposure policy;
- a market scanner;
- a persistent collector;
- a trading terminal;
- a prediction, ranking, signal, or broker execution system;
- a route for M9/research-only sources to enter default AI context.

## 10. Productization principles with evidence status

| # | Principle status | Evidence | Required wording revision | Future enforcement |
|---:|---|---|---|---|
| 1 | Supported | M8 registry/builder centralize source semantics | None | M8R tests compare product views to `m8_context_core` |
| 2 | Supported | M8 schema and builder are current canonical context core | None | Package includes builder output unchanged |
| 3 | Supported with revision | Product views do not yet exist | Say views are derived from embedded M8 core | M8R-03 consistency tests |
| 4 | Supported | Builder/projection retain authority/timing/freshness/currentness | None | Field immutability tests |
| 5 | Supported | Existing validators and M5K/M7G gates are explicit/manual | None | Execution receipt assertions |
| 6 | Supported | README/M8 acceptances prohibit scheduler/polling/signal behavior | None | Governance/forbidden behavior tests |
| 7 | Supported | FastAPI/MCP M5K execution requires explicit confirmation | Generalize beyond one phrase | M8R-05 approval artifact tests |
| 8 | Supported with revision | M7G request packages exist; immutable approved scope not yet generalized | Require plan hash / approved scope identity | M8R-05 plan immutability tests |
| 9 | Supported with revision | M8 builder flags unavailable/stale, but product missing-context object absent | Define missing-context object in M8R-03 | Missing-context tests |
| 10 | Supported | OpenAPI contracts and M8 schema say EOD is not realtime/current price | None | EOD/live-ish separation tests |
| 11 | Supported | MIS policies say not realtime guaranteed | None | Handoff wording tests |
| 12 | Supported with revision | TWSE MIS retrieved-at bounded freshness policy exists; TAIFEX MIS rejects retrieved_at upgrade | Preserve source-specific exception only where policy allows | Source-specific freshness/currentness tests |
| 13 | Supported | Registry flags and scanners forbid signals/recommendations | Avoid positive examples in product output | Scanner and markdown golden tests |
| 14 | Supported with revision | Credential-gated metadata exists, but M9 is not a concrete registry family | Define default exclusion and machine-check in M8R-01 | Registry/package exclusion tests |
| 15 | Supported | Reusable adapters/builders/surfaces exist | None | Reuse decisions in PR review checklist |
| 16 | Supported | Duplication risk documented | None | No-new-registry/schema tests or doc checks |
| 17 | Supported with revision | Existing watchlist validation is insufficient for all M8R route compatibility | M8R-01 must add exact compatibility validation | Rejected-target fixtures |
| 18 | Supported with revision | Concepts exist but are currently spread across M5Q/M8/currentness contexts | M8R package must keep separate top-level/product view concepts | Separation tests |

## 11. Package boundary decision

Future M8R product package should follow this boundary:

```json
{
  "package_version": "ai_market_context.v1",
  "generated_at_utc": "...",
  "request_summary": {},
  "execution_receipt": {},
  "m8_context_core": {},
  "product_views": {}
}
```

Decisions:

1. `m8_context_core` should directly embed the existing `m8_00_multi_source_market_context.v1` object produced by `scripts.m8_multi_source_context_builder.build_multi_source_market_context`.
2. Canonical fields are those inside `m8_context_core`: source authority, timing class, freshness/currentness, safe fields, omitted fields, caveats, and AI exposure policy.
3. `product_views` may include instrument cards, source-health summary, missing-context summary, compact/full markdown handoff text, and operator-readable execution summary.
4. Product views may group/order/summarize but must not override canonical authority, timing, currentness, freshness or safe-field truth.
5. Existing M5N conversation packages provide UX precedent but not the M8 canonical core.
6. A new wrapper is necessary because no current artifact combines request summary, execution receipt, M8 core, and derived AI handoff views.

Machine-test boundary: every product-view source/timing/currentness field must either be copied from `m8_context_core` by reference path or be marked as derived summary with a deterministic provenance path.

## 12. Request and identity boundary decision

M8R-01 should use explicit identity MVP:

- explicit `market`;
- explicit `symbol`;
- explicit or validated `instrument_type`;
- exact route/source compatibility;
- no cross-market guessing;
- ambiguous or unresolved targets fail closed.

Minimum compatibility rules for M8R-01:

| Input class | Allowed source families | Fail-closed examples |
|---|---|---|
| TWSE listed equity/ETF | `TWSE_MIS` `tse_*`, `TWSE_OPENAPI` | `market=TPEX` for a TWSE-only route if unresolved |
| TPEx/OTC equity/ETF | `TWSE_MIS` `otc_*`, `TPEX_OPENAPI` | introducing `TPEX_MIS` or `rotc_` |
| TAIEX index | TWSE MIS market index route where already supported; official EOD only if adapter supports it | treating as equity |
| TAIFEX futures/options | `TAIFEX_MIS`, `TAIFEX_OPENAPI` with supported selector scope | after-hours, weekly option, ambiguous option identity |

A complete canonical security master is not an MVP blocker because M8A already documents bounded/incomplete production classification. M8R-01 must nevertheless reject unresolved market-symbol-route combinations.

## 13. One-shot orchestration boundary

Future M8R-02 must preserve these limits:

### Request-level limits

- bounded target count;
- allowed M8 source set only;
- explicit requested context types;
- no arbitrary URL;
- no M9/research-only default sources;
- no full-market retained output.

### Planned execution metadata

- planned target identities;
- planned source families;
- planned network calls by source family, not adapter internals;
- expected retained scope;
- no polling/background/scheduler/startup fetch;
- no ranking/alerts/recommendations;
- output scope and safe output directory.

### Actual execution receipt

- started/completed timestamps;
- exact approved plan hash;
- actual source families attempted;
- target-level success/failure/missing context;
- network calls attempted count/class;
- artifact paths;
- `polling=false`, `scheduler=false`, `background_process=false`, `auto_retry=false`, `persistent_db=false`, `raw_payload_in_ai_package=false`.

No M8R task may relax TAIFEX MIS M8C limits: no realtime guarantee, no delta, no after-hours activation, no weekly option activation, no polling.

## 14. Partial completion semantics

Future package statuses:

| Status | Meaning | Safe output? |
|---|---|---|
| `ready` | All requested contexts satisfied with no blocking caveats | Yes |
| `ready_with_caveats` | Requested contexts usable but caveated/stale/reference-only caveats exist | Yes |
| `partial` | At least one requested target/context missing, but at least one requested context remains usable and all missing context is explicit | Yes, with mandatory missing-context summary |
| `blocked` | No usable safe context, identity unresolved for all targets, approval mismatch, unsafe source, or canonical M8 core invalid | No AI market discussion package; receipt only |

Minimum missing-context object for M8R-03:

```json
{
  "target": {},
  "requested_context_type": "liveish_observation",
  "source_family": "TAIFEX_MIS",
  "reason": "source_specific_currentness_unresolved",
  "usable_fallback": "TAIFEX_OPENAPI official EOD/reference only",
  "forbidden_interpretations": ["do_not_treat_eod_reference_as_current_price"]
}
```

Target-level status and package-level status must be distinct. A package may be `partial` even when some targets are `ready`.

## 15. Source-health/freshness/currentness/missingness separation

| Concept | Existing definition/enforcement | Boundary decision |
|---|---|---|
| Source health | `scripts/m5q_source_health.py`; FastAPI/MCP source-health readers | Operational/source availability; not equivalent to freshness or currentness |
| Freshness | `scripts/m8_source_freshness_evaluator.py`, M8 registry policy | Time-age/timing assessment; not exchange session proof |
| Currentness | M8A/M8B/M8C source-specific helpers | Market/date/session/source-specific semantic assessment |
| Missing context | Not yet canonical as product object | M8R-03 must add machine-readable missing-context product view |
| Interpretation caveats | Registry caveats, builder/projection caveats, AI policy | AI wording/usage constraints; not source operational status |

Current code has conceptual overlap in older M5 artifacts (`freshness_status`, `source_health`, `observation_status`) but M8 code separates source freshness/currentness more clearly. M8R must not flatten these concepts into one status string.

## 16. Approval-semantics boundary

Future M8R approval invariant: the executed request must be identical to the explicitly approved plan. Approval semantics are defined in M8R-01, enforced by M8R-02, and exposed through operator/UI surfaces in M8R-05.

M8R-01 must define, without network execution:

- normalized request contract;
- execution-plan contract;
- `plan_id` semantics generated from normalized request and plan material;
- `plan_hash` semantics over normalized targets, source families, network scope, retained scope, output scope, and non-goal flags;
- `approval_required` flag;
- approval-artifact schema or abstract approval contract;
- approved-scope identity;
- request/plan immutability requirements.

M8R-02 must enforce, before any network execution:

- executor accepts only an approved immutable plan artifact;
- executor recomputes and verifies the plan hash;
- scope mismatch fails closed before network execution;
- tests may simulate operator approval through fixtures.

M8R-05 must implement only approval surfaces over the already-defined semantics: CLI confirmation surface, local API approval surface, MCP plan/approve/execute surface, and frontend approval interaction. M8R-05 must not be the first place where approval semantics are defined.

A fixed confirmation phrase may be used by a surface implementation but is not the long-term approval model by itself.

## 17. M9 and deferred-source exclusion

Current repository state represents credential-gated providers as metadata/research providers and excludes them from runtime dependency semantics, but it does not yet have an M8R-specific package guard because M8R does not exist.

M8R-00 decision:

- M9/research-only sources are excluded from default M8R runtime and `ai_market_context.v1`.
- Unaccepted sources must not affect deterministic metrics.
- Large M9 governance is deferred.
- Minimum machine-checkable guard should be an M8R-01 prerequisite or part of M8R-01 tests, not a broad M9 subsystem in M8R-00.

## 18. Reuse-versus-create decisions and code-level dependency map

| Future capability | Existing implementation | Existing contract | Existing tests | Gap | Reuse decision |
|---|---|---|---|---|---|
| Bounded target request | `scripts/m5k_common.normalize_watchlist`, `validate_watchlist`, `plan_live_observation`; `config/m5k_default_watchlist.json` | `docs/architecture/ai_watchlist_workflow.md` | `tests/unit/test_m5n_watchlist_workflow.py`, `tests/unit/test_m7g_refresh_request_package_builder.py` | M8-wide explicit market/source/context request and route compatibility | Adapt, do not replace |
| Source selection | M8 registry; M5L adapter matrix; M8A/M8B/M8C execution args | M8 source registry and source contracts | M8 source governance tests | Unified M8R source-selection policy | Reuse registry, add request contract |
| One-shot execution | M8A `execute_official_eod_refresh`; M8B `execute_taifex_openapi_refresh`; M8C `execute_taifex_mis_snapshot`; M5K `execute_live_observation` | M8A/M8B/M8C execution contracts | M8A/B/C execution tests | Cross-source orchestrator and receipt | New orchestrator reusing existing executors |
| Currentness | M8A resolver; M8B currentness; M8C currentness bridge | M8 freshness/currentness contracts | Currentness tests | Packaging separation from source health | Reuse as-is |
| M8 context core | `build_multi_source_market_context` | M8 schema/builder docs | `tests/unit/test_m8_multi_source_context_builder.py` | Product wrapper | Reuse directly |
| Product views | M5N conversation context, M8 controlled projection | M5N and M8 conversation docs | Conversation projection tests | `ai_market_context.v1` views | New derived views over M8 core |
| Markdown handoff | `build_controlled_conversation_context`, `build_m5n_conversation_context` | Conversation package guide; M8 projection contract | Markdown/forbidden tests | Compact/full M8R prompt blocks | Adapt M8 projector, use M5N UX precedent |
| Execution receipt | M5B/M5C/M7G receipts, M8 validator summaries | Authorization/probe contracts | M5B/M7G tests | Unified M8R receipt | New receipt based on existing patterns |
| Approval flow | M7G request package; M5K confirm flag; MCP/FastAPI confirmation gates | Authorization docs | M7G/MCP/FastAPI tests | Plan-hash immutable approval | Adapt concepts, new M8R plan/approval contract |
| API/MCP exposure | `server/main.py`; `server/mcp_server.py` | API/MCP reference | `tests/unit/test_mcp_server.py`, `tests/unit/test_m5fgh_fastapi_context.py` | M8R plan/execute/latest endpoints/tools | Add later, not M8R-00 |

## 19. Incremental acceptance strategy

Do not defer validation until M8R-06.

| Task | Required acceptance |
|---|---|
| M8R-01 | request validation fixtures; execution-plan and approval-artifact contract fixtures; `plan_id`/`plan_hash` semantics; route compatibility; rejected target semantics; request/plan immutability; no M9 default source; no second registry/schema; no network execution |
| M8R-02 | one-shot execution tests with mocked executors; approved immutable plan required; plan-hash recomputation; scope mismatch fail-closed before network; partial completion; execution receipt; no polling/background/retry/scheduler; no raw payload in product scope |
| M8R-03 | `m8_context_core`/derived view consistency; missing-context tests; EOD/live-ish separation; source-health/freshness/currentness separation |
| M8R-04 | Markdown golden tests; compact/full handoff tests; forbidden wording tests; no current-price overclaim for EOD |
| M8R-05 | CLI/API/MCP/frontend approval surface tests over M8R-01/M8R-02 semantics; unauthorized execution fail-closed; approved scope cannot be mutated by any surface |
| M8R-06 | complete E2E user-scenario closure with no live network requirement by default |

Reusable current tests/scanners: `tests/unit/test_m8_multi_source_context_builder.py`, `tests/unit/test_m8_controlled_conversation_context_integration.py`, M8A/B/C adapter/currentness tests, `tests/test_m5q_source_health.py`, `tests/unit/test_mcp_server.py`, `tests/test_m6e_operator_acceptance.py`, `scripts/governance_forbidden_path_guard.py`, and `scripts/forbidden_behavior_scanner.py`.

## 20. User-scenario inventory

| Scenario | Expected package status | Usable context | Missing context | Required caveats | Forbidden interpretation |
|---|---|---|---|---|---|
| TWSE listed equity with live-ish + official EOD | `ready_with_caveats` | TWSE MIS live-ish and TWSE OpenAPI EOD | none if both succeed | not realtime; EOD not current price | trading signal/recommendation |
| TPEx/OTC equity with `otc_*` route | `ready_with_caveats` | TWSE MIS OTC route and TPEx OpenAPI EOD | none if both succeed | source is TWSE MIS route, not `TPEX_MIS` | cross-market guessing |
| TAIEX market index | `ready_with_caveats` or `partial` | supported bounded index observation | official EOD if unavailable | index context not full-market breadth | market prediction |
| TAIFEX futures contract | `ready_with_caveats` | TAIFEX MIS regular-session and/or TAIFEX OpenAPI EOD | live-ish if session/currentness unresolved | no realtime/delta/night-session guarantee | futures lead/predict spot |
| TAIFEX MIS unavailable with OpenAPI fallback | `partial` | TAIFEX OpenAPI EOD/statistical reference | TAIFEX MIS live-ish observation | fallback is not current price | settlement as current price |
| Official EOD only | `ready_with_caveats` | official reference | live-ish context not requested or unavailable | EOD/reference only | current price claim |
| Stale live-ish observation | `ready_with_caveats` or `partial` | stale context as caveated metadata/supporting context | fresh live-ish current observation | stale not current | present-tense current quote |
| Currentness unresolved | `partial` | metadata/reference context | current live-ish context | fail-closed currentness | current/live wording |
| Partial target success | `partial` | successful target contexts | failed target/context entries | explicit missing-context summary | treating package as complete |
| Invalid market-symbol combination | `blocked` for target, package `partial` or `blocked` | unaffected valid targets | invalid target identity | route compatibility failed | automatic market fallback |
| Source unavailable | `partial` or `blocked` | other source contexts | unavailable source context | source health separated from currentness | silent omission |
| Network disabled | `blocked` or `partial` depending cached/reference inputs | no live network results | network-required contexts | no network attempted | pretending fresh data |
| After-hours TAIFEX request | `partial` | official EOD/statistical fallback | TAIFEX MIS after-hours live-ish | after-hours unsupported | night-session activation |
| Weekly-option request | `partial` or target blocked | official reference only if exact supported selector exists | TAIFEX MIS weekly option runtime | weekly option runtime deferred | unsupported product activation |

## 21. Proposed M8R task and PR dependency graph

### M8R-00 Productization Boundary and Scope Closure

Purpose: lock productization boundaries. User value: prevents scope drift before implementation. Reuses: repository evidence and contracts. Missing capability: none implemented. New artifact: this document. Network behavior: none. Exit: `CONDITIONAL_GO` and next task named.

### M8R-01 Bounded Market Context Request Contract

Purpose: define exact normalized request, execution-plan contract, target identity, source/context selection, route compatibility, rejected-target semantics, `plan_id`, `plan_hash`, `approval_required`, approval-artifact/abstract approval contract, approved-scope identity, and request/plan immutability requirements. User value: user/AI can request bounded context without ambiguity and can later approve an exact immutable plan. Reuses: M5N watchlist, M5K planning, M8 registry, M7G approval concepts. Missing capability: M8-wide request and plan object. Files likely involved: `docs/protocol/`, `config/`, `scripts/`, `tests/unit/`. Tests: validation fixtures, route compatibility, plan-hash fixtures, approval-artifact fixtures, no M9 default source. Network: none. Entry: M8R-00 accepted. Exit: request/plan/approval contract and validator accepted.

### M8R-02 One-shot Market Context Execution Orchestrator

Purpose: compose existing executors once, accepting only an approved immutable plan artifact from M8R-01. User value: one command produces M8 core inputs only after the exact approved plan is verified. Reuses: M8A/B/C executors, M5K/M7G execution gate concepts. Missing capability: cross-source orchestrator and receipt. Tests: mocked one-shot execution, approved-plan requirement, plan-hash recomputation, scope mismatch fail-closed before network, partial completion, no scheduler/polling/retry. Network: explicit approved-plan execution only. Entry: M8R-01. Exit: orchestrator creates receipt and M8 context core without product views.

### M8R-03 AI Market Context Product Package

Purpose: define and generate `ai_market_context.v1` wrapper with `m8_context_core` and derived views. User value: AI-readable product artifact. Reuses: M8 builder and controlled projection. Missing capability: wrapper, missing-context view, consistency tests. Network: none beyond M8R-02 inputs. Entry: M8R-02. Exit: package schema/export accepted.

### M8R-04 AI Handoff and Operator CLI

Purpose: compact/full markdown handoff and operator CLI around package generation. User value: pasteable context for AI discussion. Reuses: M5N handoff UX, M8 projection markdown. Missing capability: M8R-specific prompt blocks. Tests: golden markdown and forbidden wording. Network: none unless invoking M8R-02 with explicit approval. Entry: M8R-03.

### M8R-05 Plan / Approval / Execute Surface

Purpose: implement CLI/API/MCP/frontend approval surfaces over the approval semantics already defined in M8R-01 and enforced in M8R-02. User value: AI can prepare a plan, the user can approve exact scope, and every surface preserves the same immutable approved plan. Reuses: FastAPI/MCP/frontend patterns and M7G approval concepts. Missing capability: operator-facing approval interactions. Tests: unauthorized execution fail-closed, surface cannot mutate approved plan/scope/hash, UI-specific approval artifact handling. Network: execute only through M8R-02 approved immutable plan enforcement. Entry: M8R-04.

### M8R-06 Final User-scenario Acceptance

Purpose: end-to-end scenario closure over supported sources and failure modes. User value: confidence that product solves original AI discussion problem. Reuses: all prior M8R tasks and existing M8 tests. Missing capability: complete scenario suite. Network: non-network fixtures by default; optional bounded live validation separate. Entry: M8R-05.

## 22. Deferred and post-MVP items

Initial M8R MVP defers:

- attention / disposition / trading restriction enrichment;
- corporate action / ex-right / ex-dividend enrichment;
- recent 5D/20D baseline;
- spot-derivatives descriptive composer;
- overseas reference context;
- TAIEX concentration;
- ETF passive-flow research;
- broker branch research;
- credential-gated provider integration;
- personal portfolio overlay;
- TAIFEX after-hours activation;
- TAIFEX weekly-option activation;
- SockJS delta runtime;
- persistent polling.

Recommended post-MVP bundle: `M8R-E1-OFFICIAL-QUOTE-INTERPRETATION-ENRICHMENT`, limited to quote-interpretation caveats unless separately re-scoped.

## 23. Decision log

| Decision | Result | Rationale |
|---|---|---|
| M8R naming | Keep `M8R`, define `R` as Runtime Productization / Release | Matches milestone style while preventing new-architecture interpretation |
| High-level decision | `CONDITIONAL_GO` | Direction supported, but M8R-01 must add request/identity guard and M9 exclusion tests before runtime work |
| Canonical core | Existing M8 multi-source context | M8 builder is current accepted core |
| Package wrapper | Needed | No current artifact combines request, receipt, M8 core, and product views |
| Security master | Not MVP blocker | Existing classification caveat permits bounded exact identity; route compatibility still required |
| M9 | Deferred/excluded by default | Product gap is orchestration/handoff, not high-risk research ingestion |

## 24. Risks and mitigations

| Risk | Mitigation |
|---|---|
| M8R becomes a parallel architecture | M8R may only wrap/derive from M8 core; no second registry/schema/currentness policy |
| Product views drift from M8 core | Consistency tests from M8R-03 onward |
| Legacy M5 source-health/freshness strings get conflated with M8 currentness | Separate source health, freshness, currentness, missing context, and caveats in package |
| Orchestrator scope creep | One-shot only; no scheduler/polling/background/retry/ranking/alerts |
| API/MCP unauthorized execution | Plan hash and approval artifact invariant |
| M9 source leakage | M8R-01 default-source exclusion test |
| TAIFEX unsupported session/product activation | Preserve M8C fail-closed policy and unsupported session/product missing-context entries |
| Official EOD becomes current price in AI handoff | EOD/live-ish separation tests and markdown golden tests |

## 25. Validation and inspection record

Commands executed for M8R-00 in this PR branch:

| Command | Result | Notes |
|---|---|---|
| `git diff --check` | PASS | No whitespace/diff-format errors. |
| `python scripts/governance_forbidden_path_guard.py` | PASS | Command completed with no forbidden path error. |
| `python scripts/forbidden_behavior_scanner.py` | PASS | Returned `{"ok": true, "findings": []}`. |
| `python -m compileall scripts server tests` | PASS | Scripts, server, and tests compiled successfully. |
| `pytest -m "not network" -v` | FAIL | Full non-network suite was executed on the same effective code state and reported 1321 passed, 1 skipped, 1 deselected, 7 failed. Failure group: existing M5D/frontend-public baseline drift and dependent candidate/materialization assertions. |
| Representative suite listed below | PASS | 160 passed, 1 warning. |

Full-suite failure detail from `pytest -m "not network" -v`:

- `tests/unit/test_m5d_frontend_publication_preflight.py::test_m5d_request_is_request_only` failed because candidate validation reported `frontend_public_baseline_drift`.
- `tests/unit/test_m5d_publication_candidate.py::test_candidate_validates` failed because candidate validation reported `frontend_public_baseline_drift`.
- `tests/unit/test_m5d_publication_candidate.py::test_frontend_public_baseline_recomputed_matches_current` failed because the committed frontend-public baseline hash for `frontend/public/index.html` did not match the current file hash.
- `tests/unit/test_m5d_publication_candidate.py::test_destination_already_exists_simulation` and `tests/unit/test_m5d_publication_candidate.py::test_rollback_no_existing_destination_deletes_new_file` failed as dependent candidate/simulation assertions after the baseline drift.
- `tests/unit/test_m5d_publication_candidate.py::test_shallow_checkout_missing_pr57_commit_does_not_block` failed because candidate validation still reported `frontend_public_baseline_drift`.
- `tests/unit/test_m5e_controlled_frontend_publication.py::test_reproducibility_materialize_candidate` failed because the generated `frontend_public_baseline.json` hash differed from the committed candidate manifest.

Base-branch reproduction was not performed because this follow-up is constrained to the existing PR branch and the base branch name is not present locally as `main` in this checkout. Causality is therefore classified from unchanged-path evidence and failure scope rather than direct base reproduction: PR #134 changes protocol/index documentation, and this follow-up additionally updates the authoritative M8 source-capability registry plus tests that encoded its active next-task state. It does not modify `frontend/public` artifacts; the failed tests compare existing M5D frontend-public baseline/materialization artifacts against `frontend/public/index.html`. Classification: known pre-existing non-task baseline failure.

Representative suite command:

```bash
pytest -v \
  tests/unit/test_m8_multi_source_context_builder.py \
  tests/unit/test_m8_controlled_conversation_context_integration.py \
  tests/unit/test_m8_source_freshness_evaluator.py \
  tests/unit/test_m8_source_governance_foundation.py \
  tests/unit/test_m8a_official_eod_context_integration.py \
  tests/unit/test_m8b_taifex_openapi_context_integration.py \
  tests/unit/test_m8c_02_taifex_mis_context_integration.py \
  tests/test_m5q_source_health.py \
  tests/unit/test_mcp_server.py \
  tests/unit/test_m5k_workflow.py
```

Result: PASS, `160 passed, 1 warning`.

## 26. GO / CONDITIONAL GO / NO-GO conclusion

`CONDITIONAL_GO` for M8R as `M8 Runtime Productization / Release Track`.

Evidence supports that:

- existing M8 context model is sufficiently canonical for product reuse;
- source semantics are stable enough not to be redefined;
- existing runtimes can be composed in a bounded one-shot workflow;
- the main missing capability is product orchestration/handoff;
- M8R can remain a productization track rather than a new architecture.

Conditions before M8R-02 runtime implementation:

1. M8R-01 must define and test a bounded normalized request contract with explicit market/symbol/instrument identity and route compatibility.
2. M8R-01 must define and test the execution-plan contract, `plan_id`, `plan_hash`, `approval_required`, approval-artifact/abstract approval contract, approved-scope identity, and request/plan immutability requirements without network execution.
3. M8R-01 must add default exclusion tests for M9/research-only sources.
4. M8R-01/M8R-03 must define machine-readable missing-context semantics.
5. M8R-02 must accept only an approved immutable plan artifact, recompute/verify the plan hash, and fail closed on scope mismatch before network execution.
6. M8R-03 must enforce `m8_context_core` as canonical and product views as derived.

## 27. Exact immediate next task

`M8R-01-BOUNDED-MARKET-CONTEXT-REQUEST-CONTRACT`.

M8R-01 must be documentation plus validator/test work only: normalized request contract, execution-plan contract, approval-required/approval-artifact semantics, approved-scope identity, plan immutability, route compatibility, and rejection fixtures; no live-source expansion, no one-shot orchestrator, no network execution, no API/MCP/Frontend production surface, and no M9 ingestion.
