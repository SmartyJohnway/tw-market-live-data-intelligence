# M8R-03D Watchlist Evidence Source Integration and Controlled Execution

Status: `GO_WITH_CAVEATS_fixture_and_controlled_executor_ready_live_validation_not_completed`.

## Scope and architecture

M8R-03D connects validated M8R-03C watchlist evidence requests to governed source execution through a separate orchestration layer. The flow is:

`validated watchlist evidence request -> authorization -> identity and route planning -> controlled source execution or fixture replay -> m8r_watchlist_input_observation.v1 normalization -> M8R-03C bundle builder -> final bundle validation -> retained governed artifacts`.

The M8R-03C bundle builders remain source-agnostic. Network execution is confined to `scripts/m8r_03d_watchlist_controlled_executor.py` and is not enabled by default.

## Authorization model

Authorization schema: `m8r_03d_watchlist_execution_authorization.v1`.

The authorization is bound to the canonical SHA-256 hash of the validated evidence request JSON using sorted-key compact JSON. It also requires a non-empty `authorization_id` and `one_shot_nonce`, and is bounded by bundle type, non-empty target IDs, source families, maximum target count, expiry, and safety flags. Required safety flags are: `network_execution_allowed=true`, `one_shot_only=true`, `polling_allowed=false`, `scheduler_allowed=false`, `persistent_storage_allowed=false`, and `raw_payload_retention_allowed=false`.

An authorization for one request hash cannot execute a modified request. Expired authorizations, malformed timestamps, empty or duplicate authorization arrays, unknown authorization fields, unauthorized targets, unauthorized sources, unauthorized bundle types, polling/scheduler flags, and raw-retention permission are rejected before controlled execution. Execute mode atomically claims the authorization/nonce in a fixed governed filesystem-backed consumption receipt root before source calls; the receipt root is independent of `--artifact-root`, so changing artifact output directories cannot bypass replay protection. A second use fails with `authorization_replayed`. Preflight and fixture modes do not consume authorization.

## Execution modes

- `--mode preflight`: validates the request, resolves identities and source routes, builds a deterministic plan, reports source call groups, performs no network calls, and writes no observations.
- `--mode fixture`: uses local source-response fixtures, performs no network calls, normalizes observations, builds and validates snapshot or performance bundles, and writes governed artifacts.
- `--mode execute`: requires valid authorization and performs one bounded execution against approved source families only.

The CLI rejects `--poll`, `--schedule`, `--watch`, and `--continuous`.

## Source scope

Current/snapshot source family: `TWSE_MIS`.

EOD/performance source families: `TWSE_OPENAPI` and `TPEX_OPENAPI`.

TPEx/OTC current observations use the already-approved TWSE MIS OTC route (`otc_{symbol}.tw`). No `TPEX_MIS` family is introduced. TAIFEX, MOPS, broker APIs, market pulse, public APIs, MCP, frontend, polling, and persistent watchlist storage remain out of scope.

## Identity and route resolution

Targets are retained in request order. Supported IDs are explicit `TWSE:{code}` and `TPEX:{code}` watchlist IDs from the M8R-03C request, but the prefix is not treated as authoritative identity. Planning resolves each target through the governed security-master/classifier path into `target_id`, `security_code`, `security_name`, `canonical_market`, `instrument_type`, `listing_status`, `lifecycle_state`, `resolution_status`, and `resolution_evidence`. TWSE targets plan `TWSE_MIS` current route `tse_{symbol}.tw` and `TWSE_OPENAPI` EOD. TPEx targets plan `TWSE_MIS` current route `otc_{symbol}.tw` and `TPEX_OPENAPI` EOD.

Unknown identities remain target-local when other targets are valid; no source calls are planned for them. Market-prefix conflicts become `market_mismatch`, inactive securities become `lifecycle_unsupported`, unsupported instruments become `unsupported_instrument`, cross-market duplicate conflicts become `identity_conflict`, and these blocking issues stop fixture and execute modes before source invocation. Current repository classifier lookup may provide identity and classification without lifecycle evidence; missing lifecycle evidence is recorded as `lifecycle_state=unknown` and `lifecycle_resolution_status=unavailable`, permits interim `execution_allowed_with_caveat`, and must not be described as active. Explicit inactive lifecycle evidence supplied by an injected or future canonical lifecycle-aware master remains blocking.

