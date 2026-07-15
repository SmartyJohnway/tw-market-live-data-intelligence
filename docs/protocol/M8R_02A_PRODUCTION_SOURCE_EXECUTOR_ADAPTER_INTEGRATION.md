# M8R-02A Production Source Executor Adapter Integration

Status: `m8r_02a_production_source_executor_adapter_integration_go`

Decision: `GO`

Recommended successor: `M8R-02B-CONTROLLED-LIVE-EXECUTION-VALIDATION-AND-FINAL-RUNTIME-ACCEPTANCE`

## Verified baseline

The implementation started from `/workspace/tw-market-live-data-intelligence` on branch `work` at HEAD `02cb65c68dea2eb61fd3d1fcd28eab4eae2940d4`, the PR #138 merge. The working tree was clean before edits. Applicable instructions were the repository-root `AGENTS.md` and the M8R-02A task text.

## Executor evidence matrix

| Source family / route | Existing callable | Accepted input | Actual network scope | Actual result schema | Target bounding | Identity evidence | Reusable directly? | Required adapter |
|---|---|---|---|---|---|---|---|---|
| TWSE_MIS listed equity | `scripts.probe_twse_mis_rich_fields.fetch_twse_mis_rows` | `tse_{symbol}.tw` such as `tse_2330.tw` | bounded TWSE MIS query list | raw MIS rows plus failures/telemetry | one approved query identifier only | MIS `key`/symbol fields checked against approved target | yes, with normalization | `execute_twse_mis_operation` |
| TWSE_MIS OTC equity | same | `otc_{symbol}.tw` such as `otc_6488.tw` | bounded TWSE MIS OTC route | raw MIS rows plus failures/telemetry | one approved query identifier only | MIS route and symbol checked | yes, with normalization | `execute_twse_mis_operation` |
| TWSE_MIS TAIEX index | same | `tse_t00.tw` | bounded TWSE MIS index route | raw MIS row | one approved query identifier only | approved route `tse_t00.tw`; no symbol inference | yes, with limitations | `execute_twse_mis_operation` |
| TWSE_OPENAPI equity EOD | `execute_twse_official_eod_adapter` | requested symbols | whole-market source endpoint | M8A adapter result with normalized observations | retain approved symbol only | retained observation symbol/market | yes | `execute_twse_openapi_operation` |
| TPEX_OPENAPI equity EOD | `execute_tpex_official_eod_adapter` | requested symbols | whole-market source endpoint | M8A adapter result with normalized observations | retain approved TPEx symbol only | retained observation symbol/market | yes | `execute_tpex_openapi_operation` |
| TAIFEX_MIS monthly future | `execute_taifex_mis_snapshot` + `adapt_taifex_mis_observation` | exact monthly regular selector | bounded REST + SockJS initial snapshot | M8C runtime observation then M8 context observation | one selector, one retained observation | returned contract month/session from M8C context `contract_identity` | yes | `execute_taifex_mis_operation` |
| TAIFEX_MIS monthly option | same | exact monthly regular selector with strike/call-put | bounded REST + SockJS initial snapshot | M8C runtime observation then M8 context observation | one selector, one retained observation | returned month/strike/option type/session from M8C evidence | yes | `execute_taifex_mis_operation` |
| TAIFEX_OPENAPI future reference/statistical | `execute_taifex_openapi_refresh` | product plus contract selector | official OpenAPI endpoint selected by M8B | M8B execution result observations | bounded requested product/contract selector | contract-level only when selector is retained | yes | `execute_taifex_openapi_operation` |
| TAIFEX_OPENAPI option reference/statistical | same | product plus month/strike/call-put selector | official OpenAPI endpoint selected by M8B | M8B execution result observations | bounded requested product/contract selector | contract-level only when selector is retained | yes | `execute_taifex_openapi_operation` |

## Adapter architecture and registry

`scripts/m8r_production_source_adapters.py` contains source-specific M8R executor adapters. Each public adapter matches the existing M8R executor signature and returns the normalized operation envelope consumed by `normalize_operation_result(...)`.

The M8R-02 orchestrator remains generic. Its default production registry now calls `build_production_executor_registry(...)` and maps the five network source families to source-specific adapters instead of the prior generic fail-closed placeholder. Dependency injection remains supported by passing an explicit `executor_registry` to preflight or execution.

## Per-source disposition

