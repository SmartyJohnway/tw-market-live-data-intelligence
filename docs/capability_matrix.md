# Data Source Capability Matrix

**Generated at (UTC):** `2026-06-20T11:04:07.251419+00:00`
**Generated at (Taipei):** `2026-06-20T19:04:07.251428+08:00`
*Note: This report is automatically generated and displays live network probe results. Real-world target constraints and current API conditions apply.*

| Source | Source Type | URL/Endpoint | Auth | Session | Probe Status | HTTP | Parse | Norm | Freshness | Delay | Risk | AI Suitability | Usable Now | Unsupported | Failed | Notes | Last Verified |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TWSE_OpenAPI | official_openapi | https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL | No | No | `normalized_pass` | 200 | success | success | eod_batch | eod | low | historical_and_eod | **Yes** | 3 | 0 |  | 2026-06-20T11:03:42.595387+00:00 |
| TPEx_OpenAPI | official_openapi | https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes | No | No | `normalized_pass` | 200 | success | success | eod_batch | eod | low | historical_and_eod | **Yes** | 3 | 0 |  | 2026-06-20T11:03:50.779079+00:00 |
| Yahoo_Finance | unofficial_api | https://query1.finance.yahoo.com/v8/finance/chart/[symbol] | No | No | `normalized_pass` | 200 | success | success | realtime_candidate | stale | medium | live_watchlist | **Yes** | 2 | 0 | Rate limits apply, Not an official data source, Unofficial endpoint | 2026-06-20T11:03:56.384642+00:00 |
| TWSE_MIS | unofficial_frontend_endpoint | https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_2330.tw&#124;tse_1435.tw&#124;otc_8069.tw&#124;otc_5347.tw&#124;tse_0050.tw&#124;tse_00929.tw&#124;tse_9105.tw&#124;tse_t00.tw&json=1&delay=0&_=1781953437131 | No | Yes | `normalized_pass` | 200 | success | success | realtime_candidate | stale | high | live_watchlist | **Yes** | 2 | 0 | Strict rate limiting, Requires index.jsp visit for cookies, Not designed for API use, Unofficial endpoint | 2026-06-20T11:03:57.311587+00:00 |
| FinMind | commercial_api | https://api.finmindtrade.com/api/v4/data | Yes | No | `normalized_pass` | 200 | success | success | eod_batch | stale | low | historical_and_eod | **No** | 1 | 1 | Free tier rate limits apply | 2026-06-20T11:04:07.249370+00:00 |
| Fugle_MarketData | commercial_api | https://developer.fugle.tw/ | Yes | No | `auth_required` | N/A | unknown | unknown | unknown | unknown | low | live_streaming_capable | **No** | 0 | 0 | Requires personal API key | 2026-06-20T11:04:07.251236+00:00 |
| Fubon_Neo_API | broker_api | https://developer.fubon.com/ | Yes | No | `doc_only` | N/A | unknown | unknown | unknown | unknown | high | execution_capable_but_complex | **No** | 0 | 0 | Requires valid brokerage account, Requires certificate setup | 2026-06-20T11:04:07.251265+00:00 |

## M5B bounded live evidence capability note

| Source | Bounded targets | Live execution | Contract status | Freshness/delay | Production promotion | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| TWSE_OpenAPI | 2330, 0050, 00929 | Executed once | normalized_pass | EOD/reference; realtime not guaranteed | false | Staging-only evidence package; no non-target rows retained. |

## M5K capability matrix

| Capability | M5F Level 1 | M5K Level 2 |
| --- | --- | --- |
| Canonical context | Yes | No |
| Default startup network access | No | No |
| Explicit bounded observation | No | Yes |
| Watchlist import/export/edit | No | Yes |
| Conversation handoff | Stable context only | `m5k_conversation_handoff.v1` |
| Frontend publication | Governed M5D/M5F only | Never writes `frontend/public` |
| Promotion | Reviewed package promotion | Never automatic |
| Trading signals | Prohibited | Prohibited |

## M5L addition — TAIFEX TX live observation

| Source | Instrument | Capability | Status | Caveat |
| --- | --- | --- | --- | --- |
| TAIFEX MIS getQuoteList | TX / TXF front month | Bounded Level 2 live observation | Supported in M5K | Official browser endpoint; no verified real-time SLA; freshness/delay must be displayed. |
| TAIFEX OpenAPI DailyMarketReportFut | TX futures EOD/reference | Daily report/reference | Rejected for M5K live | No intraday live quote timestamp for current observation. |

## M5Q source-health regression capability

- Capability: manual bounded source-health regression report for representative TWSE MIS listed stock, TWSE MIS listed ETF, TWSE MIS TPEx/OTC, TWSE MIS TAIEX, and TAIFEX TX routes.
- Runner: `python scripts/run_m5q_source_health_probe.py --check-only` performs no network calls and no writes; `python scripts/run_m5q_source_health_probe.py --execute-health-probe` performs explicit bounded calls and writes normalized reports only under `research/live_observation_runs/source_health/`.
- Boundaries: no M5F mutation, no `frontend/public` write, no `research/generated` write, no polling, no scheduler, no full-market scan, no trading logic, and no raw endpoint payload in product-facing reports.
