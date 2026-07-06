# Validated Endpoint Data Capability Inventory

## Executive summary

This inventory includes validated runtime sources, validated contracts/probes, validated historical workbench sources, catalogued candidates, and credential-gated providers. Not every listed source family is a validated usable endpoint. The current product works, but the exposed live context remains thin because several raw fields are known while the parser/normalizer/consumers retain only selected facts. This report separates source availability, parser consumption, normalized retention, and consumer exposure before M7A/M7B/M7C/M7D/M7E implementation.

Evidence-status counts: {'validated_runtime_source': 11, 'validated_contract_or_probe': 4, 'validated_historical_workbench': 1, 'credential_gated_provider': 2}

## Source-family summary

| source_id | evidence_status | availability_status | authority_class | timing_class | runtime_integrated | candidate_milestone |
|---|---|---|---|---|---|---|
| TWSE_MIS | validated_runtime_source | implemented_normalized_now | official_browser_json_candidate | live_or_intraday | True | M7A_rich_mis_observation_contract |
| TAIFEX_MIS | validated_runtime_source | implemented_normalized_now | official_browser_json | live_or_intraday | True | M7A_rich_mis_observation_contract |
| TWSE_OpenAPI | validated_contract_or_probe | implemented_probe_or_contract_now | official_openapi | end_of_day | False | M7C_official_eod_context_expansion |
| TPEx_OpenAPI | validated_contract_or_probe | implemented_probe_or_contract_now | official_openapi | end_of_day | False | M7C_official_eod_context_expansion |
| TAIFEX_OpenAPI | validated_contract_or_probe | implemented_docs_only | official_openapi | official_statistical | False | M7_or_M8_decision_pending |
| Yahoo_Finance | validated_contract_or_probe | implemented_probe_or_contract_now | unofficial_api | historical | False | M7D_optional_third_party_historical_context |
| FinMind | validated_historical_workbench | validated_historical_workbench | commercial_api | historical | False | M7D_optional_third_party_historical_context |
| Fugle_MarketData | credential_gated_provider | credential_gated_not_usable_now | commercial_api | credential_dependent | False | M7E_credential_gated_provider_research |
| Fubon_Neo_API | credential_gated_provider | credential_gated_not_usable_now | broker_api | credential_dependent | False | M7E_credential_gated_provider_research |
| Local_M5F_canonical_context | validated_runtime_source | implemented_normalized_now | local_generated_artifact | local_static_context | True | M7C_official_eod_context_expansion |
| Local_M5K_latest_observation | validated_runtime_source | implemented_normalized_now | local_generated_artifact | live_or_intraday | True | M7A_rich_mis_observation_contract |
| Local_M5K_observation_history | validated_runtime_source | implemented_probe_or_contract_now | local_generated_artifact | historical | True | M7B_market_context_package_and_ai_markdown |
| M5N_watchlist_conversation_handoff | validated_runtime_source | implemented_normalized_now | local_generated_artifact | local_static_context | True | M7B_market_context_package_and_ai_markdown |
| M5Q_source_health_report | validated_runtime_source | implemented_probe_or_contract_now | local_generated_artifact | source_health_probe | True | M7B_market_context_package_and_ai_markdown |
| FastAPI_context_endpoints | validated_runtime_source | implemented_normalized_now | local_generated_artifact | local_static_context | True | M7B_market_context_package_and_ai_markdown |
| FastAPI_live_observation_endpoints | validated_runtime_source | implemented_normalized_now | local_generated_artifact | live_or_intraday | True | M7A_rich_mis_observation_contract |
| FastAPI_conversation_context_endpoint | validated_runtime_source | implemented_normalized_now | local_generated_artifact | local_static_context | True | M7B_market_context_package_and_ai_markdown |
| MCP_server_exposed_resources_tools | validated_runtime_source | implemented_normalized_now | local_generated_artifact | local_static_context | True | M7B_market_context_package_and_ai_markdown |

## Source taxonomy summary

| category | source_ids |
|---|---|
| external_runtime_sources | TWSE_MIS, TAIFEX_MIS |
| official_eod_contract_sources | TWSE_OpenAPI, TPEx_OpenAPI, TAIFEX_OpenAPI |
| unofficial_or_commercial_contract_sources | Yahoo_Finance, FinMind |
| credential_gated_providers | Fugle_MarketData, Fubon_Neo_API |
| local_product_surfaces_or_artifacts | Local_M5F_canonical_context, Local_M5K_latest_observation, Local_M5K_observation_history, M5N_watchlist_conversation_handoff, M5Q_source_health_report, FastAPI_context_endpoints, FastAPI_live_observation_endpoints, FastAPI_conversation_context_endpoint, MCP_server_exposed_resources_tools |

## Current architecture map

- Local canonical context: M5F local artifacts are read through FastAPI, frontend, MCP, and conversation context.
- Live bounded observation: M5K runtime sources currently include TWSE MIS and TAIFEX MIS, but this inventory did not execute them.
- Conversation context: M5N composes selected latest observation fields, source-health summaries, and canonical context without raw payload handoff.
- Source health: M5Q stores normalized source-health reports, not raw endpoint payloads.
- Consumer exposure is traced from code paths; artifact existence alone is not treated as frontend/MCP/conversation exposure.

## Source family inventory

### TWSE_MIS

