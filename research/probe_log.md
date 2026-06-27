# Probe Execution Log

**Generated at (UTC):** `2026-06-20T11:04:07.251419+00:00`
**Generated at (Taipei):** `2026-06-20T19:04:07.251428+08:00`

## TWSE_OpenAPI (twse_openapi_20260620_110341)
- Contract Status: `normalized_pass`
- HTTP Status: 200

## TPEx_OpenAPI (tpex_openapi_20260620_110342)
- Contract Status: `normalized_pass`
- HTTP Status: 200

## Yahoo_Finance (yahoo_20260620_110350)
- Contract Status: `normalized_pass`
- HTTP Status: 200

## TWSE_MIS (twse_mis_20260620_110356)
- Contract Status: `normalized_pass`
- HTTP Status: 200

## FinMind (finmind_20260620_110357)
- Contract Status: `normalized_pass`
- HTTP Status: 200
- Errors: HTTP 422 for TaiwanFutureDaily:TX

## Fugle_MarketData (fugle_20260620_110407)
- Contract Status: `auth_required`
- HTTP Status: N/A

## Fubon_Neo_API (fubon_20260620_110407)
- Contract Status: `doc_only`
- HTTP Status: N/A



## M5B bounded TWSE_OpenAPI live probe — 2026-06-27T01:51:36Z

- Source name: TWSE_OpenAPI
- Source type: official_openapi
- URL: https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL
- Request method: GET
- Required headers/cookies/session: Accept: application/json; no cookies/session/credentials used
- Status code: 200
- Retained sample scope: only 0050, 00929, 2330 normalized rows retained under research/live_probe_runs/m5b/m5b_twse_openapi_20260627T015136Z/
- Parsed fields: symbol, name, trade_date, OHLC, change, trade_volume, trade_value, transaction_count, currency, freshness/delay flags
- Timestamp fields: retrieved_at_utc recorded per artifact; source trade_date retained when present
- Freshness assessment: EOD/reference, realtime not guaranteed
- Legal/maintenance risk: official public endpoint; schema drift and public rate limits possible
- AI integration suitability: bounded staging-only EOD/reference evidence; no production promotion or trading signal
