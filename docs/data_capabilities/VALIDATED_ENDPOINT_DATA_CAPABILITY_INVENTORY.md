# Validated Endpoint Data Capability Inventory

## Executive summary

The current local product works, but the context surfaced to humans and AI is thin: successful live rows mostly expose one price-like value plus timestamp, freshness, and caveats. Repository evidence shows several source families and field contracts are available or partially implemented, especially TWSE MIS raw fields that are currently dropped by normalization. The main gap is therefore normalization, runtime exposure, and conversation-context composition, not only source discovery. Next implementation should be evidence-driven and preserve non-trading semantics.

## Current architecture map

- **Local canonical context:** M5F reads reviewed local artifacts through FastAPI, frontend, and MCP.
- **Live bounded observation:** M5K can explicitly execute bounded TWSE MIS and TAIFEX observations; this PR did not run it.
- **Conversation context:** M5N combines watchlist, canonical, latest observation, and source-health summaries without raw endpoint payloads.
- **Source health:** M5Q records manual bounded health probe summaries; latest report is read-only unless operator executes the probe.
- **Frontend:** readonly preview consumes local API endpoints and displays caveats.
- **MCP:** exposes readonly/local tools plus explicit bounded execution tools guarded by confirmation.

## Source family inventory

### TWSE_MIS

- **What it is:** TWSE MIS browser JSON stock/index quotes
- **Repo evidence:** files=scripts/m5k_common.py, scripts/observation_contract.py, config/m5l_live_source_adapter_matrix.json; docs=docs/protocol/TWSE_MIS_FIELD_DICTIONARY.md, docs/protocol/TWSE_MIS_PROTOCOL.md, docs/m5l_live_sources_validation_matrix.md
- **Current implementation status:** implemented_normalized_now; runtime=exposed_in_fastapi, exposed_in_mcp, exposed_in_frontend, exposed_in_conversation_context, fetched_but_dropped
- **Available fields:** c, ex, n, ch, z, y, o, h, l, v, tv, b, g, a, f, u, w, d, t, tlong, %, ot
- **Normalized/exposed fields:** schema_version, symbol, display_symbol, category_id, instrument_type, status, source, adapter_id, market, source_type, price_like_value, value, price_semantics, source_timestamp, retrieved_at_utc, freshness_assessment, delay_status, delay_seconds, staleness_seconds, reference_only...
- **Dropped fields:** previous_close, open, high, low, cumulative_volume, latest_trade_volume, bid_ladder, ask_ladder, limit_up, limit_down, display_name, exchange, channel
- **AI context value:** Richer quote snapshot facts, displayed depth snapshot, day range, and bounded watchlist aggregates without trading interpretation.
- **Semantic risks:** medium_unofficial_contract_fragility, high_realtime_claim_risk, high_trading_interpretation_risk
- **Recommended milestone:** M7A_rich_mis_observation_contract

### TAIFEX_MIS

- **What it is:** TAIFEX MIS TX futures QuoteList
- **Repo evidence:** files=scripts/m5k_common.py, scripts/observation_contract.py, config/m5l_live_source_adapter_matrix.json; docs=docs/m5l_taifex_live_source_validation.md, docs/m5k_taifex_tx_futures_preflight.md
- **Current implementation status:** implemented_normalized_now; runtime=exposed_in_fastapi, exposed_in_mcp, exposed_in_frontend, exposed_in_conversation_context, fetched_but_dropped
- **Available fields:** CLastPrice, SettlementPrice, CRefPrice, CDate, CTime, Status, SymbolID, DispEName, DispCName
- **Normalized/exposed fields:** schema_version, symbol, display_symbol, category_id, instrument_type, status, source, adapter_id, market, source_type, price_like_value, value, price_semantics, source_timestamp, retrieved_at_utc, freshness_assessment, delay_status, delay_seconds, staleness_seconds, reference_only...
- **Dropped fields:** other_quote_list_contracts, raw_quote_count, open/high/low/reference/volume/bid/ask fields if present are not evident in current parser
- **AI context value:** TX context adjacent to TAIEX/watchlist if richer fields are validated.
- **Semantic risks:** high_realtime_claim_risk, high_trading_interpretation_risk
- **Recommended milestone:** M7A_rich_mis_observation_contract

### TWSE_OpenAPI