- Evidence status: validated_runtime_source
- Runtime integrated: True; runtime exposure: exposed_in_fastapi, exposed_in_mcp, exposed_in_frontend, exposed_in_conversation_context, fetched_but_dropped
- Evidence files: scripts/m5k_common.py, scripts/observation_contract.py, config/m5l_live_source_adapter_matrix.json, docs/protocol/TWSE_MIS_FIELD_DICTIONARY.md, docs/protocol/TWSE_MIS_PROTOCOL.md
- Current normalized/retained fields: schema_version, symbol, display_symbol, category_id, instrument_type, status, source, adapter_id, market, source_type, price_like_value, value, price_semantics, source_timestamp, retrieved_at_utc, freshness_assessment, delay_status, delay_seconds, staleness_seconds, reference_only, contract, contract_month, contract_selector, data_quality_flags, source_risk_flags, caveats, price_source_field
- Raw/source fields known: c, ex, n, ch, z, y, o, h, l, v, tv, b, g, a, f, u, w, d, t, tlong, %, ot
- Dropped-field handling: See top-level dropped_field_decisions and field_inventory lifecycle rows; names alone are insufficient evidence.
- Evidence claims:
  - `twse_mis_raw_fields` (confirmed_from_contract): TWSE MIS raw field dictionary includes z/y/OHLC/volume/depth/time/channel fields. Evidence: docs/protocol/TWSE_MIS_FIELD_DICTIONARY.md; symbol/section: Raw field to normalized mapping.
  - `twse_mis_parser_reads` (confirmed_from_code): Current runtime parser reads z/y for price selection and d/t/tlong for timestamp/freshness; other rich fields are not independently retained. Evidence: scripts/m5k_common.py, scripts/observation_contract.py; symbol/section: _select_mis_price; normalize_twse_mis_row.
  - `twse_mis_consumers` (confirmed_from_code): FastAPI/MCP/frontend/conversation expose current normalized observation rows, but frontend/conversation render only selected row fields rather than every normalized key. Evidence: server/main.py, server/mcp_server.py, frontend/readonly-preview/m5k-workbench.js, scripts/m5k_common.py; symbol/section: /api/m5k/live-observation/latest; read_m5k_latest_live_observation; renderObservation; build_conversation_context.

### TAIFEX_MIS

- Evidence status: validated_runtime_source
- Runtime integrated: True; runtime exposure: exposed_in_fastapi, exposed_in_mcp, exposed_in_frontend, exposed_in_conversation_context, fetched_but_dropped
- Evidence files: scripts/m5k_common.py, scripts/observation_contract.py, config/m5l_live_source_adapter_matrix.json, docs/m5l_taifex_live_source_validation.md, docs/m5k_taifex_tx_futures_preflight.md
- Current normalized/retained fields: schema_version, symbol, display_symbol, category_id, instrument_type, status, source, adapter_id, market, source_type, price_like_value, value, price_semantics, source_timestamp, retrieved_at_utc, freshness_assessment, delay_status, delay_seconds, staleness_seconds, reference_only, contract, contract_month, contract_selector, data_quality_flags, source_risk_flags, caveats, source_status, normalization
- Raw/source fields known: CLastPrice, SettlementPrice, CRefPrice, CDate, CTime, Status, SymbolID, DispEName, DispCName
- Dropped-field handling: See top-level dropped_field_decisions and field_inventory lifecycle rows; names alone are insufficient evidence.
- Evidence claims:
  - `taifex_parser_reads` (confirmed_from_code): Current parser reads CLastPrice/SettlementPrice/CRefPrice, CDate/CTime, Status, SymbolID, DispEName, and DispCName for TX front-month normalization. Evidence: scripts/m5k_common.py, scripts/observation_contract.py; symbol/section: fetch_taifex_tx_observation; _select_taifex_tx_contract; normalize_taifex_row.
  - `taifex_no_ohlc_depth` (unknown): Repo evidence inspected here does not prove TAIFEX OHLC/volume/bid/ask fields in the current parser or contract. Evidence: scripts/m5k_common.py, scripts/observation_contract.py, docs/m5l_taifex_live_source_validation.md; symbol/section: normalize_taifex_row.

### TWSE_OpenAPI

- Evidence status: validated_contract_or_probe
- Runtime integrated: False; runtime exposure: docs_only, contract_known_but_not_implemented, normalized_but_not_exposed
- Evidence files: docs/contracts/twse_openapi_normalized_eod_quote_v1.md, docs/protocol/TWSE_OPENAPI_FIELD_DICTIONARY.md, docs/protocol/OFFICIAL_OPENAPI_SOURCE_SEMANTICS.md
- Current normalized/retained fields: trade_date, symbol, name, trade_volume, trade_value, open, high, low, close, change, transaction_count
- Raw/source fields known: Date, Code, Name, TradeVolume, TradeValue, OpeningPrice, HighestPrice, LowestPrice, ClosingPrice, Change, Transaction
- Dropped-field handling: See top-level dropped_field_decisions and field_inventory lifecycle rows; names alone are insufficient evidence.
- Evidence claims:
  - `twse_openapi_contract` (confirmed_from_contract): Official TWSE OpenAPI EOD contract includes trade date, symbol, name, volume/value, OHLC, close, change, transaction count. Evidence: docs/protocol/TWSE_OPENAPI_FIELD_DICTIONARY.md, docs/contracts/twse_openapi_normalized_eod_quote_v1.md; symbol/section: field dictionary.

### TPEx_OpenAPI

- Evidence status: validated_contract_or_probe
- Runtime integrated: False; runtime exposure: docs_only, contract_known_but_not_implemented, normalized_but_not_exposed
- Evidence files: docs/contracts/tpex_openapi_normalized_eod_quote_v1.md, docs/protocol/TPEX_OPENAPI_FIELD_DICTIONARY.md, docs/protocol/OFFICIAL_OPENAPI_SOURCE_SEMANTICS.md
- Current normalized/retained fields: trade_date, symbol, name, close, change, open, high, low, trade_volume, trade_value, transaction_count
- Raw/source fields known: Date, SecuritiesCompanyCode, CompanyName, Close, Change, Open, High, Low, Average, TradingShares, TransactionAmount, TransactionNumber, LatestBidPrice, LatesAskPrice, Capitals, NextReferencePrice, NextLimitUp, NextLimitDown
- Dropped-field handling: See top-level dropped_field_decisions and field_inventory lifecycle rows; names alone are insufficient evidence.
- Evidence claims:
  - `tpex_openapi_contract` (confirmed_from_contract): Official TPEx OpenAPI EOD contract includes close/change/OHLC/volume/value/transaction fields plus additional reference/bid/ask-like fields. Evidence: docs/protocol/TPEX_OPENAPI_FIELD_DICTIONARY.md, docs/contracts/tpex_openapi_normalized_eod_quote_v1.md; symbol/section: field dictionary.

