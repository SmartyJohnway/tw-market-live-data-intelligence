# Probe Execution Log

Last Run: 2026-06-17T06:22:54.553312

## TWSE OpenAPI
- URL: https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL
- Status: 200
- Success: True

## TPEx OpenAPI
- URL: https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes
- Status: 200
- Success: True

## Yahoo Finance (TW)
- URL: https://query1.finance.yahoo.com/v8/finance/chart/
- Status: 6/6 OK
- Success: True
- Details: [{"symbol": "2330.TW", "status": 200, "success": true}, {"symbol": "1435.TW", "status": 200, "success": true}, {"symbol": "0050.TW", "status": 200, "success": true}, {"symbol": "00929.TW", "status": 200, "success": true}, {"symbol": "^TWII", "status": 200, "success": true}, {"symbol": "TWD=X", "status": 200, "success": true}]

## TWSE MIS
- URL: https://mis.twse.com.tw/stock/api/getStockInfo.jsp
- Status: 200
- Success: True

## FinMind
- URL: https://api.finmindtrade.com/api/v4/data
- Status: 5/6 OK
- Success: True
- Details: [{"dataset": "TaiwanStockPrice", "data_id": "2330", "status": 200, "success": true}, {"dataset": "TaiwanStockPrice", "data_id": "1435", "status": 200, "success": true}, {"dataset": "TaiwanStockPrice", "data_id": "0050", "status": 200, "success": true}, {"dataset": "TaiwanStockPrice", "data_id": "00929", "status": 200, "success": true}, {"dataset": "TaiwanStockPrice", "data_id": "TAIEX", "status": 200, "success": true}, {"dataset": "TaiwanFutureDaily", "data_id": "TX", "status": 422, "success": false}]

## Fugle MarketData
- URL: https://developer.fugle.tw/
- Status: Documentation Checked
- Success: True

## Fubon Neo API
- URL: https://developer.fubon.com/
- Status: Documentation Checked
- Success: True