- **What it is:** TWSE official OpenAPI EOD daily quote
- **Repo evidence:** files=docs/contracts/twse_openapi_normalized_eod_quote_v1.md; docs=docs/protocol/TWSE_OPENAPI_FIELD_DICTIONARY.md, docs/protocol/OFFICIAL_OPENAPI_SOURCE_SEMANTICS.md
- **Current implementation status:** implemented_probe_or_contract_now; runtime=docs_only, contract_known_but_not_implemented, normalized_but_not_exposed
- **Available fields:** Date, Code, Name, TradeVolume, TradeValue, OpeningPrice, HighestPrice, LowestPrice, ClosingPrice, Change, Transaction
- **Normalized/exposed fields:** trade_date, symbol, name, trade_volume, trade_value, open, high, low, close, change, transaction_count
- **Dropped fields:** 
- **AI context value:** Official EOD baseline for daily context and stale/reference comparisons.
- **Semantic risks:** medium_delayed_or_reference_only
- **Recommended milestone:** M7C_official_eod_context_expansion

### TPEx_OpenAPI

- **What it is:** TPEx official OpenAPI EOD daily close quotes
- **Repo evidence:** files=docs/contracts/tpex_openapi_normalized_eod_quote_v1.md; docs=docs/protocol/TPEX_OPENAPI_FIELD_DICTIONARY.md, docs/protocol/OFFICIAL_OPENAPI_SOURCE_SEMANTICS.md
- **Current implementation status:** implemented_probe_or_contract_now; runtime=docs_only, contract_known_but_not_implemented, normalized_but_not_exposed
- **Available fields:** Date, SecuritiesCompanyCode, CompanyName, Close, Change, Open, High, Low, Average, TradingShares, TransactionAmount, TransactionNumber, LatestBidPrice, LatesAskPrice, Capitals, NextReferencePrice, NextLimitUp, NextLimitDown
- **Normalized/exposed fields:** trade_date, symbol, name, close, change, open, high, low, trade_volume, trade_value, transaction_count
- **Dropped fields:** Average, LatestBidPrice, LatesAskPrice, Capitals, NextReferencePrice, NextLimitUp, NextLimitDown
- **AI context value:** Official TPEx daily baseline and next-day reference context.
- **Semantic risks:** medium_delayed_or_reference_only
- **Recommended milestone:** M7C_official_eod_context_expansion

### Yahoo_Finance

- **What it is:** Yahoo Finance chart endpoint
- **Repo evidence:** files=docs/contracts/yahoo_finance_normalized_chart_v1.md; docs=docs/protocol/YAHOO_FINANCE_CHART_PROTOCOL.md, docs/capability_matrix.md
- **Current implementation status:** implemented_probe_or_contract_now; runtime=docs_only, contract_known_but_not_implemented
- **Available fields:** meta, timestamp, indicators.quote.open/high/low/close/volume, adjclose, chart.error
- **Normalized/exposed fields:** symbol, regular_market_price, regular_market_time, open, high, low, close, volume
- **Dropped fields:** full_intraday_series, timezone_metadata, currency, exchangeName
- **AI context value:** Optional historical/chart context if coverage and delay are displayed.
- **Semantic risks:** medium_unofficial_contract_fragility, medium_delayed_or_reference_only
- **Recommended milestone:** M7D_optional_third_party_historical_context

### FinMind

- **What it is:** FinMind data API
- **Repo evidence:** files=docs/capability_matrix.md; docs=docs/protocol/OFFICIAL_OPENAPI_SOURCE_SEMANTICS.md
- **Current implementation status:** validated_historical_workbench; runtime=docs_only, contract_known_but_not_implemented
- **Available fields:** dataset-dependent
- **Normalized/exposed fields:** historical/eod sample fields in prior capability matrix only
- **Dropped fields:** not integrated into runtime observation
- **AI context value:** Optional historical context package.
- **Semantic risks:** medium_delayed_or_reference_only, high_credential_or_compliance_risk
- **Recommended milestone:** M7D_optional_third_party_historical_context

### Fugle_MarketData

- **What it is:** Fugle MarketData API
- **Repo evidence:** files=config/m5l_live_source_adapter_matrix.json, docs/capability_matrix.md; docs=docs/protocol/OFFICIAL_OPENAPI_SOURCE_SEMANTICS.md
- **Current implementation status:** credential_gated_not_usable_now; runtime=docs_only
- **Available fields:** unknown_needs_credentials
- **Normalized/exposed fields:** 
- **Dropped fields:** all provider fields; no integration
- **AI context value:** Licensed read-only live provider if terms and credentials allow.
- **Semantic risks:** high_credential_or_compliance_risk, high_realtime_claim_risk
- **Recommended milestone:** M7E_credential_gated_provider_research

