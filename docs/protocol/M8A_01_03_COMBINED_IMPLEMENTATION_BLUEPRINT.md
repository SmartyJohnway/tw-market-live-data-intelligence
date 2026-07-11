# M8A-01-03 combined implementation blueprint

Status: m8a_00_official_eod_adapter_scope_and_contract_preflight_complete
Generated: 2026-07-11T10:24:35Z
Next task: M8A-01-03-OFFICIAL-EOD-ADAPTERS-CONTEXT-INTEGRATION-AND-FINAL-ACCEPTANCE


Target task: `M8A-01-03-OFFICIAL-EOD-ADAPTERS-CONTEXT-INTEGRATION-AND-FINAL-ACCEPTANCE`.

## Commit 1 — adapters and normalized schema implementation
Create shared normalized observation helper/model, TWSE parser, TPEx parser, source-specific mappings, deterministic fixture loader support. Suggested files: `scripts/m8a_official_eod_observation.py`, `scripts/m8a_twse_official_eod_adapter.py`, `scripts/m8a_tpex_official_eod_adapter.py`. No runtime endpoint yet.

## Commit 2 — fixtures, contract tests, and failure handling
Add curated official-response fixtures, parser tests, no-trade/suspended/null cases, invalid numeric, schema drift, empty/non-trading-day, failure isolation, provenance tests. Default CI no-network only.

## Commit 3 — M8 context and controlled runtime integration
Map adapter output to M8 multi-source observations, update registry runtime status, integrate M8 freshness, preserve same-symbol live-ish + EOD context, add explicit bounded operator-triggered execution helper `scripts/m8a_official_eod_execution.py`. No scheduler/polling/startup fetch.

## Commit 4 — conversation integration, bounded evidence, inventory, final acceptance
Project official EOD into AI-readable conversation context with trade_date/currentness/provenance, perform bounded live validation, compatibility regression, inventory closure, M8A final acceptance doc, next-track recommendation.

## Runtime integration options
Option A: extend M7G controlled refresh execution framework. Pro: reuses operator controls. Con: live-ish MIS symbol-bounded behavior differs from official whole-market EOD latest arrays.

Option B: create separate M8A controlled official EOD execution helper. Pro: clean EOD failure/currentness contract and whole-market-network/bounded-output distinction. Con: one more helper.

Option C: shared generic controlled source execution framework. Pro: best long-term abstraction. Con: too large for M8A-01-03.

Recommendation: Option B now, shaped for later Option C.

## Future execution result proposal
```json
{"schema_version":"m8a_official_eod_execution_result.v1","requested_sources":[],"requested_symbols":[],"requested_trade_date":null,"started_at_utc":"...","completed_at_utc":"...","source_results":[],"normalized_observations":[],"safe_projection_scope":{},"overall_status":"success|partial_success|failed","caveats":[]}
```

## Whole-market network response handling
Selected endpoints return whole-market/latest arrays. It is acceptable to fetch one official whole-market response per source per explicit execution, then immediately filter to bounded requested symbols for retained artifacts/context. Do not call the network request symbol-bounded. Do not retain full response by default. The execution helper must compute expected latest completed Taiwan trading date from the accepted calendar/session foundation and compare each source reported trade_date before marking official EOD context current; mismatches remain stale/reference context with reconciliation caveats.

## Context mapping
Map to M8 fields: source_id, source_family, symbol, name, market, instrument_type, context_type, safe_fields, omitted_fields, source_timestamp, retrieved_at_utc, market_date, trading_date, session_state, source_unavailable, source_unavailable_reason, value_status, validation_status, caveats. Context types: `official_equity_eod_reference`, `official_etf_eod_reference`, `official_market_eod_reference`.

## Expected-file matrix
| path | purpose | commit | new_or_modified | runtime_behavior | network_behavior | test_coverage |
|---|---|---:|---|---|---|---|
| scripts/m8a_official_eod_observation.py | shared schema/parser helpers | 1 | new | pure | none | schema tests |
| scripts/m8a_twse_official_eod_adapter.py | TWSE parser/fetch function boundary | 1 | new | no endpoint integration | fetch function only when called | TWSE parser tests |
| scripts/m8a_tpex_official_eod_adapter.py | TPEx parser/fetch function boundary | 1 | new | no endpoint integration | fetch function only when called | TPEx parser tests |
| tests/fixtures/m8a_official_eod/* | curated fixtures | 2 | new | none | none | default-ci |
| scripts/m8a_official_eod_execution.py | explicit operator execution helper | 3 | new | manual only | one whole-market request/source/action | runtime tests |
| scripts/m8_multi_source_context_builder.py | map official EOD observations | 3 | modified | controlled context only | none | builder tests |
| scripts/m8_controlled_conversation_context.py | project safe official EOD context | 4 | modified | controlled context only | none | projection tests |
| docs/data_capabilities/* | inventory/final registry | 4 | modified | none | none | contract tests |
