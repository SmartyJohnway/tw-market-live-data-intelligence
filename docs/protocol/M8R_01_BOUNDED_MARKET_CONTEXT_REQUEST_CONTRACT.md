# M8R-01 Bounded Market Context Request Contract

Status: `m8r_01_bounded_market_context_request_contract_go`
Decision: `GO`
recommended_next_task = `M8R-02-ONE-SHOT-MARKET-CONTEXT-EXECUTION-ORCHESTRATOR`
next_task = `null`
next_task_status = `awaiting_operator_acceptance`
Successor state handling: M8R-02 is recommended but not activated or approved.

## 1. Verified baseline

| Item | Observed value |
|---|---|
| Repository path | `/workspace/tw-market-live-data-intelligence` |
| Branch | `work` |
| Starting HEAD | `090f219da564500f5f8ad6b640f755d7c9d01c2d` |
| Latest merge | `090f219 Merge pull request #134 from SmartyJohnway/codex/misopenapi` |
| Working tree before edits | clean |
| Applicable AGENTS.md | `AGENTS.md` |
| Active task | `M8R-01-BOUNDED-MARKET-CONTEXT-REQUEST-CONTRACT` |
| Active task status in registry evidence | `operator_approved_not_started` |

The local repository matched the expected baseline. No reset or discard was performed.

## 2. Scope and non-scope

M8R-01 defines only request, normalization, validation, deterministic planning, hashing, approval artifact semantics, fixtures, tests, and documentation. It performs no network execution, no adapter invocation, no orchestrator, no FastAPI/MCP/frontend production surface, no scheduler, no polling, no cache/database, no AI package exporter, and no M9 ingestion.

## 3. Repository evidence reused

M8R-01 reuses these current authorities instead of redefining source semantics:

- M8R-00 boundary: `docs/protocol/M8R_00_PRODUCTIZATION_BOUNDARY_AND_SCOPE_CLOSURE.md`.
- Canonical M8 context schema and builder: `docs/protocol/M8_MULTI_SOURCE_MARKET_CONTEXT_SCHEMA.md`, `docs/protocol/M8_MULTI_SOURCE_CONTEXT_BUILDER.md`, and `scripts/m8_multi_source_context_builder.py`.
- M8 freshness/currentness policies: `docs/protocol/M8_SOURCE_FRESHNESS_EVALUATOR.md`, M8A/M8B/M8C currentness helpers, and M8 source registry policy.
- Controlled AI exposure policy: `docs/protocol/M8_CONTROLLED_CONVERSATION_CONTEXT_INTEGRATION.md`.
- TWSE MIS route semantics: `docs/protocol/M7G_TWSE_MIS_MARKET_ROUTE_SEMANTICS.md`.
- Source capability policy: `docs/data_capabilities/m8_source_capability_registry.json`.
- M5K/M5N watchlist precedent: `config/m5k_default_watchlist.json` and `scripts/m5k_common.py`.
- M7G request/approval precedent: `scripts/m7g_refresh_request_package.py` and `scripts/m7g_controlled_refresh_executor.py`.
- Existing runtime implementation evidence: M8A/M8B/M8C execution modules and server/MCP read-only surfaces.

## 4. Required design decisions

