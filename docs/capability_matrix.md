# Data Source Capability Matrix

**Generated at (UTC):** `2026-06-18T15:55:20.199107+00:00`
**Generated at (Taipei):** `2026-06-18T23:55:20.199159+08:00`
*Note: This report is automatically generated and displays live network probe results. Real-world target constraints and current API conditions apply.*

| Source | Source Type | URL/Endpoint | Auth | Session | Probe Status | HTTP | Parse | Norm | Freshness | Delay | Risk | AI Suitability | Usable Now | Unsupported | Failed | Notes | Last Verified |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TWSE_OpenAPI | official_openapi | https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL | No | No | `normalized_pass` | 200 | success | success | eod_batch | eod | low | historical_and_eod | **Yes** | 3 | 0 |  | 2026-06-18T15:54:53.819464+00:00 |
| TPEx_OpenAPI | official_openapi | https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes | No | No | `normalized_pass` | 200 | success | success | eod_batch | eod | low | historical_and_eod | **Yes** | 3 | 0 |  | 2026-06-18T15:55:03.832734+00:00 |
| Yahoo_Finance | unofficial_api | https://query1.finance.yahoo.com/v8/finance/chart/[symbol] | No | No | `normalized_pass` | 200 | success | success | realtime_candidate | delayed | medium | live_watchlist | **Yes** | 2 | 0 | Rate limits apply, Not an official data source, Unofficial endpoint | 2026-06-18T15:55:09.389031+00:00 |
| TWSE_MIS | unofficial_frontend_endpoint | https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_2330.tw&#124;tse_1435.tw&#124;otc_8069.tw&#124;otc_5347.tw&#124;tse_0050.tw&#124;tse_00929.tw&#124;tse_9105.tw&#124;tse_t00.tw&json=1&delay=0&_=1781798110083 | No | Yes | `normalized_pass` | 200 | success | success | realtime_candidate | delayed | high | live_watchlist | **Yes** | 2 | 0 | Strict rate limiting, Requires index.jsp visit for cookies, Not designed for API use, Unofficial endpoint | 2026-06-18T15:55:10.246364+00:00 |
| FinMind | commercial_api | https://api.finmindtrade.com/api/v4/data | Yes | No | `normalized_pass` | 200 | success | success | eod_batch | eod | low | historical_and_eod | **No** | 1 | 1 | Free tier rate limits apply | 2026-06-18T15:55:20.197279+00:00 |
| Fugle_MarketData | commercial_api | https://developer.fugle.tw/ | Yes | No | `auth_required` | N/A | unknown | unknown | unknown | unknown | low | live_streaming_capable | **No** | 0 | 0 | Requires personal API key | 2026-06-18T15:55:20.198931+00:00 |
| Fubon_Neo_API | broker_api | https://developer.fubon.com/ | Yes | No | `doc_only` | N/A | unknown | unknown | unknown | unknown | high | execution_capable_but_complex | **No** | 0 | 0 | Requires valid brokerage account, Requires certificate setup | 2026-06-18T15:55:20.198961+00:00 |