### Fubon_Neo_API

- **What it is:** Fubon Neo API
- **Repo evidence:** files=config/m5l_live_source_adapter_matrix.json, docs/capability_matrix.md; docs=docs/protocol/OFFICIAL_OPENAPI_SOURCE_SEMANTICS.md
- **Current implementation status:** credential_gated_not_usable_now; runtime=docs_only
- **Available fields:** unknown_needs_broker_credentials
- **Normalized/exposed fields:** 
- **Dropped fields:** all provider fields; no integration
- **AI context value:** Possible read-only broker data after strict separation from order/execution features.
- **Semantic risks:** high_credential_or_compliance_risk, high_trading_interpretation_risk
- **Recommended milestone:** M7E_credential_gated_provider_research

### Local_M5F_canonical_context

- **What it is:** Local M5F canonical context
- **Repo evidence:** files=server/main.py, server/mcp_server.py, scripts/validate_m5f_canonical_market_context_package.py; docs=README.md, docs/operator/LOCAL_WORKBENCH.md
- **Current implementation status:** implemented_normalized_now; runtime=exposed_in_fastapi, exposed_in_mcp, exposed_in_frontend, exposed_in_conversation_context
- **Available fields:** local artifact fields
- **Normalized/exposed fields:** governance, summary, content, caveats
- **Dropped fields:** raw endpoint payloads are intentionally excluded
- **AI context value:** Richer bounded summaries once source rows expose more facts.
- **Semantic risks:** low_reference_context
- **Recommended milestone:** M7C_official_eod_context_expansion

### Local_M5K_latest_observation

- **What it is:** Local M5K latest observation
- **Repo evidence:** files=scripts/m5k_common.py, server/main.py, server/mcp_server.py; docs=README.md, docs/operator/LOCAL_WORKBENCH.md
- **Current implementation status:** implemented_normalized_now; runtime=exposed_in_fastapi, exposed_in_mcp, exposed_in_frontend, exposed_in_conversation_context
- **Available fields:** local artifact fields
- **Normalized/exposed fields:** schema_version, symbol, display_symbol, category_id, instrument_type, status, source, adapter_id, market, source_type, price_like_value, value, price_semantics, source_timestamp, retrieved_at_utc, freshness_assessment, delay_status, delay_seconds, staleness_seconds, reference_only...
- **Dropped fields:** raw endpoint payloads are intentionally excluded
- **AI context value:** Richer bounded summaries once source rows expose more facts.
- **Semantic risks:** medium_delayed_or_reference_only
- **Recommended milestone:** M7A_rich_mis_observation_contract

### Local_M5K_observation_history

- **What it is:** Local M5K observation history
- **Repo evidence:** files=server/main.py; docs=README.md, docs/operator/LOCAL_WORKBENCH.md
- **Current implementation status:** implemented_probe_or_contract_now; runtime=exposed_in_fastapi, normalized_but_not_exposed
- **Available fields:** local artifact fields
- **Normalized/exposed fields:** schema_version, symbol, display_symbol, category_id, instrument_type, status, source, adapter_id, market, source_type, price_like_value, value, price_semantics, source_timestamp, retrieved_at_utc, freshness_assessment, delay_status, delay_seconds, staleness_seconds, reference_only...
- **Dropped fields:** raw endpoint payloads are intentionally excluded
- **AI context value:** Richer bounded summaries once source rows expose more facts.
- **Semantic risks:** medium_delayed_or_reference_only
- **Recommended milestone:** M7B_market_context_package_and_ai_markdown

### M5N_watchlist_conversation_handoff

- **What it is:** M5N watchlist / conversation handoff
- **Repo evidence:** files=scripts/m5k_common.py, scripts/build_m5n_conversation_context.py, server/main.py, server/mcp_server.py; docs=README.md, docs/operator/LOCAL_WORKBENCH.md
- **Current implementation status:** implemented_normalized_now; runtime=exposed_in_fastapi, exposed_in_mcp, exposed_in_frontend, exposed_in_conversation_context
- **Available fields:** local artifact fields
- **Normalized/exposed fields:** governance, summary, content, caveats
- **Dropped fields:** raw endpoint payloads are intentionally excluded
- **AI context value:** Richer bounded summaries once source rows expose more facts.
- **Semantic risks:** low_reference_context
- **Recommended milestone:** M7B_market_context_package_and_ai_markdown

