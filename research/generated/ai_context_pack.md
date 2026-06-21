# AI Context Pack v2

## Generated Metadata
- **Pack version:** m3_ai_context_pack_v2_draft
- **Generated at UTC:** 2026-06-21T12:16:59.525128+00:00
- **Generated at Taipei:** 2026-06-21T20:16:59.525128+08:00
- **Generation mode:** offline_snapshot_and_observation_read

## Source Contract Baseline
- **Canonical sources:** TWSE_MIS, Yahoo_Finance, TWSE_OpenAPI, TPEx_OpenAPI, FinMind, Fugle, Fubon
- **Official EOD sources:** TWSE_OpenAPI, TPEx_OpenAPI
- **Unofficial live candidate sources:** TWSE_MIS
- **Third-party context sources:** Yahoo_Finance, FinMind
- **Auth-required sources:** Fugle, Fubon
- **Doc-only sources:** Fugle, Fubon
- **Source contract caveats:**
  - official_openapi_sources_are_eod_reference_only
  - twse_mis_is_unofficial_frontend_candidate
  - third_party_sources_require_caveats
  - broker_sources_are_auth_required_or_doc_only

## Source Health Summary
- **Total sources:** 7
- **Unavailable or failed sources:** 7
- **Offline not attempted sources:** 5
- **Source health caveats:**
  - source_health_summary_describes_local_generated_source_state_only
  - does_not_claim_current_live_production_source_availability

## Source Authority Summary
- **Usable live sources:** None
- **Usable EOD sources:** TWSE_OpenAPI, TPEx_OpenAPI
- **Source authority caveats:**
  - usable_live_sources_excludes_eod_openapi_and_broker_sources
  - twse_mis_is_unofficial_frontend
  - yahoo_finance_and_finmind_are_third_party

## Target Support Summary
- **Bounded watchlist only:** True
- **Full market coverage:** False
- **Target count:** 10
- **Failed target count:** 10
- **Target support caveats:**
  - target_support_summary_describes_support_and_scope_not_market_movement
  - target_support_summary_must_not_rank_target_classes_or_securities
  - target_classes_include_failed_bounded_watchlist_targets

## Latest Snapshot Summary
- **Snapshot version:** latest_market_snapshot_v1_draft
- **Symbol count:** 0
- **Failed symbol count:** 10
- **Failed source count:** 7

## Watchlist Observation Summary
- **Observation version:** watchlist_observations_v1
- **Observations count:** 0
- **Failed observations count:** 10
- **Categories present:** source_failed

## Failed Sources
- **TWSE_MIS** (unofficial_frontend)
  - Error type: offline_mode_no_local_input
  - Affected symbol count: 10
- **Yahoo_Finance** (third_party)
  - Error type: offline_mode_no_local_input
  - Affected symbol count: 10
- **TWSE_OpenAPI** (official_public_exchange_eod)
  - Error type: offline_mode_no_local_input
  - Affected symbol count: 10
- **TPEx_OpenAPI** (official_public_exchange_eod)
  - Error type: offline_mode_no_local_input
  - Affected symbol count: 10
- **FinMind** (third_party)
  - Error type: not_attempted_offline_default
  - Affected symbol count: 0
- **Fugle** (broker_authenticated)
  - Error type: auth_required_doc_only_skipped
  - Affected symbol count: 0
- **Fubon** (broker_authenticated)
  - Error type: auth_required_doc_only_skipped
  - Affected symbol count: 0

## Failed Targets
- **2330** (twse_common_stock)
  - Reason: all_sources_failed
- **1435** (twse_common_stock)
  - Reason: all_sources_failed
- **8069** (tpex_common_stock)
  - Reason: all_sources_failed
- **5347** (tpex_common_stock)
  - Reason: all_sources_failed
- **0050** (twse_etf)
  - Reason: all_sources_failed
- **00929** (twse_etf)
  - Reason: all_sources_failed
- **9105** (twse_tdr)
  - Reason: all_sources_failed
- **TAIEX** (twse_index)
  - Reason: all_sources_failed
- **TX** (taifex_index_future)
  - Reason: all_sources_failed
- **FUNDA** (mutual_fund)
  - Reason: all_sources_failed

## Freshness / Delay / Staleness Summary
- **Stale count:** 0
- **Unknown freshness count:** 10
- **EOD reference count:** 0
- **Live candidate count:** 0
- **Summary caveats:**
  - latest_snapshot_contains_no_successful_symbols

## AI May Say
- The context pack is bounded to the configured watchlist.
- The current snapshot may be an offline failure envelope.
- Some sources were unavailable, failed, or not attempted in offline mode.
- Official OpenAPI sources are EOD/reference sources only.
- TWSE MIS is an unofficial frontend live candidate and must carry caveats.
- Yahoo Finance and FinMind are third-party context sources and must carry caveats.
- Broker sources are auth_required/doc_only in current repo scope.
- Watchlist observations are descriptive only.
- Source failures and stale data limit what can safely be summarized.

## AI Must Not Claim
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

## Next Actions
- review_failed_sources_and_targets
- maintain_observational_context

