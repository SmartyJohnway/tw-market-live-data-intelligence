# Data Source Capability Matrix

| Source | Type | Endpoint/URL | Contract Status | AI Suitability |
|---|---|---|---|---|
| TWSE_OpenAPI | official_openapi | https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL | `http_pass` | historical_and_eod |
| TPEx_OpenAPI | official_openapi | https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes | `http_pass` | historical_and_eod |
| Yahoo_Finance | public_api | https://query1.finance.yahoo.com/v8/finance/chart/ | `normalized_pass` | live_watchlist |
| TWSE_MIS | unofficial_frontend_endpoint | https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_2330.tw|tse_1435.tw|tse_0050.tw|tse_00929.tw|tse_t00.tw|otc_o00.tw&json=1&delay=0&_=1781685824640 | `normalized_pass` | live_watchlist |
| FinMind | commercial_api | https://api.finmindtrade.com/api/v4/data | `normalized_pass` | historical_and_eod |
| Fugle_MarketData | commercial_api | https://developer.fugle.tw/ | `auth_required` | live_streaming_capable |
| Fubon_Neo_API | broker_api | https://developer.fubon.com/ | `doc_only` | execution_capable_but_complex |