| Question | Decision |
|---|---|
| Reusable M5K/M5N fields | `symbol`, `market`, `instrument_type`, `preferred_sources`/source preferences, display metadata, enabled/order precedent, watchlist boundedness. |
| Too weak for M8R | M5K IDs such as `twse:0050` omit exact source/context plan identity; `listed_or_otc_equity` is too ambiguous; default TAIFEX `front_month` is too weak for immutable approval. |
| Existing canonical target identifier | No complete repository-wide canonical security master or M8R target ID exists; M8R-01 defines deterministic request-layer target IDs without claiming a security-master truth. |
| Market representation | M5K uses lowercase `twse`, `tpex`, `otc`, `taifex`; M8R normalizes to `TWSE`, `TPEX`, `TAIFEX`; `OTC` is an alias of `TPEX`. |
| Index distinction | `TAIEX` must be `market=TWSE`, `instrument_type=index`; it is not an equity or ETF. |
| Futures/options selectors | Futures require explicit TAIFEX market and regular-session derivative identity. Options require underlying/product, expiry, strike, call/put, and contract type; weekly options are deferred. |
| Accepted runtime source families | `TWSE_MIS`, `TWSE_OPENAPI`, `TPEX_OPENAPI`, `TAIFEX_MIS`, `TAIFEX_OPENAPI`, derived from M8 registry fields plus narrow accepted-family allowlist. |
| Research-only/credential-gated | `CREDENTIAL_GATED_PROVIDER`, `EXTERNAL_VALIDATION_ONLY`, `MOPS`, unknown/M9-like names, `TPEX_MIS`, and `ROTC_MIS` cannot enter normalized requests or plans. |
| Supported combinations | TWSE equity/ETF -> `TWSE_MIS` and `TWSE_OPENAPI`; TPEx equity/ETF -> `TWSE_MIS` OTC route and `TPEX_OPENAPI`; TAIEX -> TWSE MIS index route only; TAIFEX futures/options -> `TAIFEX_MIS` regular session and `TAIFEX_OPENAPI`. |
| Fail-closed combinations | Cross-market source/target mismatch, `TPEX_MIS`, `rotc_`, after-hours TAIFEX MIS, weekly options, ambiguous options, derivatives on cash markets, equities on TAIFEX. |
| Omitted `instrument_type` | Not allowed. Instrument type must be explicit and valid. |
| Incorrect market/symbol pairing | Rejected as target-level identity/source compatibility issue where M8R can prove route incompatibility; no cross-market guessing. |
| Duplicates | Identical duplicate target IDs collapse deterministically; conflicting duplicate definitions are target-level rejections. |
| Target order and hash | Target and mapping arrays are sorted by identity/context/source, so input order does not affect hash. Hash validation rebuilds scope from actual top-level plan fields; embedded `hash_scope` is audit-only and non-authoritative. |
| Immutable plan fields | Normalized target identities, context types, planned source families, source-to-target mappings, network scope, retained scope, output scope, approval flag, non-goal flags. |
| Excluded presentation metadata | `created_at_utc`, display labels, notes, comments, approval timestamps, and execution results. |
| Approval expiry/single-use | Approval artifact carries `single_use` and optional `expires_at_utc`; non-approved/expired/consumed statuses are invalid. Approval timestamps must be parsed RFC3339 UTC values; `now >= expires_at_utc` is expired. |
| Output scope | Relative repository path only; no absolute path, traversal, `frontend/public`, `research/generated`, `.env`, secrets, or credentials paths. |
| Limits vs network estimates | Request limits block before plan creation; planned network scope records operation classes only and does not estimate live availability. |
| Unsupported context types | Unknown context types are request-blocking validation errors; context unsupported for a target is target-level rejection. |

## 5. Contract layers

### 5.1 User request

Schema version: `m8r_bounded_market_context_request.v1`.

Required shape:

```json
{
  "schema_version": "m8r_bounded_market_context_request.v1",
  "request_id": "operator-provided-or-generated-id",
  "targets": [],
  "requested_context_types": [],
  "requested_source_families": [],
  "execution_policy": {},
  "output_policy": {}
}
```

`targets[]` require explicit `symbol`, `market`, and `instrument_type`. Optional target-level `requested_context_types` overrides request-level context lists. Request-level `requested_source_families` is an upper-bound allowlist available to all targets; target-level `requested_source_families` is an exact explicit source selection and any extra incompatible source rejects that target.

### 5.2 Normalized request

Schema version: `m8r_normalized_market_context_request.v1`.

