# ChatGPT Market Briefing

## Generated Metadata

- **Briefing Generated At (UTC)**: 2026-06-21T14:15:12.775455+00:00
- **Context Pack Version**: m3_ai_context_pack_v2_draft
- **Context Pack Generated At (UTC)**: 2026-06-21T12:16:59.525128+00:00
- **Context Pack Generated At (Taipei)**: 2026-06-21T20:16:59.525128+08:00
- **Generation Mode**: offline_snapshot_and_observation_read

*Note: The timestamp reflects context pack and briefing generation time, which does not necessarily guarantee live market freshness.*

## Current Scope

This briefing is bounded to the configured watchlist.
Full market coverage: false.

- **Bounded Watchlist Only**: true
- **Target Count**: 10
- **Failed Target Count**: 10
- **Target Classes Observed**: twse_index, twse_common_stock, mutual_fund, twse_tdr, twse_etf, taifex_index_future, tpex_common_stock
- **Target Classes Failed**: twse_index, twse_common_stock, mutual_fund, twse_tdr, twse_etf, taifex_index_future, tpex_common_stock

**Caveats**:
- target_support_summary_describes_support_and_scope_not_market_movement
- target_support_summary_must_not_rank_target_classes_or_securities
- target_classes_include_failed_bounded_watchlist_targets

**WARNING**: The current context contains no successful market targets.
No live market movement summary can be safely produced from this artifact.


## Source Health

- Total Sources: 7
- Failed/Unavailable Source Count: 7
- Failed/Unavailable Sources: TWSE_MIS, Yahoo_Finance, TWSE_OpenAPI, TPEx_OpenAPI, FinMind, Fugle, Fubon
- Offline Not Attempted Source Count: 5
- Offline Not Attempted Sources: TWSE_MIS, Yahoo_Finance, TWSE_OpenAPI, TPEx_OpenAPI
- Auth Required Sources: Fugle, Fubon
- Doc Only Sources: Fugle, Fubon

**Source Health Caveats**:
- source_health_summary_describes_local_generated_source_state_only
- does_not_claim_current_live_production_source_availability

## Source Authority

- **Official Reference (EOD)**: TWSE_OpenAPI, TPEx_OpenAPI
- **Unofficial Frontend**: TWSE_MIS
- **Third Party**: Yahoo_Finance, FinMind
- **Broker Authenticated**: Fugle, Fubon

- **Usable Live Sources**: No usable live source is established by the current context pack.
- **Usable EOD Sources**: TWSE_OpenAPI, TPEx_OpenAPI
- **Doc Only Sources**: Fugle, Fubon
- **Auth Required Sources**: Fugle, Fubon

**Source Authority Caveats**:
- usable_live_sources_excludes_eod_openapi_and_broker_sources
- twse_mis_is_unofficial_frontend
- yahoo_finance_and_finmind_are_third_party

## Market Session Status

- Status: unknown
- As of Taipei: None
- Source: generator_default
- Evidence: None
- Caveats:
  - session_detection_not_implemented_in_m3a_02

*(Note: If status is unknown, market open/closed status should not be inferred.)*

## Latest Snapshot Summary

- **Target Count**: 10
- **Symbol Count**: 0
- **Failed Symbol Count**: 10
- **Failed Source Count**: 7

**Note**: This snapshot is degraded or failed.

**Global Caveats**:
- session_detection_not_implemented_in_m3a_02

## Watchlist Observation Summary

**Important: Observations are descriptive only and not trading signals.**

- **Observations Count**: 0
- **Failed Observations Count**: 10

**Observation Type Counts**:
- **source_failed**: 10

**Severity Counts**:
- **failed**: 10

**Categories Present**: source_failed

**WARNING**: The current observation layer contains failed observations only.

**Global Caveats**:
- observations_are_descriptive_only
- observations_are_not_trading_signals

## Failed Sources

| source_id | source_type | authority_level | error_type | affected_symbol_count | caveats |
|---|---|---|---|---|---|
| TWSE_MIS | unofficial_frontend_endpoint | unofficial_frontend | offline_mode_no_local_input | 10 | no_live_network_default, offline_mode, unofficial_source_risk |
| Yahoo_Finance | third_party_api | third_party | offline_mode_no_local_input | 10 | offline_mode, third_party_coverage_caveats, no_live_network_default |
| TWSE_OpenAPI | official_openapi | official_public_exchange_eod | offline_mode_no_local_input | 10 | no_live_network_default, offline_mode, official_eod_reference_only, not_live_intraday |
| TPEx_OpenAPI | official_openapi | official_public_exchange_eod | offline_mode_no_local_input | 10 | no_live_network_default, offline_mode, official_eod_reference_only, not_live_intraday |
| FinMind | third_party_api | third_party | not_attempted_offline_default | 0 | offline_mode, historical_or_eod_candidate_with_auth_caveats |
| Fugle | broker_api | broker_authenticated | auth_required_doc_only_skipped | 0 | broker_api_not_eligible_current_repo, auth_required, doc_only |
| Fubon | broker_api | broker_authenticated | auth_required_doc_only_skipped | 0 | broker_api_not_eligible_current_repo, auth_required, doc_only |