### TAIFEX_OpenAPI

- Evidence status: validated_contract_or_probe
- Runtime integrated: False; runtime exposure: docs_only, contract_known_but_not_implemented
- Evidence files: docs/data_capabilities/taifex_openapi_endpoint_inventory.json, docs/protocol/TAIFEX_OPENAPI_PROTOCOL.md, docs/contracts/taifex_openapi_source_family_v1.md
- Current normalized/retained fields: None.
- Raw/source fields known: DailyMarketReportFut, DailyMarketReportOpt, PutCallRatio, MarketDataOfMajorInstitutionalTraders*, OpenInterestOfLargeTraders*, DailyForeignExchangeRates, FinalSettlementPrice, TimeAndSalesData, OptionsTimeAndSalesData
- Dropped-field handling: See top-level dropped_field_decisions and field_inventory lifecycle rows; names alone are insufficient evidence.
- Evidence claims:
  - `taifex_openapi_contract_preflight` (confirmed_from_contract): Official TAIFEX OAS metadata exposes derivative daily quote, statistical, reference, and historical/time-and-sales report endpoints; this source family is not runtime integrated and remains distinct from TAIFEX_MIS. Evidence: docs/data_capabilities/taifex_openapi_endpoint_inventory.json, docs/protocol/TAIFEX_OPENAPI_PROTOCOL.md; symbol/section: endpoint inventory.

### Yahoo_Finance

- Evidence status: validated_contract_or_probe
- Runtime integrated: False; runtime exposure: docs_only, contract_known_but_not_implemented
- Evidence files: docs/contracts/yahoo_finance_normalized_chart_v1.md, docs/protocol/YAHOO_FINANCE_CHART_PROTOCOL.md
- Current normalized/retained fields: symbol, regular_market_price, regular_market_time, open, high, low, close, volume
- Raw/source fields known: meta, timestamp, indicators.quote.open/high/low/close/volume, adjclose, chart.error
- Dropped-field handling: See top-level dropped_field_decisions and field_inventory lifecycle rows; names alone are insufficient evidence.
- Evidence claims:
  - `yahoo_chart_contract` (confirmed_from_contract): Yahoo chart contract documents meta, timestamp, quote arrays and error shape, but it is not activated as current runtime context. Evidence: docs/protocol/YAHOO_FINANCE_CHART_PROTOCOL.md; symbol/section: Response Shape.

### FinMind

- Evidence status: validated_historical_workbench
- Runtime integrated: False; runtime exposure: docs_only, contract_known_but_not_implemented
- Evidence files: docs/capability_matrix.md, docs/protocol/OFFICIAL_OPENAPI_SOURCE_SEMANTICS.md
- Current normalized/retained fields: None.
- Raw/source fields known: dataset-dependent
- Dropped-field handling: See top-level dropped_field_decisions and field_inventory lifecycle rows; names alone are insufficient evidence.
- Evidence claims:
  - `finmind_status` (confirmed_from_docs): FinMind is represented as historical/EOD workbench evidence with commercial/API caveats, not runtime observation. Evidence: docs/capability_matrix.md; symbol/section: FinMind row.

### Fugle_MarketData

- Evidence status: credential_gated_provider
- Runtime integrated: False; runtime exposure: docs_only
- Evidence files: docs/capability_matrix.md, config/m5l_live_source_adapter_matrix.json
- Current normalized/retained fields: None.
- Raw/source fields known: unknown_needs_credentials
- Dropped-field handling: See top-level dropped_field_decisions and field_inventory lifecycle rows; names alone are insufficient evidence.
- Evidence claims:
  - `fugle_status` (confirmed_from_docs): Fugle is credential-gated provider research only in current repo evidence. Evidence: docs/capability_matrix.md, config/m5l_live_source_adapter_matrix.json; symbol/section: Fugle rows.

### Fubon_Neo_API

- Evidence status: credential_gated_provider
- Runtime integrated: False; runtime exposure: docs_only
- Evidence files: docs/capability_matrix.md, config/m5l_live_source_adapter_matrix.json
- Current normalized/retained fields: None.
- Raw/source fields known: unknown_needs_broker_credentials
- Dropped-field handling: See top-level dropped_field_decisions and field_inventory lifecycle rows; names alone are insufficient evidence.
- Evidence claims:
  - `fubon_status` (confirmed_from_docs): Fubon is broker/API credential-gated provider research only in current repo evidence. Evidence: docs/capability_matrix.md, config/m5l_live_source_adapter_matrix.json; symbol/section: Fubon rows.

### Local_M5F_canonical_context

- Evidence status: validated_runtime_source
- Runtime integrated: True; runtime exposure: exposed_in_fastapi, exposed_in_mcp, exposed_in_frontend, exposed_in_conversation_context
- Evidence files: server/main.py, server/mcp_server.py, scripts/validate_m5f_canonical_market_context_package.py, README.md, docs/operator/LOCAL_WORKBENCH.md
- Current normalized/retained fields: governance, summary, content, caveats
- Raw/source fields known: local artifact fields
- Dropped-field handling: See top-level dropped_field_decisions and field_inventory lifecycle rows; names alone are insufficient evidence.
- Evidence claims:
  - `local_m5f_canonical_context_exposure` (confirmed_from_code): Local M5F canonical context is represented by explicit local code paths; exposure is based on returned/rendered code, not artifact existence alone. Evidence: server/main.py, server/mcp_server.py, scripts/validate_m5f_canonical_market_context_package.py; symbol/section: relevant endpoint/tool/render function.

