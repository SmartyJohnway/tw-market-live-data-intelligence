# Data Source Catalog

**Generated at (UTC):** `2026-06-20T11:04:07.251419+00:00`
**Generated at (Taipei):** `2026-06-20T19:04:07.251428+08:00`
Generated automatically by probes. Details specific source capabilities.

## TWSE_OpenAPI

- **Type:** official_openapi
- **URL:** https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL
- **Contract Status:** `normalized_pass`
- **Usable Now:** True
- **Potentially Usable (Creds):** False
- **AI Suitability:** historical_and_eod
- **Delay Status:** eod
- **Unsupported targets:** indices, futures, funds

## TPEx_OpenAPI

- **Type:** official_openapi
- **URL:** https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes
- **Contract Status:** `normalized_pass`
- **Usable Now:** True
- **Potentially Usable (Creds):** False
- **AI Suitability:** historical_and_eod
- **Delay Status:** eod
- **Unsupported targets:** indices, futures, funds

## Yahoo_Finance

- **Type:** unofficial_api
- **URL:** https://query1.finance.yahoo.com/v8/finance/chart/[symbol]
- **Contract Status:** `normalized_pass`
- **Usable Now:** True
- **Potentially Usable (Creds):** False
- **AI Suitability:** live_watchlist
- **Delay Status:** stale
- **Staleness:** 192822 seconds
- **Warnings:** HTTP 404 for known unsupported placeholder TX.TW, HTTP 404 for known unsupported placeholder FUNDA.TW
- **Unsupported targets:** TX.TW, FUNDA.TW

## TWSE_MIS

- **Type:** unofficial_frontend_endpoint
- **URL:** https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_2330.tw|tse_1435.tw|otc_8069.tw|otc_5347.tw|tse_0050.tw|tse_00929.tw|tse_9105.tw|tse_t00.tw&json=1&delay=0&_=1781953437131
- **Contract Status:** `normalized_pass`
- **Usable Now:** True
- **Potentially Usable (Creds):** False
- **AI Suitability:** live_watchlist
- **Delay Status:** stale
- **Staleness:** 189236 seconds
- **Unsupported targets:** futures, funds

## FinMind

- **Type:** commercial_api
- **URL:** https://api.finmindtrade.com/api/v4/data
- **Contract Status:** `normalized_pass`
- **Usable Now:** False
- **Potentially Usable (Creds):** True
- **AI Suitability:** historical_and_eod
- **Delay Status:** stale
- **Staleness:** 212647 seconds
- **Errors:** HTTP 422 for TaiwanFutureDaily:TX
- **Unsupported targets:** funds
- **Failed targets:** TX

## Fugle_MarketData

- **Type:** commercial_api
- **URL:** https://developer.fugle.tw/
- **Contract Status:** `auth_required`
- **Usable Now:** False
- **Potentially Usable (Creds):** True
- **AI Suitability:** live_streaming_capable
- **Delay Status:** unknown
- **Warnings:** Not probed live due to missing configured credentials.

## Fubon_Neo_API

- **Type:** broker_api
- **URL:** https://developer.fubon.com/
- **Contract Status:** `doc_only`
- **Usable Now:** False
- **Potentially Usable (Creds):** True
- **AI Suitability:** execution_capable_but_complex
- **Delay Status:** unknown
- **Warnings:** Not probed live. Complex auth requirements.


## M5B bounded TWSE_OpenAPI execution evidence (2026-06-27)

TWSE_OpenAPI was probed once through the bounded M5B runner for targets 2330, 0050, and 00929 only. The official endpoint used was `https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL`; no credentials, cookies, fallback source, or full-market retention were used. The retained evidence is staging-only under `research/live_probe_runs/m5b/m5b_twse_openapi_20260627T015136Z/` and preserves EOD/reference semantics without any realtime guarantee.

## M5K source catalog additions

- **TWSE MIS**: official browser JSON endpoint candidate used only for explicit bounded M5K observation. Request method: GET. Required headers: local User-Agent plus TWSE MIS referer; no cookies or credentials are required by the implementation. Status code is recorded when execution occurs, but raw response samples and raw source fields are not exposed in AI/API/MCP/frontend payloads. Parsed consumer fields include symbol, source timestamp, price-like value, retrieval time, source, freshness assessment, and delay status. Maintenance risk: browser-oriented endpoint. AI suitability: good for bounded conversational observation with strong caveats; not canonical and not realtime-guaranteed.
- **TWSE OpenAPI STOCK_DAY_ALL**: official EOD/reference endpoint retained as a fallback preference for equities/ETFs. It is not used as M5K's primary current observation source because its semantics are EOD/batch.
- **TPEx OpenAPI**: official OTC source family retained as a future route for OTC-like instruments; not silently adopted for initial M5K live execution.
- **TAIFEX**: official futures source family required for TX futures, but initial M5K does not execute it until futures contract mapping and timestamp semantics are validated.