### M5Q_source_health_report

- **What it is:** M5Q source-health report
- **Repo evidence:** files=scripts/m5q_source_health.py, scripts/run_m5q_source_health_probe.py, server/main.py, server/mcp_server.py; docs=README.md, docs/operator/LOCAL_WORKBENCH.md
- **Current implementation status:** implemented_probe_or_contract_now; runtime=exposed_in_fastapi, exposed_in_mcp, exposed_in_frontend, exposed_in_conversation_context
- **Available fields:** local artifact fields
- **Normalized/exposed fields:** governance, summary, content, caveats
- **Dropped fields:** raw endpoint payloads are intentionally excluded
- **AI context value:** Richer bounded summaries once source rows expose more facts.
- **Semantic risks:** medium_delayed_or_reference_only
- **Recommended milestone:** M7B_market_context_package_and_ai_markdown

### FastAPI_context_endpoints

- **What it is:** FastAPI readonly context endpoints
- **Repo evidence:** files=server/main.py; docs=README.md, docs/operator/LOCAL_WORKBENCH.md
- **Current implementation status:** implemented_normalized_now; runtime=exposed_in_fastapi, exposed_in_frontend
- **Available fields:** local artifact fields
- **Normalized/exposed fields:** governance, summary, content, caveats
- **Dropped fields:** raw endpoint payloads are intentionally excluded
- **AI context value:** Richer bounded summaries once source rows expose more facts.
- **Semantic risks:** low_reference_context
- **Recommended milestone:** M7B_market_context_package_and_ai_markdown

### FastAPI_live_observation_endpoints

- **What it is:** FastAPI live observation read/plan endpoints
- **Repo evidence:** files=server/main.py; docs=README.md, docs/operator/LOCAL_WORKBENCH.md
- **Current implementation status:** implemented_normalized_now; runtime=exposed_in_fastapi, exposed_in_frontend
- **Available fields:** local artifact fields
- **Normalized/exposed fields:** schema_version, symbol, display_symbol, category_id, instrument_type, status, source, adapter_id, market, source_type, price_like_value, value, price_semantics, source_timestamp, retrieved_at_utc, freshness_assessment, delay_status, delay_seconds, staleness_seconds, reference_only...
- **Dropped fields:** raw endpoint payloads are intentionally excluded
- **AI context value:** Richer bounded summaries once source rows expose more facts.
- **Semantic risks:** medium_delayed_or_reference_only
- **Recommended milestone:** M7A_rich_mis_observation_contract

### FastAPI_conversation_context_endpoint

- **What it is:** FastAPI conversation context endpoint
- **Repo evidence:** files=server/main.py, scripts/m5k_common.py; docs=README.md, docs/operator/LOCAL_WORKBENCH.md
- **Current implementation status:** implemented_normalized_now; runtime=exposed_in_fastapi, exposed_in_frontend, exposed_in_conversation_context
- **Available fields:** local artifact fields
- **Normalized/exposed fields:** governance, summary, content, caveats
- **Dropped fields:** raw endpoint payloads are intentionally excluded
- **AI context value:** Richer bounded summaries once source rows expose more facts.
- **Semantic risks:** low_reference_context
- **Recommended milestone:** M7B_market_context_package_and_ai_markdown

### MCP_server_exposed_resources_tools

- **What it is:** MCP server exposed resources/tools
- **Repo evidence:** files=server/mcp_server.py; docs=README.md, docs/operator/LOCAL_WORKBENCH.md
- **Current implementation status:** implemented_normalized_now; runtime=exposed_in_mcp, exposed_in_conversation_context
- **Available fields:** local artifact fields
- **Normalized/exposed fields:** governance, summary, content, caveats
- **Dropped fields:** raw endpoint payloads are intentionally excluded
- **AI context value:** Richer bounded summaries once source rows expose more facts.
- **Semantic risks:** low_reference_context
- **Recommended milestone:** M7B_market_context_package_and_ai_markdown

## Field-level gap analysis

