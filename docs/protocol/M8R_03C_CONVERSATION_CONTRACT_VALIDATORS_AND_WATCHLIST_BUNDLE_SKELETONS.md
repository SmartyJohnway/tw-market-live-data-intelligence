# M8R-03C Conversation Contract Validators and Watchlist Bundle Skeletons

Status: `GO_WITH_CAVEATS_non_network_contract_validators_and_watchlist_bundle_skeletons_completed`.

## Scope

M8R-03C implements runtime validators and deterministic watchlist bundle builders for the M8R-03B design contracts. It does not fetch TWSE, TPEx, TAIFEX, broker, browser, or commercial sources. Source execution remains external input.

Implemented layers:

1. canonical contract loading from the M8R-03B JSON artifacts;
2. runtime validators for conversation intent, evidence request, watchlist requests, and bundle envelopes;
3. non-network watchlist snapshot and performance bundle skeleton builders;
4. fixture CLI for deterministic local execution.

Not implemented: network adapters, polling, scheduler, background storage, MCP/API/frontend surfaces, market pulse automation, dynamic research execution, broker integration, alerts, order creation, or M8R-04.

## Architecture

Dependency direction is:

```text
design contracts -> runtime validators -> bundle builders -> validated bundle output
```

The bundle builders accept already-normalized `m8r_watchlist_input_observation.v1` records and never import or call production source adapters.

## Canonical contract loading

`scripts/m8r_03c_contracts.py` loads:

- `docs/data_capabilities/m8r_03b_conversation_scope_contract.json`
- `docs/data_capabilities/m8r_03b_evidence_bundle_contracts.json`

It fails closed for missing files, invalid JSON, unsupported contract schema versions, missing required sections, duplicate field definitions, unknown field type declarations, and invalid enum declarations. Runtime metadata accessors expose scope modes, time modes, evidence depth modes, calculation statuses, and coverage states derived from the canonical artifacts.

Supported design schema versions:

- `m8r_03b_conversation_scope_contract.v2`
- `m8r_03b_evidence_bundle_contracts.v2`

Supported runtime schemas include the M8R-03B conversation/evidence/watchlist bundle schemas plus the bounded internal `m8r_watchlist_input_observation.v1` envelope.

## Validator behavior

`scripts/m8r_03c_conversation_contract_validator.py` provides reusable public functions:

- `validate_conversation_intent`
- `validate_evidence_request`
- `validate_watchlist_snapshot_request`
- `validate_watchlist_performance_request`
- `validate_watchlist_snapshot_bundle`
- `validate_watchlist_performance_bundle`

Validators return normalized deep copies and do not mutate caller-owned input. Failures raise `M8R03CValidationError` with stable `code`, `path`, and `detail` attributes.

## Unknown-field policy

Strict contract objects fail closed on unknown fields, including conversation intent, evidence request, time scope, explicit range, watchlist reference, dynamic entity request, execution policy, follow-up context, coverage records, derived metric records, missing evidence records, and bundle envelopes.

Extensible maps are allowed only where the contract intentionally carries caller- or resolver-provided data, including `explicit_user_constraints`, `inferred_defaults`, `identity_resolver_output`, `conversation_context`, `source_summary`, and normalized `facts` values.

## Watchlist snapshot skeleton

`build_watchlist_snapshot_bundle` validates the evidence request, rejects clarification-required requests, groups supplied observations by target, and represents every enabled watchlist target exactly once in request order.

Source separation:

- current evidence: `TWSE_MIS` or `TAIFEX_MIS` / `liveish_observation`;
- EOD reference: `TWSE_OPENAPI`, `TPEX_OPENAPI`, `TAIFEX_OPENAPI`, or fixture benchmark-style EOD observations where applicable.

Coverage states:

- `usable`: resolved identity, current evidence, currentness metadata, and EOD reference are present;
- `partial`: at least one useful source or identity exists, but one or more field groups are missing or stale;
- `unavailable`: identity or usable source observation is absent.