### Local_M5K_latest_observation

- Evidence status: validated_runtime_source
- Runtime integrated: True; runtime exposure: exposed_in_fastapi, exposed_in_mcp, exposed_in_frontend, exposed_in_conversation_context
- Evidence files: scripts/m5k_common.py, server/main.py, server/mcp_server.py, frontend/readonly-preview/m5k-workbench.js, README.md, docs/operator/LOCAL_WORKBENCH.md
- Current normalized/retained fields: governance, summary, content, caveats
- Raw/source fields known: local artifact fields
- Dropped-field handling: See top-level dropped_field_decisions and field_inventory lifecycle rows; names alone are insufficient evidence.
- Evidence claims:
  - `local_m5k_latest_observation_exposure` (confirmed_from_code): Local M5K latest observation is represented by explicit local code paths; exposure is based on returned/rendered code, not artifact existence alone. Evidence: scripts/m5k_common.py, server/main.py, server/mcp_server.py, frontend/readonly-preview/m5k-workbench.js; symbol/section: relevant endpoint/tool/render function.

### Local_M5K_observation_history

- Evidence status: validated_runtime_source
- Runtime integrated: True; runtime exposure: exposed_in_fastapi, exposed_in_frontend
- Evidence files: server/main.py, frontend/readonly-preview/m5k-workbench.js, README.md, docs/operator/LOCAL_WORKBENCH.md
- Current normalized/retained fields: governance, summary, content, caveats
- Raw/source fields known: local artifact fields
- Dropped-field handling: See top-level dropped_field_decisions and field_inventory lifecycle rows; names alone are insufficient evidence.
- Evidence claims:
  - `local_m5k_observation_history_exposure` (confirmed_from_code): Local M5K observation history is represented by explicit local code paths; exposure is based on returned/rendered code, not artifact existence alone. Evidence: server/main.py, frontend/readonly-preview/m5k-workbench.js; symbol/section: relevant endpoint/tool/render function.

### M5N_watchlist_conversation_handoff

- Evidence status: validated_runtime_source
- Runtime integrated: True; runtime exposure: exposed_in_fastapi, exposed_in_mcp, exposed_in_frontend, exposed_in_conversation_context
- Evidence files: scripts/m5k_common.py, server/main.py, server/mcp_server.py, frontend/readonly-preview/m5k-workbench.js, README.md, docs/operator/LOCAL_WORKBENCH.md
- Current normalized/retained fields: governance, summary, content, caveats
- Raw/source fields known: local artifact fields
- Dropped-field handling: See top-level dropped_field_decisions and field_inventory lifecycle rows; names alone are insufficient evidence.
- Evidence claims:
  - `m5n_watchlist_conversation_handoff_exposure` (confirmed_from_code): M5N watchlist / conversation handoff is represented by explicit local code paths; exposure is based on returned/rendered code, not artifact existence alone. Evidence: scripts/m5k_common.py, server/main.py, server/mcp_server.py, frontend/readonly-preview/m5k-workbench.js; symbol/section: relevant endpoint/tool/render function.

### M5Q_source_health_report

- Evidence status: validated_runtime_source
- Runtime integrated: True; runtime exposure: exposed_in_fastapi, exposed_in_mcp, exposed_in_frontend, exposed_in_conversation_context
- Evidence files: scripts/m5q_source_health.py, server/main.py, server/mcp_server.py, frontend/readonly-preview/m5k-workbench.js, README.md, docs/operator/LOCAL_WORKBENCH.md
- Current normalized/retained fields: governance, summary, content, caveats
- Raw/source fields known: local artifact fields
- Dropped-field handling: See top-level dropped_field_decisions and field_inventory lifecycle rows; names alone are insufficient evidence.
- Evidence claims:
  - `m5q_source_health_report_exposure` (confirmed_from_code): M5Q source-health report is represented by explicit local code paths; exposure is based on returned/rendered code, not artifact existence alone. Evidence: scripts/m5q_source_health.py, server/main.py, server/mcp_server.py, frontend/readonly-preview/m5k-workbench.js; symbol/section: relevant endpoint/tool/render function.

### FastAPI_context_endpoints

- Evidence status: validated_runtime_source
- Runtime integrated: True; runtime exposure: exposed_in_fastapi, exposed_in_frontend
- Evidence files: server/main.py, frontend/readonly-preview/m5k-workbench.js, README.md, docs/operator/LOCAL_WORKBENCH.md
- Current normalized/retained fields: governance, summary, content, caveats
- Raw/source fields known: local artifact fields
- Dropped-field handling: See top-level dropped_field_decisions and field_inventory lifecycle rows; names alone are insufficient evidence.
- Evidence claims:
  - `fastapi_context_endpoints_exposure` (confirmed_from_code): FastAPI readonly context endpoints is represented by explicit local code paths; exposure is based on returned/rendered code, not artifact existence alone. Evidence: server/main.py, frontend/readonly-preview/m5k-workbench.js; symbol/section: relevant endpoint/tool/render function.

### FastAPI_live_observation_endpoints