Normalization performs case normalization, market aliases, instrument aliases, symbol trimming/uppercasing, sorted context/source lists, target ordering, duplicate handling, default policy values, canonical booleans, rejected target separation, and non-goal flags.

### 5.3 Execution plan

Schema version: `m8r_market_context_execution_plan.v1`.

The plan contains `plan_id`, `plan_hash`, `normalized_request_hash`, resolved targets, rejected targets, requested context types, planned source families, source-to-target/context mapping, planned operation classes, bounded retained scope, derived `network_required`, `approval_required=true`, output scope, non-goal flags, and `created_at_utc`. It contains no live results. `source_health` maps to `local_source_health_read` and `market_session_state` maps to `local_market_clock_evaluation`; both are local operations with `network_required=false`, while market source observations use `planned_network_fetch`. Local-only plans still require approval in M8R-01 for contract consistency.

### 5.4 Approval artifact

Schema version: `m8r_market_context_approval.v1`.

The artifact binds `approval_id`, `plan_id`, `plan_hash`, `approval_status`, `approved_at_utc`, `approved_by`, `single_use`, optional `expires_at_utc`, and approved-scope summary. It is UI-independent and does not execute anything.

## 6. Compatibility matrix

| Target class | Allowed context/source plan | Rejections |
|---|---|---|
| TWSE listed equity/ETF | `liveish_observation` via `TWSE_MIS` `tse_{symbol}.tw`; `official_eod_reference` via `TWSE_OPENAPI`. | `TPEX_OPENAPI` exact-market mismatch, `TPEX_MIS`, `rotc_`, TAIFEX sources. |
| TPEx/OTC equity/ETF | `liveish_observation` via `TWSE_MIS` `otc_{symbol}.tw`; `official_eod_reference` via `TPEX_OPENAPI`. | `TPEX_MIS`, `rotc_`, TWSE listed route when identity/source compatibility fails. |
| TAIEX index | `liveish_observation` via `TWSE_MIS` `tse_t00.tw`. | Treating TAIEX as equity/ETF, TPEX market, invented EOD index support. |
| TAIFEX futures | `liveish_observation` via `TAIFEX_MIS` regular session; `official_eod_reference`/`official_statistical_reference` via `TAIFEX_OPENAPI`. | After-hours, delta runtime, continuous-contract assumptions, TWSE/TPEX sources. |
| TAIFEX options | Same TAIFEX sources only when exact option identity is supplied. | Missing underlying/expiry/strike/call_put/contract_type, weekly options, ambiguous identity. |

## 7. Context vocabulary

Accepted vocabulary: `liveish_observation`, `official_eod_reference`, `official_statistical_reference`, `source_health`, `market_session_state`.

Post-MVP concepts such as historical baseline, technical signal, attention status, corporate action, overseas context, broker branch, ETF flow, and portfolio exposure are not accepted context types in M8R-01.

## 8. Source eligibility and M9/research exclusion

A source family is selectable only when all are true:

1. present in `docs/data_capabilities/m8_source_capability_registry.json`;
2. `runtime_available=true`;
3. `runtime_executable=true`;
4. `ai_context_allowed=true`;
5. `credential_required=false`;
6. included in the narrow accepted M8R family set: `TWSE_MIS`, `TWSE_OPENAPI`, `TPEX_OPENAPI`, `TAIFEX_MIS`, `TAIFEX_OPENAPI`.

This predicate rejects unrecognized names, M9-like candidates, credential-gated providers, validation-only sources, inactive sources, and research-only sources without relying only on source-name prefixes.

## 9. Request limits

| Limit | Value |
|---|---:|
| Maximum targets | 10 |
| Maximum requested source families | 5 |
| Maximum context types per target/request | 5 |
| Maximum total target-context combinations | 40 |
| Maximum output relative path length | 160 |
| Maximum identifier length | 64 |

Requests exceeding request-level limits fail before plan creation.

## 10. Plan hash and ID rules

