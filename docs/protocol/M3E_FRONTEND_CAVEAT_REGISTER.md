# M3E Frontend Caveat Register

## Caveat Categories

The M3E frontend handles three categories of caveats:
1.  **must_display_caveat**: Information critical for the end-user. Does not block frontend implementation. Must be prominently visible.
2.  **engineering_caveat_to_repair_before_or_during_M3E**: Technical defects or inconsistencies in upstream data. May block implementation if fields are unparseable.
3.  **deferred_caveat_for_future_milestone**: Known limitations (e.g., lack of full session detection) that will be handled later. Does not block implementation if clearly labeled.

## Caveat Registry

| caveat_id | category | source artifact / source doc | meaning | frontend display severity | frontend placement | blocks M3E? | recommended handling |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `bounded_watchlist_only` | `must_display_caveat` | `ai_context_pack.json` | The context is restricted to a configured watchlist, not the entire market. | `critical` | `top_banner` | No | Display permanently in header. |
| `not_full_market_coverage` | `must_display_caveat` | `ai_context_pack.json` | The data explicitly does not represent the full Taiwan market. | `critical` | `top_banner` | No | Display prominently. |
| `not_investment_advice` | `must_display_caveat` | `ai_context_pack.json` | AI briefings and observations are for context only, not trading recommendations. | `critical` | `top_banner` / `ai_briefing_panel` | No | Display prominently near AI output. |
| `observations_are_not_signals` | `must_display_caveat` | `ai_context_pack.json` | Descriptive observations must not be interpreted as buy/sell/hold indicators. | `critical` | `top_banner` / `observation_panel` | No | Emphasize in Observation summary. |
| `official_openapi_sources_are_eod_reference_only` | `must_display_caveat` | `ai_context_pack.json` | Official exchange data is End-of-Day batch data, not live intraday quotes. | `warning` | `source_health_panel` | No | Label OpenAPI sources as EOD explicitly. |
| `twse_mis_is_unofficial_frontend_candidate` | `must_display_caveat` | `ai_context_pack.json` | TWSE MIS is a fragile, unofficial endpoint and carries stability risks. | `warning` | `source_health_panel` | No | Mark TWSE MIS with warning icon. |
| `third_party_sources_require_caveats` | `must_display_caveat` | `ai_context_pack.json` | Yahoo Finance/FinMind are not official exchange authorities. | `warning` | `source_health_panel` | No | Label third-party sources clearly. |
| `broker_sources_are_auth_required_or_doc_only` | `must_display_caveat` | `ai_context_pack.json` | Fugle and Fubon sources are documented but require authentication not present in this scope. | `info` | `source_health_panel` | No | Label as doc_only / auth_required. |
| `failed_sources_and_failed_targets_limit_summary` | `must_display_caveat` | `ai_context_pack.json` | Widespread failures degrade the ability to summarize the market context. | `warning` | `snapshot_panel` | No | Show conditional warning if failures > 0. |
| `latest_snapshot_contains_no_successful_symbols` | `must_display_caveat` | `latest_market_snapshot.json` | The entire generated snapshot failed to retrieve any live target data. | `critical` | `snapshot_panel` | No | Show major warning; fallback to failed data views. |
| `session_detection_not_implemented_in_m3a_02` | `deferred_caveat_for_future_milestone` | `MARKET_SESSION_STATUS_SEMANTICS.md` | Market open/close status is not robustly detected yet. | `info` | `top_banner` | No | Display "Unknown Session" clearly. |
| `source_health_summary_describes_local_generated_source_state_only` | `must_display_caveat` | `ai_context_pack.json` | Errors reflect the local offline generation context, not live external API outages. | `info` | `source_health_panel` | No | Clarify "Offline Mode" context. |
| `does_not_claim_current_live_production_source_availability` | `must_display_caveat` | `ai_context_pack.json` | Do not assume source availability based on these static artifacts. | `info` | `source_health_panel` | No | Use static/offline labels. |
| `target_support_summary_describes_support_and_scope_not_market_movement` | `must_display_caveat` | `ai_context_pack.json` | The taxonomy overview does not imply market performance. | `info` | `scope_panel` | No | Clearly separate scope from snapshot data. |
| `target_support_summary_must_not_rank_target_classes_or_securities` | `must_display_caveat` | `ai_context_pack.json` | The frontend must not synthesize "top" or "best" lists from the target support array. | `critical` | `scope_panel` | No | Prohibit sorting/ranking UI elements. |
| `target_classes_include_failed_bounded_watchlist_targets` | `must_display_caveat` | `ai_context_pack.json` | Supported target classes might still map to individual failed symbol requests. | `info` | `scope_panel` | No | Display failures alongside support matrices. |