- Evidence status: validated_runtime_source
- Runtime integrated: True; runtime exposure: exposed_in_fastapi, exposed_in_frontend
- Evidence files: server/main.py, frontend/readonly-preview/m5k-workbench.js, README.md, docs/operator/LOCAL_WORKBENCH.md
- Current normalized/retained fields: governance, summary, content, caveats
- Raw/source fields known: local artifact fields
- Dropped-field handling: See top-level dropped_field_decisions and field_inventory lifecycle rows; names alone are insufficient evidence.
- Evidence claims:
  - `fastapi_live_observation_endpoints_exposure` (confirmed_from_code): FastAPI live observation read/plan endpoints is represented by explicit local code paths; exposure is based on returned/rendered code, not artifact existence alone. Evidence: server/main.py, frontend/readonly-preview/m5k-workbench.js; symbol/section: relevant endpoint/tool/render function.

### FastAPI_conversation_context_endpoint

- Evidence status: validated_runtime_source
- Runtime integrated: True; runtime exposure: exposed_in_fastapi, exposed_in_frontend, exposed_in_conversation_context
- Evidence files: server/main.py, scripts/m5k_common.py, frontend/readonly-preview/m5k-workbench.js, README.md, docs/operator/LOCAL_WORKBENCH.md
- Current normalized/retained fields: governance, summary, content, caveats
- Raw/source fields known: local artifact fields
- Dropped-field handling: See top-level dropped_field_decisions and field_inventory lifecycle rows; names alone are insufficient evidence.
- Evidence claims:
  - `fastapi_conversation_context_endpoint_exposure` (confirmed_from_code): FastAPI conversation context endpoint is represented by explicit local code paths; exposure is based on returned/rendered code, not artifact existence alone. Evidence: server/main.py, scripts/m5k_common.py, frontend/readonly-preview/m5k-workbench.js; symbol/section: relevant endpoint/tool/render function.

### MCP_server_exposed_resources_tools

- Evidence status: validated_runtime_source
- Runtime integrated: True; runtime exposure: exposed_in_mcp, exposed_in_conversation_context
- Evidence files: server/mcp_server.py, README.md, docs/operator/LOCAL_WORKBENCH.md
- Current normalized/retained fields: governance, summary, content, caveats
- Raw/source fields known: local artifact fields
- Dropped-field handling: See top-level dropped_field_decisions and field_inventory lifecycle rows; names alone are insufficient evidence.
- Evidence claims:
  - `mcp_server_exposed_resources_tools_exposure` (confirmed_from_code): MCP server exposed resources/tools is represented by explicit local code paths; exposure is based on returned/rendered code, not artifact existence alone. Evidence: server/mcp_server.py; symbol/section: relevant endpoint/tool/render function.

## Field lifecycle analysis

This table answers what raw data is known, what the current parser reads, what normalization independently retains, and what reaches FastAPI/MCP/frontend/conversation context. A `yes` exposure means the current code path returns or renders that field; it is not inferred from artifact presence alone.