M8R-01 uses canonical JSON (`sort_keys=true`, compact separators, UTF-8, no incidental whitespace, no NaN) and SHA-256.

Hash scope is rebuilt from actual top-level plan fields and includes schema version, normalized request hash, normalized target identities, requested context types, planned source families, source-to-target/context mapping, network scope, retained scope, output scope, approval-required flag, and non-goal flags. Stored `hash_scope` may remain for audit/debugging, but approval validation treats it as non-authoritative and emits `plan_internal_scope_mismatch` if it differs from the rebuilt scope.

Hash scope excludes `created_at_utc`, display labels, operator notes, comments, approval timestamps, and execution results.

`request_id` identifies request lifecycle. `plan_id` is deterministic as `m8r-plan-<first16(plan_hash)>`. `plan_hash` is the immutable scope digest. `approval_id` identifies the approval event/artifact.

## 11. Validation and rejection model

Stable issue codes include: `invalid_schema_version`, `missing_required_field`, `invalid_market`, `invalid_symbol`, `invalid_instrument_type`, `market_symbol_incompatible`, `instrument_type_market_incompatible`, `unsupported_context_type`, `unsupported_source_family`, `source_not_runtime_eligible`, `research_only_source_forbidden`, `credential_gated_source_forbidden`, `source_target_incompatible`, `duplicate_target_conflict`, `target_limit_exceeded`, `context_limit_exceeded`, `source_limit_exceeded`, `unsafe_output_scope`, `unresolved_identity`, `ambiguous_identity`, `unsupported_session_scope`, `unsupported_product_scope`, `identifier_too_long`, `approval_plan_hash_mismatch`, `approval_not_approved`, `approval_expired`, `invalid_approval_timestamp`, `plan_hash_mismatch`, and `plan_internal_scope_mismatch`.

Schema, policy, source eligibility, limit, and output-safety errors block the request. Individual identity/source compatibility errors are target-level rejections. A plan requires at least one resolved target.

## 12. Public implementation API

Implemented in `scripts/m8r_bounded_market_context_request.py`:

- `accepted_source_families(...)`
- `normalize_market_context_request(...)`
- `validate_market_context_request(...)`
- `resolve_target_identity(...)`
- `compile_market_context_execution_plan(...)`
- `compute_plan_hash(...)`
- `build_approval_artifact(...)`
- `validate_approval_for_plan(...)`

All functions are pure except local source-registry file reads for policy lookup. The module imports no HTTP client, no source adapter, and performs no network calls.

## 13. Fixtures and tests

Representative fixtures live under `tests/fixtures/m8r_request/`. Unit tests live in `tests/unit/test_m8r_bounded_market_context_request.py` and cover valid requests, invalid identities, forbidden sources, limits, deterministic hashes, approval binding, and non-network boundary checks.

## 14. Known limitations

- M8R-01 does not introduce a complete security master and therefore does not claim comprehensive symbol ownership validation.
- TAIEX official EOD index context remains unsupported unless a later accepted adapter/source contract implements it.
- TAIFEX after-hours, weekly options, delta runtime, and continuous-contract semantics remain deferred.
- Source health and market session state are planned as local non-market-source operations only; M8R-01 does not fetch, compute, or read live source-health/session artifacts.
- Approval artifacts are semantic records only; CLI/API/MCP/frontend approval surfaces are future work.

## 15. M8R-02 entry conditions

M8R-02 may consume only a valid `m8r_market_context_execution_plan.v1` whose `plan_hash` is recomputed and matched to an approved `m8r_market_context_approval.v1`. It must fail closed before any network action if scope, source, context, output, retained scope, or non-goal flags differ from the approved hash.

## 16. Acceptance status

Decision: `GO`.

Rationale: the request contract is deterministic; exact identity and route compatibility fail closed; source eligibility is derived from accepted M8 policy plus narrow allowlist; research-only/M9/credential-gated sources are excluded; plan scope is immutable and hashable; approval binds to exact plan hash; implementation is non-network; and M8R-02 has a clear input contract.

