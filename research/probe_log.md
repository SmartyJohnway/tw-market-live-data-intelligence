# Probe Execution Log

Last Run: 2026-06-17T09:50:58.528844+00:00

## TWSE_OpenAPI (twse_openapi_20260617_095033)
- URL: https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL
- Contract Status: `normalized_pass`
- HTTP Status: 200

## TPEx_OpenAPI (tpex_openapi_20260617_095035)
- URL: https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes
- Contract Status: `normalized_pass`
- HTTP Status: 200

## Yahoo_Finance (yahoo_20260617_095046)
- URL: https://query1.finance.yahoo.com/v8/finance/chart/
- Contract Status: `normalized_pass`
- HTTP Status: 200
- Risks: Rate limits apply, Not an official data source

## TWSE_MIS (twse_mis_20260617_095050)
- URL: https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_2330.tw|tse_1435.tw|tse_0050.tw|tse_00929.tw|tse_t00.tw|otc_o00.tw&json=1&delay=0&_=1781689851449
- Contract Status: `normalized_pass`
- HTTP Status: 200
- Risks: Strict rate limiting, Requires index.jsp visit for cookies, Not designed for API use

## FinMind (finmind_20260617_095051)
- URL: https://api.finmindtrade.com/api/v4/data
- Contract Status: `normalized_pass`
- HTTP Status: 200
- Risks: Free tier rate limits apply

## Fugle_MarketData (fugle_20260617_095058)
- URL: https://developer.fugle.tw/
- Contract Status: `auth_required`
- HTTP Status: N/A
- Risks: Requires personal free tier or paid API key, Good WebSocket streaming

## Fubon_Neo_API (fubon_20260617_095058)
- URL: https://developer.fubon.com/
- Contract Status: `doc_only`
- HTTP Status: N/A
- Risks: Requires valid brokerage account, Requires certificate setup