TWSE MIS is the clearest normalization gap. The raw item contract documents `z`, `y`, `o`, `h`, `l`, `v`, `tv`, bid/ask ladders, date/time, channel, exchange, and display name fields, but current live normalization mainly exposes price-like value, status, timestamp/freshness, flags, and caveats. TAIFEX normalization currently proves last/settlement/reference fallback, contract metadata, source status, and source time; repo contracts inspected here do not prove TAIFEX OHLC/volume/depth fields, so those remain unknown_needs_review rather than fabricated.

| source_id | raw_field_name | normalized_today | exposed_today | proposed_normalized_field_name | deterministic_metric_enabled | semantic_caveat |
|---|---|---|---|---|---|---|
| TWSE_MIS | z | yes | yes | last_price | change/change_percent/range_position | not official realtime; may be '-' |
| TWSE_MIS | y | yes | yes | previous_close | change/change_percent | reference fallback is not current price |
| TWSE_MIS | o | no | no | open | change_from_open_percent | may be placeholder |
| TWSE_MIS | h | no | no | high | range/position | observed day high only |
| TWSE_MIS | l | no | no | low | range/position | observed day low only |
| TWSE_MIS | v | no | no | cumulative_volume | volume summaries | unit semantics need validation |
| TWSE_MIS | tv | no | no | latest_trade_volume | last-trade context | may be placeholder |
| TWSE_MIS | b | no | no | bid_prices | spread/top5_depth | displayed depth snapshot only |
| TWSE_MIS | g | no | no | bid_volumes | top5_bid_volume | displayed depth snapshot only |
| TWSE_MIS | a | no | no | ask_prices | spread/top5_depth | displayed depth snapshot only |
| TWSE_MIS | f | no | no | ask_volumes | top5_ask_volume | displayed depth snapshot only |
| TWSE_MIS | t | yes | yes | source_time | freshness | source-local time |
| TWSE_MIS | d | yes | yes | source_date | freshness | source-local date |
| TWSE_MIS | tlong | yes | yes | source_timestamp | freshness | preferred timestamp if valid |
| TWSE_MIS | ch | no | no | channel | route audit | frontend channel |
| TWSE_MIS | ex | no | no | exchange | identity | channel semantics |
| TWSE_MIS | n | no | no | display_name | labeling | optional |
| TWSE_MIS | status/quote_state | no | no | quote_state | quality | only if observed in source rows |
| TAIFEX_MIS | CLastPrice | yes | yes | clastprice | limited_current_value_or_freshness | Current parser evidence does not prove OHLC/volume/depth fields beyond listed names. |
| TAIFEX_MIS | SettlementPrice | yes | yes | settlementprice | limited_current_value_or_freshness | Current parser evidence does not prove OHLC/volume/depth fields beyond listed names. |
| TAIFEX_MIS | CRefPrice | yes | yes | crefprice | limited_current_value_or_freshness | Current parser evidence does not prove OHLC/volume/depth fields beyond listed names. |
| TAIFEX_MIS | CDate | yes | yes | cdate | limited_current_value_or_freshness | Current parser evidence does not prove OHLC/volume/depth fields beyond listed names. |
| TAIFEX_MIS | CTime | yes | yes | ctime | limited_current_value_or_freshness | Current parser evidence does not prove OHLC/volume/depth fields beyond listed names. |
| TAIFEX_MIS | Status | yes | yes | status | limited_current_value_or_freshness | Current parser evidence does not prove OHLC/volume/depth fields beyond listed names. |
| TAIFEX_MIS | SymbolID | yes | yes | symbolid | limited_current_value_or_freshness | Current parser evidence does not prove OHLC/volume/depth fields beyond listed names. |
| TAIFEX_MIS | DispEName | yes | yes | dispename | limited_current_value_or_freshness | Current parser evidence does not prove OHLC/volume/depth fields beyond listed names. |
| TAIFEX_MIS | DispCName | yes | yes | dispcname | limited_current_value_or_freshness | Current parser evidence does not prove OHLC/volume/depth fields beyond listed names. |

## Deterministic metrics possible now