Missing evidence is recorded as structured records instead of silently dropping targets.

## Watchlist performance skeleton

`build_watchlist_performance_bundle` validates recent/historical/explicit/current-plus-recent watchlist requests, accepts EOD/precomputed fixture observations, sorts rows by effective trade date, deduplicates identical target/date rows, and rejects contradictory duplicates.

Metrics are emitted in canonical registry order and include formula metadata, source dependencies, calculation status, and `as_of`.

## Metric formulas and assumptions

`scripts/m8r_03c_watchlist_metrics.py` defines the governed initial formulas:

- `return_Nd = latest_valid_close / close_N_trading_rows_ago - 1`
- `range_high = max(valid high/close over input rows)`
- `range_low = min(valid low/close over input rows)`
- `range_position = (latest_close - range_low) / (range_high - range_low)`
- `drawdown_from_recent_high = latest_close / range_high - 1`
- `average_volume = mean(valid volume over input period)`
- `volume_ratio = latest_volume / average_volume_prior_window`
- `realized_volatility = sample standard deviation of daily log returns`
- `relative_return_vs_market = target return_Nd - supplied benchmark return_Nd`

Price metrics use source-provided unadjusted closes unless future source observations explicitly document adjustment. Missing values, zero denominators, and insufficient history produce `input_unavailable`; metrics are not silently omitted. Benchmark-relative returns are calculated only when benchmark fixture rows are explicitly supplied; otherwise the metric is `formula_not_applicable`.

## Fact, derived, assumption, and missing-evidence boundaries

Facts remain source-normalized values under `facts` and per-target source sections. Derived metrics are separate records under `derived_metrics`. Resolution assumptions record calculation and selection assumptions. Missing evidence records absent or insufficient inputs. Tests guard against derived metric identifiers being inserted into source fact maps.

## Safety and retention

Recursive forbidden-key checks fail closed for raw or secret-bearing fields including `raw_payload`, `raw_rest_records`, `full_option_chain`, `option_chain`, `sockjs_frames`, cookies, session IDs, authorization headers, and access/refresh tokens. The fixture CLI rejects URL/network/polling/scheduler inputs.

## Non-network CLI

`scripts/run_m8r_03c_watchlist_bundle_fixture.py` reads an evidence request JSON file and a normalized observation JSON file, builds either a snapshot or performance bundle, validates the bundle, and writes deterministic JSON output.

Required flags:

```bash
--request --observations --bundle-type snapshot|performance --output
```

## Test matrix

Unit tests cover contract loader fail-closed behavior, enum synchronization, conversation invariants, evidence request invariants, strict versus extensible unknown fields, raw-key rejection, snapshot usable/partial/unavailable states, source separation, performance metric calculation, insufficient-history statuses, duplicate-date conflict rejection, benchmark behavior, fact/derived separation, and CLI determinism.

Fixtures in `tests/fixtures/m8r_03c/` cover usable snapshot, partial snapshot, stale currentness, unavailable target through request expansion, complete performance history, insufficient history, duplicate-date conflict, benchmark supplied, and benchmark absent.

## Known limitations

- No live source execution is implemented.
- Benchmark-relative return is limited to explicitly supplied fixture/observation series.
- Price adjustment and dividend handling are not implemented; metrics are not total-return metrics.
- TAIFEX watchlist performance is not production-integrated.
- No persistent watchlist storage or public product surface is introduced.

## Decision

M8R-03C is `GO_WITH_CAVEATS`: non-network validators and watchlist bundle skeletons pass local fixture validation, while production source integration remains a separate bounded task.

## Next bounded task

Recommended next task: `M8R-03D-WATCHLIST-EVIDENCE-SOURCE-INTEGRATION-AND-CONTROLLED-EXECUTION`.

Rationale: M8R-03C proves request/bundle structure and non-network safety. The next bounded step should connect already-governed source execution to the watchlist evidence path under explicit controls, without claiming market pulse, dynamic research, or M8R-04 completion.
