# M8R-03 AI Market Context Package v1

Status: `m8r_03_ai_market_context_package_v1_go`

Decision: `GO`

Recommended immediate successor: `M8R-02A-PRODUCTION-SOURCE-EXECUTOR-ADAPTER-INTEGRATION`

Recommended product successor after M8R-02A: `M8R-04-CONTROLLED-AI-CONVERSATION-HANDOFF`

## Verified baseline

M8R-03 was implemented from repository path `/workspace/tw-market-live-data-intelligence` on branch `work` at starting HEAD `2c7199b3693ee91003c5284b7aeacfc4af730067`, the PR #137 merge for M8R-02. The working tree was clean before edits. Applicable instructions were the repository-root `AGENTS.md` and the operator task text.

Inspected authorities included M8R-00, M8R-01, M8R-01F, M8R-02 protocol documents; M8R request/orchestrator scripts; M8 multi-source context, controlled conversation, and source freshness scripts; M8R/M8 unit tests; source registry; and repository-wide currentness, caveat, missing-context, safe-field, execution-receipt, and timing/authority usages.

## Input contract

`ai_market_context.v1` consumes only `m8r_market_context_orchestration_result.v1`-shaped orchestration results and their associated `m8r_market_context_execution_receipt.v1`, `operation_results`, `missing_context`, approval state, and optional `m8_00_multi_source_market_context.v1` status. The authoritative builder is pure and does not accept raw source payloads or perform network execution.

Public entry point:

```python
build_ai_market_context_package(orchestration_result, *, generated_at_utc=None, package_policy=None)
```

## Package schema

The stable top-level schema is:

- `schema_version = ai_market_context.v1`
- deterministic `package_id`
- `generated_at_utc`
- `package_status = ready|ready_with_caveats|partial|blocked`
- `scope`
- `provenance`
- `targets`
- `source_contexts`
- `market_session_context`
- `source_health_context`
- `missing_context`
- `currentness_summary`
- `caveats`
- `forbidden_interpretations`
- `conversation_views`
- `production_readiness`
- `integrity`

## Hash identity

`package_hash` is SHA-256 over deterministic semantic hash scope. `package_id` is `amc-` plus the first 16 hash characters. The hash binds schema version, package status, provenance identifiers, approved scope summary, target/source/local/missing projections, currentness summary, caveats, forbidden interpretations, and production-readiness policy. It excludes `generated_at_utc`, markdown, filesystem paths outside approved artifact identity, and presentation-only ordering.

## Provenance

The package preserves traceability to approved execution through request, plan, approval, receipt, orchestration schema, execution start/finish, approval consumption, approved output scope, and retention assertions.

Required retention assertions are enforced:

```text
bounded_retention = true
raw_payload_retained = false
full_market_retained_output = false
```

Unsafe upstream retention produces a blocked package with `unsafe_upstream_retention_contract` and no successful live-readiness upgrade.

## Target, source, and local views

Target views are one entry per approved or inferable target and preserve market, symbol, instrument type, requested/available/missing context types, source-context references, target status, and exact TAIFEX derivative identity. Futures preserve `expiry`, `contract_type`, and `session`; options additionally preserve `underlying`, `strike`, and `call_put`.

Source-context views project only accepted normalized observation fields: source family/id, market, symbol, instrument type, context type, authority level, timing class, source timestamp, retrieval time, source-specific currentness, safe fields, and caveats. Raw payload, HTTP bodies, HTML, cookies, authorization headers, diagnostics, and full-market rows are excluded.

Local contexts are separated into `source_health_context` and `market_session_context`. Local source health is explicitly local-only and not treated as a live probe. Market session state is resolved only when evidence is present; unresolved state creates a caveat and a prohibition against saying the market is open or closed.

## Currentness rules

The package preserves source-specific currentness and timing classes rather than deriving currentness from retrieval time alone. `liveish_intraday_snapshot`, `official_eod`, `official_statistics_eod`, and `reference_metadata` remain distinct. Package-level summary may be `current`, `mixed`, `stale`, `unknown`, or `not_applicable`; mixed packages are never labeled simply current.

