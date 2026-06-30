# M5Q Source Health Report

- Schema: `m5q_source_health_report.v1`
- Generated at UTC: 2026-06-30T04:23:40Z
- Execution mode: explicit_health_probe
- Network calls may have occurred: True
- Bounded targets: 2330, 0050, 3483, TAIEX, TX

## Summary

- healthy: 2
- degraded: 3
- failed: 0
- unsupported: 0

## Checks

| Target | Source family | Adapter | Status | Observation status | Freshness | Delay | Caveats | Next step |
|---|---|---|---|---|---|---|---|---|
| 2330 | TWSE_MIS listed stock route | twse_mis_equity_etf_quote | degraded | reference_value_only | current observation candidate; realtime status not guaranteed by M5K | 10 | current_z_unavailable_y_reference_fallback_not_current_trade; fragile_frontend_contract; freshness_must_be_displayed; live_observation_not_canonical; no_trading_signal; not_official_realtime_api; not_realtime_guaranteed; source_may_be_delayed_or_unavailable; unofficial_source_risk | Do not infer a current trade value from reference-only or unavailable MIS fields; retry a bounded explicit observation later or inspect source availability. |
| 0050 | TWSE_MIS listed ETF route | twse_mis_equity_etf_quote | degraded | reference_value_only | current observation candidate; realtime status not guaranteed by M5K | 10 | current_z_unavailable_y_reference_fallback_not_current_trade; fragile_frontend_contract; freshness_must_be_displayed; live_observation_not_canonical; no_trading_signal; not_official_realtime_api; not_realtime_guaranteed; source_may_be_delayed_or_unavailable; unofficial_source_risk | Do not infer a current trade value from reference-only or unavailable MIS fields; retry a bounded explicit observation later or inspect source availability. |
| 3483 | TWSE_MIS TPEx / OTC route | twse_mis_equity_etf_quote | degraded | reference_value_only | current observation candidate; realtime status not guaranteed by M5K | 197 | current_z_unavailable_y_reference_fallback_not_current_trade; fragile_frontend_contract; freshness_must_be_displayed; live_observation_not_canonical; no_trading_signal; not_official_realtime_api; not_realtime_guaranteed; source_may_be_delayed_or_unavailable; unofficial_source_risk | Do not infer a current trade value from reference-only or unavailable MIS fields; retry a bounded explicit observation later or inspect source availability. |
| TAIEX | TWSE_MIS TAIEX route | twse_mis_taiex_index_quote | healthy | ok | current observation candidate; realtime status not guaranteed by M5K | 4 | fragile_frontend_contract; freshness_must_be_displayed; live_observation_not_canonical; no_trading_signal; not_official_realtime_api; not_realtime_guaranteed; source_may_be_delayed_or_unavailable; unofficial_source_risk | Source route usable for bounded observation; continue to display caveats and avoid realtime claims. |
| TX | TAIFEX TX route | taifex_mis_tx_futures_quote | healthy | ok | fresh | 0 | freshness_must_be_displayed; live_observation_not_canonical; no_realtime_sla_verified; no_trading_signal; not_realtime_guaranteed; official_browser_endpoint_not_openapi_contract; source_may_be_delayed_or_unavailable | Source route usable for bounded observation; continue to display caveats and avoid realtime claims. |

## Boundaries

No M5F mutation, frontend/public write, research/generated write, polling, scheduler, full-market scan, trading logic, or raw endpoint payload is included.