## M8R-01F canonical identity correction

M8R-01 remains merged, but M8R-02 is gated by `M8R-01F-CANONICAL-REQUEST-HASH-AND-SEMANTIC-DUPLICATE-CORRECTION`. The M8R-01 status is therefore `GO_WITH_REQUIRED_FOLLOW_UP_FIX` until the corrective gate is accepted.

M8R-01F formally separates four identities:

- `request_id` is lifecycle-only and traces one operator request lifecycle. It must not alter `normalized_request_hash`, `plan_hash`, or `plan_id`.
- `normalized_request_hash` is the canonical semantic request hash. It is built from normalized schema version, accepted target semantic identities, effective per-target contexts and source selections, source-selection mode where behavior differs, normalized derivative/session identity, execution-policy fields, validated output scope, and non-goal flags that govern execution.
- `plan_id` and `plan_hash` identify the exact executable approved scope. The plan hash may include `normalized_request_hash` only because that hash is the canonical semantic hash, not a full normalized-object digest.
- `approval_id` identifies one approval event bound to one exact plan hash and is not interchangeable with request or plan identity.

Execution-semantic fields may enter canonical semantic scope: `market`, `symbol`, `instrument_type`, option/future selectors, `session`, effective requested context types, effective requested source families, source-selection mode, execution policy, output policy, retained scope, local/network operation class, and execution-governing non-goal flags.

Presentation fields must not enter semantic request or plan identity: `display_name`, `display_label`, `description`, `notes`, `comments`, UI ordering, display labels, and operator narrative.

Lifecycle fields must not enter plan identity: `request_id`, `created_at_utc`, `approval_id`, and `approved_at_utc`.

Rejected targets are audit/non-executable output only. They remain visible in `normalized_request.rejected_targets` and `plan.rejected_targets`, but rejected target raw `input_identity`, presentation metadata, aliases, validation warnings, validation message text, and operator comments do not enter `normalized_request_hash` or `plan_hash` and do not produce source mappings.

Duplicate comparison uses canonical normalized execution semantics rather than raw `input_identity`. Semantically identical aliases collapse deterministically. The issue code `duplicate_target_conflict` is reserved for the same canonical duplicate key with conflicting effective execution semantics such as different context types, exact target-level sources, option expiry/strike/call-put/contract type, derivative session, or target-scoped output/execution behavior.

Additional supported internal API functions:

- `build_target_semantic_scope(...)`
- `build_normalized_request_hash_scope(...)`

### M8R-01F follow-up closure

M8R-01F is complete with status `m8r_01f_canonical_request_hash_and_semantic_duplicate_correction_go`. M8R-02 remains inactive and awaits separate operator acceptance; the active state is `next_task=null`, `next_task_status=awaiting_operator_acceptance`, and `recommended_next_task=M8R-02-ONE-SHOT-MARKET-CONTEXT-EXECUTION-ORCHESTRATOR`.

The semantic request hash uses effective target scope. Request-level `requested_context_types` and `requested_source_families` are normalization defaults or allowlists only; they do not independently enter `normalized_request_hash` when accepted targets have already resolved effective target contexts, sources, source-selection mode, and planned mappings. If a request-level default actually changes a target's effective context/source/mapping scope, the target semantic scope changes and therefore both `normalized_request_hash` and `plan_hash` change.

TAIFEX futures use Model A exact contract identity for M8R-01F. A future target requires exact `expiry`, `contract_type=monthly`, and `session=regular`; the canonical identity includes expiry and contract type, for example `TAIFEX:future:TX:202607:monthly`. Implicit front-month selection is forbidden. Explicit selector identity such as `contract_selector=front_month` is rejected until a later contract defines selector binding, dynamic-resolution caveats, and execution-receipt recording semantics.