## Missing-context rules

Every upstream missing-context record is preserved with target, context type, planned source family, reason code, operation status, null usable fallback, and `not_safe_to_infer_missing_values`. Missing required contexts make the package partial or blocked; they are not hidden by another successful source.

## Caveat model

Caveats are deterministic objects with stable code, severity, scope, optional target/source, and message. Implemented categories include partial context, stale source, unknown currentness, unresolved market session, local health not live probe, EOD not intraday, live-ish not exchange-official realtime, production executor adapter not ready, production live execution not ready, exact TAIFEX contract requirement, missing context, and M8 core unavailability.

## Forbidden interpretations

Machine-readable prohibitions include `not_full_market`, `not_trading_signal`, `not_prediction`, `not_recommendation`, `not_broker_instruction`, `not_guaranteed_realtime`, `not_all_sources_current`, `not_complete_when_partial`, `not_live_production_ready_without_m8r02a`, and `not_safe_to_infer_missing_values`, with source/local additions for EOD-not-live, live-ish-not-official-realtime, local health not live probe, and unresolved session not open/closed.

## Conversation views

Structured views are deterministic derivatives of the authoritative package:

- `compact`: bounded injection summary with package status, targets, latest usable observations, currentness, material caveats, and missing count.
- `standard`: target summaries, source provenance, currentness, missing context, caveats, and prohibitions.
- `diagnostic`: plan/receipt provenance, operation outcomes, source mappings, identity evidence, and caveat codes.

No investment-advice, prediction, recommendation, ranking, or broker-action language is generated.

## Retention and raw-data safety

Recursive forbidden-key inspection rejects keys including `raw_payload`, `response_body`, `html`, `cookies`, `authorization`, `api_key`, `access_token`, `refresh_token`, `secret`, and `password`. The scan is key-based so harmless caveat text containing words such as raw is not rejected.

## Artifact output

`write_ai_market_context_artifacts` writes only receipt-scoped files under an approved root and fails if the receipt directory already exists. Outputs are atomic JSON writes:

- `ai_market_context_v1.json`
- `ai_market_context_compact.json`
- `ai_market_context_standard.json`
- `ai_market_context_diagnostic.json`

No artifacts are written under `frontend/public` or `research/generated`.

## Production-readiness distinction

M8R-03 packages existing orchestration outputs. It does not make production network execution available and does not mark the product live-ready.

Required readiness flags remain conservative:

```json
{
  "package_schema_ready": true,
  "offline_packaging_ready": true,
  "production_orchestrator_contract_ready": true,
  "production_executor_adapters_ready": false,
  "production_live_execution_ready": false,
  "m8r_02a_required": true,
  "live_validation_completed": false
}
```

## Tests

Added focused unit coverage for deterministic identity, status derivation, source timing semantics, currentness, TAIFEX identity preservation, missing context, local contexts, forbidden interpretations, raw-data safety, conversation views, validation tampering, artifact writes, and non-network boundary checks.

Validation run for this acceptance used:

- `git diff --check`
- `python scripts/governance_forbidden_path_guard.py`
- `python scripts/forbidden_behavior_scanner.py`
- `python -m compileall scripts server tests`
- focused M8R/M8 unit suite required by the task
- `pytest -m "not network" -v`

## Known caveats

- M8R-03 is an offline packaging layer over accepted orchestration outputs; it does not replace M8R-02A.
- Production network executor adapters remain intentionally not ready until M8R-02A.
- Some packages may be `CONDITIONAL_GO` operationally when upstream local/currentness fields are unresolved, but the package layer itself is safe and deterministic.

## Decision

`GO`: the package schema is deterministic, safe, traceable to plan/approval/receipt, semantically faithful to source authority/timing/currentness, preserves missing contexts, excludes raw/full-market payloads, and is usable offline over accepted M8R-02 orchestration results.

Active-state handling:

