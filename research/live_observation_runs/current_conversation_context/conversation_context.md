# M5N Conversation Context

## Executive Summary
Single governed AI conversation package for watchlist observation discussion; not canonical M5F and not raw endpoint payload.

Canonical Summary is Level 1 reviewed context. Latest Observation Summary is Level 2 bounded observation state. They are not the same.

## Watchlist Summary
- Watchlist: M5N Default Taiwan AI Watchlist Workspace (m5k_default_taiwan_ai_watchlist)
- Total symbols: 19
- Enabled symbols: 19
- Categories: taiwan_etf, taiwan_equity, index_and_futures

## Canonical Summary
- Canonical source: TWSE_OpenAPI
- Canonical source date: 2026-06-26
- Canonical symbols: 0050, 00929, 2330
- Caveats: not_realtime_guaranteed, not_trading_signal, not_production_current_state, source_risk_present, freshness_must_be_displayed

## Latest Observation Summary
- healthy=15 degraded=4 failed=0 unsupported=0 reference_only=3

## Healthy Observations
- 00878 00878: 32.9 (last_or_reference_value_as_reported_by_source); source=TWSE_MIS; freshness=current observation candidate; realtime status not guaranteed by M5K; delay=not_realtime_guaranteed
- 00919 00919: 29.46 (last_or_reference_value_as_reported_by_source); source=TWSE_MIS; freshness=current observation candidate; realtime status not guaranteed by M5K; delay=not_realtime_guaranteed
- 00929 00929: 29.99 (last_or_reference_value_as_reported_by_source); source=TWSE_MIS; freshness=current observation candidate; realtime status not guaranteed by M5K; delay=not_realtime_guaranteed
- 00934 00934: 27.78 (last_or_reference_value_as_reported_by_source); source=TWSE_MIS; freshness=current observation candidate; realtime status not guaranteed by M5K; delay=not_realtime_guaranteed
- 00939 00939: 21.26 (last_or_reference_value_as_reported_by_source); source=TWSE_MIS; freshness=current observation candidate; realtime status not guaranteed by M5K; delay=not_realtime_guaranteed
- 00940 00940: 12.48 (last_or_reference_value_as_reported_by_source); source=TWSE_MIS; freshness=current observation candidate; realtime status not guaranteed by M5K; delay=not_realtime_guaranteed
- 00981A 00981A: 29.94 (last_or_reference_value_as_reported_by_source); source=TWSE_MIS; freshness=current observation candidate; realtime status not guaranteed by M5K; delay=not_realtime_guaranteed
- 1569 1569: 44.9 (last_or_reference_value_as_reported_by_source); source=TWSE_MIS; freshness=current observation candidate; realtime status not guaranteed by M5K; delay=not_realtime_guaranteed
- 2317 2317: 246.5 (last_or_reference_value_as_reported_by_source); source=TWSE_MIS; freshness=current observation candidate; realtime status not guaranteed by M5K; delay=not_realtime_guaranteed
- 2324 2324: 34.2 (last_or_reference_value_as_reported_by_source); source=TWSE_MIS; freshness=current observation candidate; realtime status not guaranteed by M5K; delay=not_realtime_guaranteed
- 2603 2603: 184.0 (last_or_reference_value_as_reported_by_source); source=TWSE_MIS; freshness=current observation candidate; realtime status not guaranteed by M5K; delay=not_realtime_guaranteed
- 2609 2609: 51.4 (last_or_reference_value_as_reported_by_source); source=TWSE_MIS; freshness=current observation candidate; realtime status not guaranteed by M5K; delay=not_realtime_guaranteed
- 3293 3293: 769.0 (last_or_reference_value_as_reported_by_source); source=TWSE_MIS; freshness=current observation candidate; realtime status not guaranteed by M5K; delay=not_realtime_guaranteed
- 3543 3543: 28.6 (last_or_reference_value_as_reported_by_source); source=TWSE_MIS; freshness=current observation candidate; realtime status not guaranteed by M5K; delay=not_realtime_guaranteed
- TAIEX TAIEX: 44999.9 (last_or_reference_value_as_reported_by_source); source=TWSE_MIS; freshness=current observation candidate; realtime status not guaranteed by M5K; delay=not_realtime_guaranteed

## Degraded Observations
- 0050 0050: status=reference_value_only; observation_status=reference_value_only; freshness=current observation candidate; realtime status not guaranteed by M5K; reason=reference_value_only; next=Do not infer a current trade value from reference-only or unavailable MIS fields; retry a bounded explicit observation later or inspect source availability.
- 2330 2330: status=reference_value_only; observation_status=reference_value_only; freshness=current observation candidate; realtime status not guaranteed by M5K; reason=reference_value_only; next=Do not infer a current trade value from reference-only or unavailable MIS fields; retry a bounded explicit observation later or inspect source availability.
- 3483 3483: status=reference_value_only; observation_status=reference_value_only; freshness=current observation candidate; realtime status not guaranteed by M5K; reason=reference_value_only; next=Do not infer a current trade value from reference-only or unavailable MIS fields; retry a bounded explicit observation later or inspect source availability.
- TX TX futures: status=ok; observation_status=ok; freshness=stale_or_closed_session; reason=ok; next=Review caveats before AI discussion.

## Reference-only Observations
- 0050 0050: value_present=True; reason=reference_value_only; next=Do not infer a current trade value from reference-only or unavailable MIS fields; retry a bounded explicit observation later or inspect source availability.
- 2330 2330: value_present=True; reason=reference_value_only; next=Do not infer a current trade value from reference-only or unavailable MIS fields; retry a bounded explicit observation later or inspect source availability.
- 3483 3483: value_present=True; reason=reference_value_only; next=Do not infer a current trade value from reference-only or unavailable MIS fields; retry a bounded explicit observation later or inspect source availability.

## Failed Observations

## Source Health
- Status: available
- Summary: {'degraded': 3, 'failed': 0, 'healthy': 2, 'unsupported': 0}
- Degraded source families: TWSE_MIS TPEx / OTC route, TWSE_MIS listed ETF route, TWSE_MIS listed stock route
- Failed source families: none

## Current Caveats
- freshness_must_be_displayed
- live_observation_not_canonical
- manual_bounded_regression_probe
- no_polling_or_scheduler
- no_trading_signal
- not_live_scanner
- not_production_current_state
- not_realtime_guaranteed
- not_trading_signal
- raw_endpoint_payload_excluded
- source_may_be_delayed_or_unavailable
- source_risk_present

## Suggested Questions For AI
- 哪些資料目前可信？
- 哪些 observation 是 reference-only？
- 哪些 observation 不可視為 current price？
- 哪些來源 degraded？
- 哪些標的是 unavailable？
- Canonical Package 包含哪些內容？
- Latest Observation 包含哪些內容？
- 目前最大的資料限制是什麼？
- 下一步建議人工做什麼？
