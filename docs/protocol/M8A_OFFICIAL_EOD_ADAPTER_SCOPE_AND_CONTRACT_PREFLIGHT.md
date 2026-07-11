# M8A official EOD adapter scope and contract preflight

Status: m8a_00_official_eod_adapter_scope_and_contract_preflight_complete
Generated: 2026-07-11T10:24:35Z
Next task: M8A-01-03-OFFICIAL-EOD-ADAPTERS-CONTEXT-INTEGRATION-AND-FINAL-ACCEPTANCE


## 1. Purpose
Establish endpoint truth, contract truth, normalized schema, failure/currentness behavior, runtime architecture, and go/no-go decisions for official TWSE and TPEx EOD/reference context. This PR is preflight only: no production adapter, no runtime fetching, no server/frontend/MCP change, no scheduler, no polling, no DB write.

## 2. Accepted M8 upstream
Accepted upstream includes M7G controlled TWSE_MIS refresh plus M8-00 timing, authority, freshness, registry, multi-source context, controlled conversation projection, and final acceptance `m8_00_final_acceptance_pass_with_caveats`. Repository review covered M8 protocol docs, source registry, freshness evaluator, multi-source builder, controlled conversation context, legacy OpenAPI normalizer tests, source contract tests, authority registry, and coverage matrix.

## 3. Research method and evidence hierarchy
Evidence order: official Swagger/OpenAPI specs, bounded direct official endpoint probes, official examples/terms, current repository contracts, secondary references only if official evidence is incomplete. Official TWSE docs checked: `https://openapi.twse.com.tw/v1/swagger.json` and Swagger UI root. Official TPEx docs checked: `https://www.tpex.org.tw/openapi/` and `https://www.tpex.org.tw/openapi/swagger.json`.

## 4. Existing repository capability review
Existing assumptions use `https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL` and `https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes`. Legacy normalizers parse row-level EOD fields and retain raw rows; they are useful references but should be superseded for M8A by a raw-payload-free normalized observation model. No contradiction with M8 registry: OpenAPI remains official EOD/reference, not realtime. Existing default-ci includes legacy normalizer and M8 final acceptance tests.

## 5. TWSE endpoint candidates
Preferred: `twse_openapi_stock_day_all_v1`, official TWSE Swagger path `/exchangeReport/STOCK_DAY_ALL`, GET, no auth, JSON array, no pagination observed, no date parameter documented, latest available listed-market daily rows. Rejected for core: `/exchangeReport/MI_INDEX` because it is index-level data, not security OHLC rows. Historical-by-date TWSE products were not selected because this OpenAPI path directly covers the required core current/latest official EOD row set and avoids adding a separate monthly/historical contract in this preflight.

## 6. TPEx endpoint candidates
Preferred: `tpex_openapi_mainboard_daily_close_quotes_v1`, official TPEx Swagger path `/v1/tpex_mainboard_daily_close_quotes`, GET, no auth, JSON array, latest available OTC mainboard daily close quote rows. Rejected for core: `tpex_esb_latest_statistics` because it is emerging-stock/latest statistics coverage and out of M8A runtime scope.

## 7. Selected endpoint contracts
Selected TWSE endpoint: `https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL`. Selected TPEx endpoint: `https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes`. Both are official, accessible with HTTP 200, application/json, top-level array responses, and bounded evidence artifacts.

## 8. Probe matrix and results
Probes captured latest omitted-date behavior and invalid/extra date parameter behavior. TWSE latest probe observed 1369 rows with Date `1150709`. TPEx latest probe observed 10093 rows with Date `1150709`. Invalid `date=invalid` query parameters were ignored by both selected endpoints, confirming they should not be modeled as requested-date endpoints. Weekend/non-trading-day by request is not supported by selected endpoints; classify by latest reported trade_date and exchange calendar instead.

## 9. Field-by-field contract summary
See `docs/data_capabilities/m8a_official_eod_field_mapping.csv`. Core shared fields are symbol, name, trade_date, open, high, low, close, change, trade_volume, trade_value, transaction_count, currency, source status, and observation status. Previous close is not source-reported; it may be derived as close minus change when both are valid. Change percent is deferred by default.