| source_id | raw_field_name | raw_field_known | current_parser_reads_field | current_parser_usage | retained_as_independent_normalized_field | normalized_field_name | derived_normalized_fields | exposed_fastapi | exposed_mcp | exposed_frontend | exposed_conversation_context | dropped_status | dropped_reason_category | reintroduction_priority |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TWSE_MIS | z | yes | yes | preferred current/last price candidate via _select_mis_price | yes | price_like_value/value when selected | [] | yes | yes | yes | yes | not_dropped | not_applicable | defer |
| TWSE_MIS | y | yes | yes | fallback price_like_value when z unavailable; reference_value_only status | no |  | [] | no | no | no | no | consumed_not_retained | original_scope_minimal_price_only | M7A_high |
| TWSE_MIS | o | yes | no | not read by current parser | no |  | [] | no | no | no | no | fetched_but_not_parsed | original_scope_minimal_price_only | M7A_high |
| TWSE_MIS | h | yes | no | not read by current parser | no |  | [] | no | no | no | no | fetched_but_not_parsed | original_scope_minimal_price_only | M7A_high |
| TWSE_MIS | l | yes | no | not read by current parser | no |  | [] | no | no | no | no | fetched_but_not_parsed | original_scope_minimal_price_only | M7A_high |
| TWSE_MIS | v | yes | no | not read by current parser | no |  | [] | no | no | no | no | fetched_but_not_parsed | unit_not_verified | M7A_high |
| TWSE_MIS | tv | yes | no | not read by current parser | no |  | [] | no | no | no | no | fetched_but_not_parsed | unit_not_verified | M7A_high |
| TWSE_MIS | b | yes | no | not read by current parser | no |  | [] | no | no | no | no | fetched_but_not_parsed | semantic_not_verified | M7A_high |
| TWSE_MIS | g | yes | no | not read by current parser | no |  | [] | no | no | no | no | fetched_but_not_parsed | semantic_not_verified | M7A_high |
| TWSE_MIS | a | yes | no | not read by current parser | no |  | [] | no | no | no | no | fetched_but_not_parsed | semantic_not_verified | M7A_high |
| TWSE_MIS | f | yes | no | not read by current parser | no |  | [] | no | no | no | no | fetched_but_not_parsed | semantic_not_verified | M7A_high |
| TWSE_MIS | u | yes | no | not read by current parser | no |  | [] | no | no | no | no | fetched_but_not_parsed | semantic_not_verified | M7B_medium |
| TWSE_MIS | w | yes | no | not read by current parser | no |  | [] | no | no | no | no | fetched_but_not_parsed | semantic_not_verified | M7B_medium |
| TWSE_MIS | ch | yes | no | not read by current parser | no |  | [] | no | no | no | no | fetched_but_not_parsed | replaced_by_existing_field | defer |
| TWSE_MIS | ex | yes | no | not read by current parser | no |  | [] | no | no | no | no | fetched_but_not_parsed | replaced_by_existing_field | defer |
| TWSE_MIS | n | yes | no | not read by current parser | no |  | [] | no | no | no | no | fetched_but_not_parsed | consumer_not_ready | M7B_medium |
| TWSE_MIS | % | yes | no | not read by current parser | no |  | [] | no | no | no | no | fetched_but_not_parsed | freshness_or_timestamp_unclear | defer |
| TWSE_MIS | ot | yes | no | not read by current parser | no |  | [] | no | no | no | no | fetched_but_not_parsed | freshness_or_timestamp_unclear | defer |
| TWSE_MIS | t | yes | yes | used to build normalized source_timestamp/delay flags | no |  | ['source_timestamp', 'delay_seconds'] | yes | yes | yes | yes | consumed_not_retained | replaced_by_existing_field | defer |
| TWSE_MIS | d | yes | yes | used to build normalized source_timestamp/delay flags | no |  | ['source_timestamp', 'delay_seconds'] | yes | yes | yes | yes | consumed_not_retained | replaced_by_existing_field | defer |
| TWSE_MIS | tlong | yes | yes | used to build normalized source_timestamp/delay flags | no |  | ['source_timestamp', 'delay_seconds'] | yes | yes | yes | yes | consumed_not_retained | replaced_by_existing_field | defer |
| TAIFEX_MIS | CLastPrice | yes | yes | preferred last price input | yes | price_like_value/value when selected | [] | yes | yes | yes | yes | not_dropped | not_applicable | defer |
| TAIFEX_MIS | SettlementPrice | yes | yes | fallback price input when CLastPrice unavailable | no |  | [] | no | no | no | no | consumed_not_retained | original_scope_minimal_price_only | M7A_high |
| TAIFEX_MIS | CRefPrice | yes | yes | fallback price input after CLastPrice/SettlementPrice | no |  | [] | no | no | no | no | consumed_not_retained | original_scope_minimal_price_only | M7A_high |
| TAIFEX_MIS | CDate | yes | yes | source timestamp date input | no |  | ['source_timestamp'] | yes | yes | yes | yes | consumed_not_retained | replaced_by_existing_field | defer |
| TAIFEX_MIS | CTime | yes | yes | source timestamp time input | no |  | ['source_timestamp'] | yes | yes | yes | yes | consumed_not_retained | replaced_by_existing_field | defer |
| TAIFEX_MIS | Status | yes | yes | session/quote status used for freshness flags and source_status extra | yes | source_status | [] | yes | yes | no | no | parsed_retained_partially_exposed | consumer_not_ready | M7B_medium |
| TAIFEX_MIS | SymbolID | yes | yes | selected contract identity and extra normalization metadata | yes | contract/source_contract_symbol | [] | yes | yes | no | no | parsed_retained_partially_exposed | consumer_not_ready | M7B_medium |
| TAIFEX_MIS | DispEName | yes | yes | contract month derivation and source_display_name metadata | yes | normalization.source_display_name | [] | yes | yes | no | no | parsed_retained_partially_exposed | consumer_not_ready | M7B_medium |
| TAIFEX_MIS | DispCName | yes | yes | contract month fallback derivation | no |  | [] | no | no | no | no | consumed_not_retained | original_scope_minimal_price_only | M7A_high |
| TPEx_OpenAPI | Average | yes | no | source is not current runtime integrated | no |  | [] | no | no | no | no | known_from_contract_not_runtime_fetched | timing_class_not_runtime_compatible | M7C_official_eod |
| TPEx_OpenAPI | LatestBidPrice | yes | no | source is not current runtime integrated | no |  | [] | no | no | no | no | known_from_contract_not_runtime_fetched | timing_class_not_runtime_compatible | M7C_official_eod |
| TPEx_OpenAPI | LatesAskPrice | yes | no | source is not current runtime integrated | no |  | [] | no | no | no | no | known_from_contract_not_runtime_fetched | timing_class_not_runtime_compatible | M7C_official_eod |
| TPEx_OpenAPI | NextReferencePrice | yes | no | source is not current runtime integrated | no |  | [] | no | no | no | no | known_from_contract_not_runtime_fetched | timing_class_not_runtime_compatible | M7C_official_eod |
| Yahoo_Finance | full_intraday_series | yes | no | source is not current runtime integrated | no |  | [] | no | no | no | no | known_from_contract_not_runtime_fetched | intentionally_deferred | M7D_optional |
| Fugle_MarketData | provider_fields_unknown | unknown | no | source is not current runtime integrated | no |  | [] | no | no | no | no | unknown_needs_validation | credential_or_access_limited | M7E_provider_research |
| Fubon_Neo_API | provider_fields_unknown | unknown | no | source is not current runtime integrated | no |  | [] | no | no | no | no | unknown_needs_validation | credential_or_access_limited | M7E_provider_research |

## Dropped field decision analysis

`Dropped` does not always mean intentionally rejected. Some fields are dropped because M5K currently normalizes minimal price/freshness; some are known but need unit or semantic validation; some are not dropped at runtime because their source is not integrated at all; and some may be safely deferred to avoid raw payload leakage or trading-like semantics.

