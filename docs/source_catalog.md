# Data Source Catalog

**Generated at (UTC):** `2026-06-18T08:34:19.075822+00:00`
**Generated at (Taipei):** `2026-06-18T16:34:19.075831+08:00`
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
- **Contract Status:** `failed`
- **Usable Now:** False
- **Potentially Usable (Creds):** False
- **AI Suitability:** unknown
- **Delay Status:** unknown
- **Errors:** Response ended prematurely

## Yahoo_Finance

- **Type:** unofficial_api
- **URL:** https://query1.finance.yahoo.com/v8/finance/chart/[symbol]
- **Contract Status:** `normalized_pass`
- **Usable Now:** True
- **Potentially Usable (Creds):** False
- **AI Suitability:** live_watchlist
- **Delay Status:** delayed
- **Staleness:** 11040 seconds
- **Errors:** HTTP 404 for TX.TW, HTTP 404 for FUNDA.TW
- **Failed targets:** TX.TW, FUNDA.TW

## TWSE_MIS

*(See also: [TWSE MIS Protocol](protocol/TWSE_MIS_PROTOCOL.md) and [Field Dictionary](protocol/TWSE_MIS_FIELD_DICTIONARY.md))*

- **Type:** unofficial_frontend_endpoint
- **URL:** https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_2330.tw|tse_1435.tw|otc_8069.tw|otc_5347.tw|tse_0050.tw|tse_00929.tw|tse_9105.tw|tse_t00.tw&json=1&delay=0&_=1781771649033
- **Contract Status:** `normalized_pass`
- **Usable Now:** True
- **Potentially Usable (Creds):** False
- **AI Suitability:** live_watchlist
- **Delay Status:** delayed
- **Staleness:** 7449 seconds
- **Unsupported targets:** futures, funds

## FinMind

- **Type:** commercial_api
- **URL:** https://api.finmindtrade.com/api/v4/data
- **Contract Status:** `normalized_pass`
- **Usable Now:** False
- **Potentially Usable (Creds):** True
- **AI Suitability:** historical_and_eod
- **Delay Status:** eod
- **Staleness:** 30859 seconds
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