```text
M8R-03 status = GO
next_task = null
next_task_status = awaiting_operator_acceptance
recommended_next_task = M8R-02A-PRODUCTION-SOURCE-EXECUTOR-ADAPTER-INTEGRATION
recommended_product_successor_after_m8r02a = M8R-04-CONTROLLED-AI-CONVERSATION-HANDOFF
production_live_execution_ready = false
production_executor_adapters_ready = false
```

## Commit 2 hardening notes

PR #138 commit 2 hardens the accepted M8R-03 package contract without changing the sequencing boundary. Conversation views remain deterministic derivatives, not main-hash inputs; validation now rebuilds compact, standard, and diagnostic views from the authoritative package-without-views and fails closed with `conversation_view_mismatch` if any stored AI-facing view diverges, omits required prohibitions, carries mismatched `package_id`, or adds unsupported investment language.

Artifact writing is now bound to `package.provenance.approved_output_scope.artifact_root` and `package.provenance.receipt_id`. Optional test overrides are accepted only when they exactly equal approved provenance; otherwise the writer fails with `approved_output_scope_mismatch` or `receipt_identity_mismatch`. Relative path safety remains a second guard and still rejects absolute, traversal, `frontend/public`, and `research/generated` roots.

Source-context caveats are normalized into one structured representation:

```json
{
  "code": "source_warning",
  "severity": "warning",
  "message": "source_warning",
  "source": "observation_caveat|operation_issue"
}
```

The normalizer accepts strings and dictionaries, preserves stable issue codes, deduplicates by canonical JSON, sorts deterministically, and does not copy sensitive exception detail fields.

Package construction now begins with `validate_orchestration_result_for_ai_package`. Malformed orchestration schemas, receipt schemas, missing receipt provenance, unsafe output scope, non-list operation/missing-context fields, incompatible receipt status, and incorrect receipt counts fail construction with `AIMarketContextPackageError`. Structurally valid unsafe-retention inputs may still produce a blocked package carrying `unsafe_upstream_retention_contract`.

Target provenance is explicit. Approved target projections are preferred. When M8R-02 output omits target projection but operation results contain bounded evidence, the package is labeled `target_identity_provenance = inferred_from_operation_result`, receives `approved_target_scope_not_fully_available`, and cannot become `ready`. Missing-only and globally blocked packages require approved target scope so approved targets and exact TAIFEX identities remain visible.

Currentness classification now uses an explicit vocabulary map rather than substring matching. Known fresh statuses map to `current`, known stale statuses to `stale`, EOD/reference statuses to `not_applicable`, and unresolved or unknown vocabulary to `unknown`; retrieval time alone does not create currentness.

Additional integrity validation checks approved target count, approved operation count against authoritative operation_outcomes, target available/missing context consistency, unique target source references, missing-context target references, status conservatism against upstream status, required base prohibitions, exact production-readiness flags, and deterministic conversation-view derivation.

## Commit 3 hardening notes

`operation_outcomes` are now authoritative, hash-bound package evidence derived directly from validated upstream `operation_results`. Each outcome records operation ID, target ID, terminal status, source family, context type, and operation class; the list is deterministic and is included in `build_ai_market_context_hash_scope`. Diagnostic conversation views only project `package.operation_outcomes` and are never used as an evidence source during validation.

Validation now checks operation-outcome IDs, terminal status vocabulary, target references, source-family allowlist/null-local semantics, and consistency with source contexts for successful non-local operations or missing-context records for failed/blocked non-local operations. Recomputing the package hash after operation-outcome tampering cannot bypass these semantic checks.

Operation issue messages are not trusted and are not copied into source contexts or AI views. For operation-issue dictionaries, only stable code, fixed severity, fixed source, and `message = code` enter the package. Fields such as upstream `message`, `detail`, `error`, exception text, paths, URLs, tokens, headers, and response excerpts are omitted. Observation caveat strings/dicts are also bounded by a safe caveat-code vocabulary; unknown prose is normalized to `source_warning` so unbounded upstream text cannot enter artifacts through a caveat field.