## Safe-field normalization

`normalize_twse_mis_watchlist_observation`, `normalize_twse_openapi_watchlist_observation`, and `normalize_tpex_openapi_watchlist_observation` convert governed adapter outputs into `m8r_watchlist_input_observation.v1` and validate before bundling.

TWSE MIS safe fields are bounded to latest price, change, change percent, open, high, low, volume, close, and no-trade state. EOD safe fields are bounded to open, high, low, close, volume, trade date, and latest price. Raw payloads, headers, cookies, sessions, authorization material, `msgArray`, browser frames, option chains, and arbitrary endpoint dumps are rejected.

## Currentness and EOD semantics

TWSE MIS normalization preserves source timestamp separately from `retrieved_at_utc`. `retrieved_at_utc` is never treated as exchange time. Stale or unresolved currentness maps into partial snapshot coverage via the M8R-03C builder's currentness missing-evidence logic.

TWSE_OPENAPI and TPEX_OPENAPI observations use `trade_date` as official completed EOD date. Snapshot bundles select the latest supplied EOD reference. Performance bundles use bounded sorted EOD rows, deduplicate deterministic duplicate dates, and fail on contradictory duplicate facts through the M8R-03C builder.

## History window and batch limits

The plan records bounded history needs for performance requests. A 20-trading-day request requires at least 21 valid closes plus a five-trading-day buffer marker. Target count is limited to 10 for this watchlist execution path; over-limit requests fail preflight rather than being silently truncated.

## Partial coverage behavior

Per-target and per-source failures do not remove other targets. Execute mode records each source call group with source family, target IDs, start/completion timestamps, status, observation count, and reason code. If one group fails, other authorized groups continue and bundles are built from successful observations. If all source groups fail and no observations are retained, the result is `source_execution_failed`; otherwise partial evidence returns `success_with_partial_coverage`. Source identity is checked against the planned security code and documented market aliases before normalization; mismatches fail target/source closed with `source_identity_mismatch`.

## Artifact retention

Run artifacts are written under `artifacts/m8r_03d/<run_id>/` or a caller-provided bounded artifact root. Retained artifacts are authorization, validated request, execution plan, normalized observations, snapshot/performance bundle, and execution result. Raw HTTP payloads, browser frames, cookies, credentials, authorization headers, and complete endpoint dumps are forbidden.

## CLI usage

```bash
python scripts/run_m8r_03d_watchlist_controlled_execution.py \
  --request tests/fixtures/m8r_03c/snapshot_request.json \
  --mode fixture \
  --bundle-type snapshot \
  --fixture-source-data tests/fixtures/m8r_03d/snapshot_source_data.json
```

Controlled live validation requires `--mode execute` and a valid authorization JSON bound to the exact request hash.

## Controlled live validation procedure

Live validation is manual, one-shot, and outside default CI. The operator must prepare an authorization with the exact canonical request hash, authorization ID, one-shot nonce, authorized source families, authorized targets, max target count, expiry, and all safety flags. A failed live execution consumes the nonce after successful validation and atomic claim; retry requires a new authorization/nonce so replay cannot silently repeat network calls. No live validation was executed in this task because no explicit authorization was supplied.

## Known caveats

- Live validation is not completed.
- Full lifecycle verification is not completed; it remains a bounded follow-up tied to integrating a verified external lifecycle-aware security-master/classifier snapshot. The current implementation only uses repository classifier evidence and injected test masters, and does not infer active lifecycle from absent evidence.
- TPEx current coverage is limited to the already-approved TWSE MIS OTC route.
- Performance metrics use unadjusted EOD closes supplied by official EOD adapters or fixtures.
- There is no persistent watchlist database, scheduler, polling, frontend, MCP, public API, notification, broker, order, or M8R-04 implementation.

## GO/NO-GO criteria

Decision: `GO_WITH_CAVEATS`.

Fixture execution covers the complete integration path, controlled execution is authorization-bound and bounded, normalized observations validate, snapshot and performance bundles validate, default tests remain non-network, and raw retention is blocked. Full `GO` requires an explicitly authorized successful live validation.

## Next task recommendation

Recommended next bounded task: `M8R-03E-WATCHLIST-AI-CONTEXT-PACKAGE-AND-CONVERSATION-HANDOFF`.