| metric_id | required_fields | source_family_compatibility | current_availability | ai_phrasing_allowed | ai_phrasing_forbidden |
|---|---|---|---|---|---|
| change | ['last_price', 'previous_close'] | ['TWSE_MIS', 'TWSE_OpenAPI', 'TPEx_OpenAPI'] | not_currently_available_for_live | price difference | signal/recommendation |
| change_percent | ['last_price', 'previous_close'] | ['TWSE_MIS'] | not_currently_available_for_live | percentage move versus reference | momentum call |
| range | ['high', 'low'] | ['TWSE_MIS', 'TWSE_OpenAPI', 'TPEx_OpenAPI', 'Yahoo_Finance'] | available_eod_not_live_exposed | observed range | support/resistance as fact |
| range_percent | ['high', 'low', 'previous_close'] | ['TWSE_MIS'] | not_currently_available_for_live | range relative to reference | volatility prediction |
| position_in_day_range | ['last_price', 'high', 'low'] | ['TWSE_MIS'] | not_currently_available_for_live | location within observed day range | entry/exit |
| distance_from_high_percent | ['last_price', 'high'] | ['TWSE_MIS'] | not_currently_available_for_live | distance from observed high | resistance |
| distance_from_low_percent | ['last_price', 'low'] | ['TWSE_MIS'] | not_currently_available_for_live | distance from observed low | support |
| change_from_open_percent | ['last_price', 'open'] | ['TWSE_MIS'] | not_currently_available_for_live | change from open | trade setup |
| spread | ['best_ask', 'best_bid'] | ['TWSE_MIS'] | not_currently_available_for_live | displayed spread snapshot | liquidity guarantee |
| spread_percent | ['best_ask', 'best_bid', 'last_price'] | ['TWSE_MIS'] | not_currently_available_for_live | displayed spread percent | execution cost guarantee |
| top5_bid_volume | ['bid_volumes'] | ['TWSE_MIS'] | not_currently_available_for_live | observed displayed bid depth | institutional flow |
| top5_ask_volume | ['ask_volumes'] | ['TWSE_MIS'] | not_currently_available_for_live | observed displayed ask depth | institutional flow |
| top5_displayed_bid_ask_ratio | ['bid_volumes', 'ask_volumes'] | ['TWSE_MIS'] | not_currently_available_for_live | displayed depth balance | chip flow |
| watchlist_advancers_count | ['change'] | ['M5N_watchlist_conversation_handoff'] | candidate_after_M7A | bounded watchlist advancers | ranking |
| watchlist_decliners_count | ['change'] | ['M5N_watchlist_conversation_handoff'] | candidate_after_M7A | bounded watchlist decliners | ranking |
| watchlist_unchanged_count | ['change'] | ['M5N_watchlist_conversation_handoff'] | candidate_after_M7A | bounded watchlist unchanged | ranking |
| watchlist_unavailable_count | ['status'] | ['M5N_watchlist_conversation_handoff'] | currently_possible | unavailable observations | quality hidden |
| cross_instrument_change_diff | ['change_percent'] | ['TWSE_MIS', 'TAIFEX_MIS'] | candidate_after_M7A | bounded cross-instrument difference | relative value recommendation |

## AI context expansion strategy

- **Facts:** expose source fields as bounded observations with source time, retrieval time, freshness, and caveats.
- **Deterministic derived metrics:** compute arithmetic metrics only when all required fields exist and quality flags permit.
- **Bounded cross-instrument summaries:** summarize watchlist counts and differences without ranking or preference language.
- **AI interpretation layer:** only context discussion; no trading advice, no targets, and no execution wording.

## Semantic safety rules

Allowed examples: observed displayed bid depth; bounded watchlist observation; reference-only; delayed or stale; not official realtime SLA.

Forbidden examples: buy; sell; hold; target price; ranking; guaranteed realtime; support/resistance as fact; institutional chip flow unless supported by future verified data.

## Recommended M7 roadmap

- **M7A_rich_mis_observation_contract:** Rich TWSE MIS / TAIFEX observation contract expansion; no new source; expose richer quote snapshot facts.
- **M7B_market_context_package_and_ai_markdown:** Market Context Package plus richer AI Markdown/MCP context and bounded cross-instrument summaries.
- **M7C_official_eod_context_expansion:** Official TWSE/TPEx EOD context expansion and canonical/recent daily baseline.
- **M7D_optional_third_party_historical_context:** Optional Yahoo/FinMind historical context with coverage and delay caveats.
- **M7E_credential_gated_provider_research:** Fugle/Fubon credential-gated provider research only; no implementation until compliance decisions exist.

## README summary proposal

README now links this report and the machine-readable JSON, explains that multiple source families exist, and states that raw availability is not the same as normalized/exposed availability. It also reiterates context-only, non-trading usage.