| source_id | raw_field_name | current_lifecycle | dropped_reason_category | dropped_decision_status | reintroduction_priority | reintroduction_blockers |
|---|---|---|---|---|---|---|
| TWSE_MIS | y | consumed_not_retained | original_scope_minimal_price_only | implicit_from_current_code | M7A_high | ['add independent previous_close tests', 'preserve reference-only caveat'] |
| TWSE_MIS | o | fetched_but_not_parsed | original_scope_minimal_price_only | implicit_from_current_code | M7A_high | ['confirm placeholder semantics', 'add normalization tests'] |
| TWSE_MIS | h | fetched_but_not_parsed | original_scope_minimal_price_only | implicit_from_current_code | M7A_high | ['confirm numeric placeholder semantics', 'add normalization tests'] |
| TWSE_MIS | l | fetched_but_not_parsed | original_scope_minimal_price_only | implicit_from_current_code | M7A_high | ['confirm numeric placeholder semantics', 'add normalization tests'] |
| TWSE_MIS | v | fetched_but_not_parsed | unit_not_verified | no_clear_decision_found | M7A_high | ['validate unit semantics before labeling shares/lots'] |
| TWSE_MIS | tv | fetched_but_not_parsed | unit_not_verified | no_clear_decision_found | M7A_high | ['validate unit semantics and placeholder behavior'] |
| TWSE_MIS | b | fetched_but_not_parsed | semantic_not_verified | no_clear_decision_found | M7A_high | ['parse ladder safely', 'describe only as displayed depth snapshot'] |
| TWSE_MIS | g | fetched_but_not_parsed | semantic_not_verified | no_clear_decision_found | M7A_high | ['validate ladder volume unit', 'avoid pressure/flow wording'] |
| TWSE_MIS | a | fetched_but_not_parsed | semantic_not_verified | no_clear_decision_found | M7A_high | ['parse ladder safely', 'describe only as displayed depth snapshot'] |
| TWSE_MIS | f | fetched_but_not_parsed | semantic_not_verified | no_clear_decision_found | M7A_high | ['validate ladder volume unit', 'avoid pressure/flow wording'] |
| TWSE_MIS | u | fetched_but_not_parsed | semantic_not_verified | no_clear_decision_found | M7B_medium | ['confirm limit semantics across index/equity rows'] |
| TWSE_MIS | w | fetched_but_not_parsed | semantic_not_verified | no_clear_decision_found | M7B_medium | ['confirm limit semantics across index/equity rows'] |
| TWSE_MIS | ch | fetched_but_not_parsed | replaced_by_existing_field | implicit_from_current_code | defer | ['route/channel already available from plan where needed'] |
| TWSE_MIS | ex | fetched_but_not_parsed | replaced_by_existing_field | implicit_from_current_code | defer | ['market/adapter already retained; validate need before adding'] |
| TWSE_MIS | n | fetched_but_not_parsed | consumer_not_ready | implicit_from_current_code | M7B_medium | ['decide precedence versus watchlist display_name'] |
| TWSE_MIS | % | fetched_but_not_parsed | freshness_or_timestamp_unclear | no_clear_decision_found | defer | ['semantics unknown; tlong/d/t already used'] |
| TWSE_MIS | ot | fetched_but_not_parsed | freshness_or_timestamp_unclear | no_clear_decision_found | defer | ['semantics unknown; tlong/d/t already used'] |
| TWSE_MIS | t | consumed_not_retained | replaced_by_existing_field | implicit_from_current_code | defer | [] |
| TWSE_MIS | d | consumed_not_retained | replaced_by_existing_field | implicit_from_current_code | defer | [] |
| TWSE_MIS | tlong | consumed_not_retained | replaced_by_existing_field | implicit_from_current_code | defer | [] |
| TAIFEX_MIS | SettlementPrice | consumed_not_retained | original_scope_minimal_price_only | implicit_from_current_code | M7A_high | ['decide if settlement should be independently retained'] |
| TAIFEX_MIS | CRefPrice | consumed_not_retained | original_scope_minimal_price_only | implicit_from_current_code | M7A_high | ['decide if reference should be independently retained'] |
| TAIFEX_MIS | CDate | consumed_not_retained | replaced_by_existing_field | implicit_from_current_code | defer | [] |
| TAIFEX_MIS | CTime | consumed_not_retained | replaced_by_existing_field | implicit_from_current_code | defer | [] |
| TAIFEX_MIS | Status | parsed_retained_partially_exposed | consumer_not_ready | implicit_from_current_code | M7B_medium | ['frontend/conversation may need compact status display'] |
| TAIFEX_MIS | SymbolID | parsed_retained_partially_exposed | consumer_not_ready | implicit_from_current_code | M7B_medium | ['frontend currently renders contract sparsely'] |
| TAIFEX_MIS | DispEName | parsed_retained_partially_exposed | consumer_not_ready | implicit_from_current_code | M7B_medium | ['decide whether UI should show source display name'] |
| TAIFEX_MIS | DispCName | consumed_not_retained | original_scope_minimal_price_only | implicit_from_current_code | M7A_high | ['add tests if retained'] |
| TPEx_OpenAPI | Average | known_from_contract_not_runtime_fetched | timing_class_not_runtime_compatible | inferred_from_docs | M7C_official_eod | ['runtime integration not in scope', 'validate source contract before exposure'] |
| TPEx_OpenAPI | LatestBidPrice | known_from_contract_not_runtime_fetched | timing_class_not_runtime_compatible | inferred_from_docs | M7C_official_eod | ['runtime integration not in scope', 'validate source contract before exposure'] |
| TPEx_OpenAPI | LatesAskPrice | known_from_contract_not_runtime_fetched | timing_class_not_runtime_compatible | inferred_from_docs | M7C_official_eod | ['runtime integration not in scope', 'validate source contract before exposure'] |
| TPEx_OpenAPI | NextReferencePrice | known_from_contract_not_runtime_fetched | timing_class_not_runtime_compatible | inferred_from_docs | M7C_official_eod | ['runtime integration not in scope', 'validate source contract before exposure'] |
| Yahoo_Finance | full_intraday_series | known_from_contract_not_runtime_fetched | intentionally_deferred | inferred_from_docs | M7D_optional | ['runtime integration not in scope', 'validate source contract before exposure'] |
| Fugle_MarketData | provider_fields_unknown | unknown_needs_validation | credential_or_access_limited | inferred_from_docs | M7E_provider_research | ['runtime integration not in scope', 'validate source contract before exposure'] |
| Fubon_Neo_API | provider_fields_unknown | unknown_needs_validation | credential_or_access_limited | inferred_from_docs | M7E_provider_research | ['runtime integration not in scope', 'validate source contract before exposure'] |