## 10. Units and date semantics
Dates are ROC `yyyMMdd` in source rows and must normalize to Gregorian `YYYY-MM-DD`. Prices and change are TWD per unit Decimal-compatible values. Volume is shares or beneficial units as reported by each security class. Trade value is TWD. Transaction count is trade count. Retrieval time records fetch time only and must not be treated as trade time.

## 11. Instrument coverage
TWSE row instrument type is not explicit; observed rows include common stocks and ETFs/active ETFs. TPEx observed row count and fields indicate mixed instruments beyond common OTC equities are possible. ETFs are included; warrants/bonds/other rows require classification before AI context/deterministic metrics. Emerging-stock endpoint is explicitly rejected and not runtime-authorized.

## 12. Canonical identity
Canonical instrument identity: `(market, symbol)`. Market values: `listed` and `tpex_otc`. Symbol alone can collide across markets. When security-master classification is unavailable, row may be retained as unclassified partial evidence with caveat but must not enter deterministic metrics or AI context unless policy allows.

## 13. Shared normalized schema decision
Decision: `accepted_with_source_extensions`. One shared adapter output schema is feasible with source-specific endpoint contracts, parsers, and field mappings. Blocking differences: none. Non-blocking differences: TPEx extra fields and mixed coverage; TWSE/TPEx field names differ.

## 14. Failure/currentness/non-trading-day contract
See `docs/protocol/M8A_OFFICIAL_EOD_FAILURE_CURRENTNESS_AND_NON_TRADING_DAY_CONTRACT.md`. Required distinctions include `empty_non_trading_day`, `source_unavailable`, `source_error`, `schema_drift`, `date_mismatch`, `valid_zero_trade_row`, `successful_eod_batch`, and `partial_source_success`.

## 15. Runtime integration options
Option A extends M7G controlled refresh. Option B creates a separate M8A controlled EOD execution helper. Option C creates a generic controlled source execution framework.

## 16. Selected implementation architecture
Recommendation: Option B for M8A-01-03, with interfaces shaped for later Option C. Reason: official EOD whole-market fetch, latest-date semantics, parser/failure behavior, and bounded output differ materially from M7G live-ish TWSE_MIS refresh. Do not overload M7G in the next PR.

## 17. Combined PR implementation blueprint
See `docs/protocol/M8A_01_03_COMBINED_IMPLEMENTATION_BLUEPRINT.md`. Commit 1 adapters/schema; Commit 2 fixtures/tests/failure; Commit 3 M8 controlled runtime integration; Commit 4 conversation projection/evidence/final acceptance.

## 18. Test and fixture strategy
See `docs/protocol/M8A_OFFICIAL_EOD_TEST_AND_FIXTURE_STRATEGY.md`. Default CI remains no-network fixture tests. Live validation is explicit/manual only.

## 19. Go / no-go matrix
TWSE endpoint readiness: go. TPEx endpoint readiness: conditional_go. TWSE field contract: go. TPEx field contract: conditional_go. Shared normalized schema: accepted_with_source_extensions. Controlled runtime design: accepted. Combined implementation PR feasible: yes.

## 20. Known caveats
Selected endpoints expose latest available official daily arrays, not requested historical dates. Instrument classification is not explicit in rows. TPEx mixed instrument handling must fail closed for deterministic metrics and AI context. No full raw payloads are committed.

## 21. Explicit non-goals
No production adapter, runtime fetch, FastAPI, frontend, MCP, scheduler, polling, startup fetch, DB write, TAIFEX, MOPS, TPEX_MIS, rotc_, emerging-stock live route, M8A final acceptance, or broad semantic filter expansion.

## 22. Final result
Final result: `pass_with_caveats`.

## 23. Next task
`M8A-01-03-OFFICIAL-EOD-ADAPTERS-CONTEXT-INTEGRATION-AND-FINAL-ACCEPTANCE`.
