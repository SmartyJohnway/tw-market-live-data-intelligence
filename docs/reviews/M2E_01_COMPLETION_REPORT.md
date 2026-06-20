# M2E-01 Completion Report

## Final Status
`M2E_01_COMPLETED`

## Files Changed
* `docs/protocol/TARGET_TAXONOMY.md` (new)
* `docs/protocol/SYMBOL_FORMAT_REGISTRY.md` (new)
* `docs/protocol/SOURCE_TARGET_SUPPORT_MATRIX.md` (new)
* `docs/protocol/SUPPORT_STATUS_SEMANTICS.md` (new)
* `docs/protocol/TARGET_CONFIG_SCHEMA_DRAFT.md` (new)
* `docs/capability_matrix.md` (updated via generator)
* `docs/source_catalog.md` (updated via generator)
* `frontend/public/matrix.json` (updated via generator)
* `research/generated/ai_context_pack.md` (updated via generator)
* `research/generated/ai_context_pack.json` (updated via generator)
* `research/probe_log.md` (updated via generator)
* `README.md` (updated with cross-references)

## Validation Commands Executed
* `python -m pip install -r requirements.txt`
* `python -m compileall scripts server tests`
* `pytest -m "not network" -v`
* `python scripts/run_all_probes.py`

## Terminal Output Summary
* `pytest`: 50 passed in 3.10s. No test failures.
* `run_all_probes.py`: All probes ran successfully, generating reports cleanly. No transient network errors or parser failures observed.
* `compileall`: Finished with zero errors.

## Target Taxonomy Summary
Created a canonical target taxonomy featuring `twse_common_stock`, `tpex_common_stock`, `twse_etf`, `tpex_etf`, `twse_tdr`, `twse_index`, `tpex_index`, `taifex_index_future`, `taifex_stock_future`, `mutual_fund`, `foreign_stock_or_adr`, `broker_account_target`, and `unknown_or_unsupported`. Each class includes definitions, examples, and capabilities.

## Symbol Format Registry Summary
Created a symbol format registry detailing how assets like `2330` (台積電) or `TAIEX` are represented differently across TWSE MIS, Yahoo Finance, TWSE OpenAPI, TPEx OpenAPI, FinMind, and broker APIs. Fallback formats like `candidate` and `unsupported` are strictly defined.

## Source-Target Support Matrix Summary
Created a comprehensive matrix mapped against the new taxonomy. Official OpenAPI sources are strictly capped at EOD capabilities for their specific exchanges. TWSE MIS is kept bounded. Yahoo Finance capabilities reflect specific placeholder support levels (e.g., `TX.TW` mapped as `observed_unsupported`).

## Support Status Semantics Summary
Defined a rigorous vocabulary for the support matrix: `supported_observed`, `supported_candidate`, `observed_unsupported`, `unsupported`, `auth_required`, `doc_only`, `unknown`, and `deferred`. These explicitly prevent AI hallucination or the creation of unverified API capabilities.

## Config Change Summary
**Rationale:** M2E-01 intentionally leaves `config/market_targets.json` unchanged to avoid changing probe behavior during a documentation-first taxonomy milestone. A backward-compatible target config schema is proposed in `TARGET_CONFIG_SCHEMA_DRAFT.md` for a future M2E-02 implementation task.

## Tests Added
**Rationale:** No code or config behavior changed in M2E-01, so no new offline tests were added. Existing validation commands were still executed.

## Remaining Caveats
* Symbol formats for broker APIs remain largely documentation-only / candidate-level without valid authenticated access.
* TAIFEX futures and mutual funds require dedicated source implementations outside the current repo scope.

## Deferred M2E-02 / M3 / M4 Items
* Migrating `config/market_targets.json` to the schema proposed in `TARGET_CONFIG_SCHEMA_DRAFT.md` (M2E-02).
* Building runtime validation of the config schema.
* Developing comprehensive AI context pack protocols (M3).

## Next Milestone Recommendation
`M2E-02-TARGET-CONFIG-SCHEMA-AND-VALIDATION`