## Failed Targets

| symbol | target_class | failure_reason | source_attempts | caveats |
|---|---|---|---|---|
| 2330 | twse_common_stock | all_sources_failed | TWSE_MIS, Yahoo_Finance, TWSE_OpenAPI, TPEx_OpenAPI | offline_mode |
| 1435 | twse_common_stock | all_sources_failed | TWSE_MIS, Yahoo_Finance, TWSE_OpenAPI, TPEx_OpenAPI | offline_mode |
| 8069 | tpex_common_stock | all_sources_failed | TWSE_MIS, Yahoo_Finance, TWSE_OpenAPI, TPEx_OpenAPI | offline_mode |
| 5347 | tpex_common_stock | all_sources_failed | TWSE_MIS, Yahoo_Finance, TWSE_OpenAPI, TPEx_OpenAPI | offline_mode |
| 0050 | twse_etf | all_sources_failed | TWSE_MIS, Yahoo_Finance, TWSE_OpenAPI, TPEx_OpenAPI | offline_mode |
| 00929 | twse_etf | all_sources_failed | TWSE_MIS, Yahoo_Finance, TWSE_OpenAPI, TPEx_OpenAPI | offline_mode |
| 9105 | twse_tdr | all_sources_failed | TWSE_MIS, Yahoo_Finance, TWSE_OpenAPI, TPEx_OpenAPI | offline_mode |
| TAIEX | twse_index | all_sources_failed | TWSE_MIS, Yahoo_Finance, TWSE_OpenAPI, TPEx_OpenAPI | offline_mode |
| TX | taifex_index_future | all_sources_failed | TWSE_MIS, Yahoo_Finance, TWSE_OpenAPI, TPEx_OpenAPI | offline_mode |
| FUNDA | mutual_fund | all_sources_failed | TWSE_MIS, Yahoo_Finance, TWSE_OpenAPI, TPEx_OpenAPI | offline_mode |


## Freshness / Delay / Staleness

- **Stale Count**: 0
- **Unknown Freshness Count**: 10
- **EOD Reference Count**: 0
- **Live Candidate Count**: 0

**Freshness Status Counts**:
- **unknown**: 10

**Delay Status Counts**:
- **unknown**: 10

**Important Rules**:
- Unknown freshness limits interpretation.
- EOD reference does not imply live intraday data.
- Live candidates are not official realtime unless future evidence explicitly proves it.

**Summary Caveats**:
- latest_snapshot_contains_no_successful_symbols

## What AI May Say

- The context pack is bounded to the configured watchlist.
- The current snapshot may be an offline failure envelope.
- Some sources were unavailable, failed, or not attempted in offline mode.
- Official OpenAPI sources are EOD/reference sources only.
- TWSE MIS is an unofficial frontend live candidate and must carry caveats.
- Yahoo Finance and FinMind are third-party context sources and must carry caveats.
- Broker sources are auth_required/doc_only in current repo scope.
- Watchlist observations are descriptive only.
- Source failures and stale data limit what can safely be summarized.

## What AI Must Not Claim

- Do not claim full-market coverage.
- Do not claim official realtime quotes unless explicitly proven.
- Do not claim EOD OpenAPI data is live intraday data.
- Do not claim TWSE MIS, Yahoo, or FinMind is official exchange authority.
- Do not turn watchlist observations into buy/sell/hold signals.
- Do not rank securities as investment opportunities.
- Do not infer target prices.
- Do not provide execution advice.
- Do not hide stale data or source failure caveats.
- Do not claim broker-account or authenticated data availability without explicit credentials and scope.
- Do not introduce unsupported average-volume, moving-average, momentum, ranking, or trend-strength language unless future artifacts explicitly support it.

## Mandatory Caveats

- bounded_watchlist_only
- not_full_market_coverage
- not_investment_advice
- observations_are_not_signals
- official_openapi_sources_are_eod_reference_only
- twse_mis_is_unofficial_frontend_candidate
- third_party_sources_require_caveats
- broker_sources_are_auth_required_or_doc_only
- failed_sources_and_failed_targets_limit_summary

## Suggested Safe Questions

- Which sources failed in the generated context pack?
- Which targets failed and why?
- What caveats should I keep in mind before interpreting this snapshot?
- What can and cannot be safely inferred from this context?
- Which source categories are official EOD vs unofficial or third-party?
- Why is this not a trading signal?
- What does bounded watchlist scope mean here?