### Fields with no explicit drop decision found

- TWSE_MIS.v: Raw field is documented, but current normalize_twse_mis_row selects z/y and timestamp fields only; no explicit repo decision found to independently normalize v.
- TWSE_MIS.tv: Raw field is documented, but current normalize_twse_mis_row selects z/y and timestamp fields only; no explicit repo decision found to independently normalize tv.
- TWSE_MIS.b: Raw field is documented, but current normalize_twse_mis_row selects z/y and timestamp fields only; no explicit repo decision found to independently normalize b.
- TWSE_MIS.g: Raw field is documented, but current normalize_twse_mis_row selects z/y and timestamp fields only; no explicit repo decision found to independently normalize g.
- TWSE_MIS.a: Raw field is documented, but current normalize_twse_mis_row selects z/y and timestamp fields only; no explicit repo decision found to independently normalize a.
- TWSE_MIS.f: Raw field is documented, but current normalize_twse_mis_row selects z/y and timestamp fields only; no explicit repo decision found to independently normalize f.
- TWSE_MIS.u: Raw field is documented, but current normalize_twse_mis_row selects z/y and timestamp fields only; no explicit repo decision found to independently normalize u.
- TWSE_MIS.w: Raw field is documented, but current normalize_twse_mis_row selects z/y and timestamp fields only; no explicit repo decision found to independently normalize w.
- TWSE_MIS.%: Raw field is documented, but current normalize_twse_mis_row selects z/y and timestamp fields only; no explicit repo decision found to independently normalize %.
- TWSE_MIS.ot: Raw field is documented, but current normalize_twse_mis_row selects z/y and timestamp fields only; no explicit repo decision found to independently normalize ot.

### Fields intentionally or safely deferred

- TWSE_MIS.ch: replaced_by_existing_field / defer.
- TWSE_MIS.ex: replaced_by_existing_field / defer.
- TWSE_MIS.%: freshness_or_timestamp_unclear / defer.
- TWSE_MIS.ot: freshness_or_timestamp_unclear / defer.
- TWSE_MIS.t: replaced_by_existing_field / defer.
- TWSE_MIS.d: replaced_by_existing_field / defer.
- TWSE_MIS.tlong: replaced_by_existing_field / defer.
- TAIFEX_MIS.CDate: replaced_by_existing_field / defer.
- TAIFEX_MIS.CTime: replaced_by_existing_field / defer.
- Yahoo_Finance.full_intraday_series: intentionally_deferred / M7D_optional.
- Fugle_MarketData.provider_fields_unknown: credential_or_access_limited / M7E_provider_research.
- Fubon_Neo_API.provider_fields_unknown: credential_or_access_limited / M7E_provider_research.

## Deterministic metrics possible

| metric_id | required_fields | source_family_compatibility | current_availability | ai_phrasing_allowed | ai_phrasing_forbidden |
|---|---|---|---|---|---|
| change | ['last_price', 'previous_close'] | ['TWSE_MIS', 'TWSE_OpenAPI', 'TPEx_OpenAPI'] | candidate_after_field_retention | price difference | signal/recommendation |
| change_percent | ['last_price', 'previous_close'] | ['TWSE_MIS'] | candidate_after_field_retention | percentage move versus reference | momentum call |
| range | ['high', 'low'] | ['TWSE_MIS', 'TWSE_OpenAPI', 'TPEx_OpenAPI', 'Yahoo_Finance'] | available_eod_not_live_exposed | observed range | support/resistance as fact |
| position_in_day_range | ['last_price', 'high', 'low'] | ['TWSE_MIS'] | candidate_after_field_retention | location within observed day range | entry/exit |
| spread | ['best_ask', 'best_bid'] | ['TWSE_MIS'] | candidate_after_depth_retention | displayed spread snapshot | liquidity guarantee |
| top5_bid_volume | ['bid_volumes'] | ['TWSE_MIS'] | candidate_after_depth_retention | observed displayed bid depth | institutional/chip flow |
| watchlist_unavailable_count | ['status'] | ['M5N_watchlist_conversation_handoff'] | currently_possible | unavailable observations | quality hidden |
| cross_instrument_change_diff | ['change_percent'] | ['TWSE_MIS', 'TAIFEX_MIS'] | candidate_after_field_retention | bounded cross-instrument difference | relative value recommendation |

## AI context expansion strategy

- Facts: expose retained fields with source time, retrieval time, freshness, caveats, and evidence status.
- Deterministic derived metrics: compute only when required fields are retained and quality flags permit.
- Bounded summaries: use watchlist counts and differences without preference, ranking, or execution language.
- AI layer: context-only discussion; no trading semantics.

## Semantic safety rules

Allowed examples: observed displayed bid depth; bounded watchlist observation; reference-only; delayed or stale; not official realtime SLA.

Forbidden examples: buy; sell; hold; target price; ranking; guaranteed realtime; support/resistance as fact; institutional/chip flow.

## Recommended M7 roadmap

- **M7A_rich_mis_observation_contract:** Rich TWSE MIS / TAIFEX observation contract expansion; no new source; expose richer quote snapshot facts after lifecycle tests.
- **M7B_market_context_package_and_ai_markdown:** Market Context Package plus richer AI Markdown/MCP context and bounded summaries.
- **M7C_official_eod_context_expansion:** Official TWSE/TPEx EOD context expansion and canonical/recent daily baseline.
- **M7D_optional_third_party_historical_context:** Optional Yahoo/FinMind historical context with coverage and delay caveats.
- **M7E_credential_gated_provider_research:** Fugle/Fubon credential-gated provider research only.

## README summary proposal

README now states that the inventory includes validated runtime sources, validated contracts/probes, validated historical workbench evidence, catalogued candidates, and credential-gated providers; it also warns that not every listed family is a validated usable endpoint.