| Source family | M8R-02A disposition | Limitation |
|---|---|---|
| `TWSE_MIS` | `production_adapter_ready_with_explicit_limitations` | live-ish only, unofficial/undocumented, no exchange-guaranteed realtime claim |
| `TWSE_OPENAPI` | `production_adapter_ready_with_explicit_limitations` | whole-market endpoint fetched by accepted M8A adapter; retained output is approved targets only; EOD only |
| `TPEX_OPENAPI` | `production_adapter_ready_with_explicit_limitations` | whole-market endpoint fetched by accepted M8A adapter; retained output is approved TPEx targets only; EOD only |
| `TAIFEX_MIS` | `production_adapter_ready_with_explicit_limitations` | monthly regular-session futures/options only; no weekly, after-hours, front-month, continuous contract, polling, reconnect, or delta loop |
| `TAIFEX_OPENAPI` | `production_adapter_ready_with_explicit_limitations` | official EOD/statistical/reference semantics only; product-level data is not relabeled as live or exact contract evidence |

No source family remains silently mapped to `_blocked_default_executor`.

## Target translation and bounding

TWSE MIS translation is explicit: TWSE equity/ETF uses `tse_{symbol}.tw`, TPEx OTC equity/ETF uses `otc_{symbol}.tw`, and TAIEX index uses `tse_t00.tw`. The adapter rejects route/market mismatches and requests no extra symbols.

TWSE and TPEx OpenAPI adapters record `network_scope = whole_market_endpoint` and `retention_scope = approved_targets_only`. Non-approved rows are discarded before creating the operation result and cannot enter `source_observation`, `issues`, diagnostics, or retained artifacts.

## TAIFEX exact identity trace

For TAIFEX MIS, the approved target derivative identity is translated to the existing M8C selector fields: `instrument_type`, `requested_product_id`, `contract_month_or_week`, `session`, and for options `strike_price` and `option_type`. The M8C executor validates selectors, resolves runtime identity, collects a bounded initial snapshot, and the context adapter exposes returned identity through `safe_fields.contract_identity`. The M8R adapter returns only identity evidence present in that accepted runtime/context output. Unsupported weekly or after-hours identities block before network.

For TAIFEX OpenAPI, the adapter passes requested product, session, month, strike, and option type to the M8B executor. The adapter records `identity_level` in safe fields and does not describe aggregate product-level records as exact-contract observations.

## Currentness, exceptions, and accounting

Adapters preserve source timing classes: TWSE MIS and TAIFEX MIS remain `liveish_intraday_snapshot`; TWSE/TPEx OpenAPI remain `official_eod`; TAIFEX OpenAPI remains official statistical/reference timing. Currentness is copied from accepted source observations where available and otherwise remains unresolved/not applicable.

Expected source exceptions become stable issue codes such as `source_timeout`, `source_connection_failed`, `source_payload_invalid`, `source_identity_mismatch`, `target_not_present_in_source_result`, and `exact_contract_not_supported`. Raw exception text, URLs, headers, cookies, tokens, and response bodies are not copied.

Each adapter reports `adapter_invocation_count = 1`, `network_attempted`, and `network_request_count`. TAIFEX MIS reports a multi-request logical path count for REST plus SockJS initial snapshot. No adapter adds orchestrator retry, polling, scheduler, background execution, persistent database, cache, ranking, prediction, recommendation, broker action, MCP/API/frontend work, M9 source, arbitrary URL support, or credential handling.

## M8 core and AI package integration

Fake-transport non-network integration tests prove the route from approved M8R plan through the production adapter registry to operation result, M8 context core, and `ai_market_context.v1`. Production executor adapter readiness is now distinct from live validation readiness:

```json
{
  "package_schema_ready": true,
  "offline_packaging_ready": true,
  "production_orchestrator_contract_ready": true,
  "production_executor_adapters_ready": true,
  "production_live_execution_ready": false,
  "m8r_02a_required": false,
  "m8r_02b_required": true,
  "live_validation_completed": false
}
```

## Tests

Added non-network tests for production registry replacement, TWSE MIS route translation and identity failure, OpenAPI whole-market bounding, TPEx market guarding, TAIFEX MIS future/option exact selectors, TAIFEX OpenAPI identity level, sanitized timeout handling, network gating, and end-to-end fake adapter execution into `ai_market_context.v1`.

## Known limitations

M8R-02A did not run controlled live network acceptance and does not mark runtime live-ready. M8R-02B remains required before any production live execution readiness claim.

## Decision

`GO`: all intended MVP source families have explicit source-specific production adapters, bounded retention, identity checks, conservative timing/currentness semantics, sanitized errors, accounting, non-network integration tests, and AI package compatibility. `production_live_execution_ready` and `live_validation_completed` remain `false`.
