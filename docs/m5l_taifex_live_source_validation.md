# M5L TAIFEX TX live source validation

Date of investigation: 2026-06-29 UTC. Scope: bounded TX futures live-observation feasibility for M5K Level 2 only; M5F canonical package and promotion semantics are unchanged.

## Validation result

Accepted for M5K bounded observation: TAIFEX MIS browser JSON endpoint `POST https://mis.taifex.com.tw/futures/api/getQuoteList` with body `{"MarketType":"0","SymbolType":"F","KindID":"1","CID":"TXF"}`.

This source is official TAIFEX-hosted browser infrastructure, but not TAIFEX OpenAPI. It is suitable for evidence-backed bounded observation with caveats, not for SLA-backed long-term production without TAIFEX licensing or written terms.

Live execution evidence captured in `research/live_observation_runs/m5k/m5l_taifex_tx_live_observation_evidence.json`:

- observed symbol: `TX`
- selected contract: `TXFG6-F`
- contract month: `202607`
- source display name: `TX076`
- observed value: `45550.0`
- source timestamp: `2026-06-29T13:44:59+08:00`
- retrieved at: `2026-06-29T17:06:49Z`
- freshness: `stale_or_closed_session`
- measured delay: `40910` seconds
- source status: `TC` (closed-session status as reported by source)

## Endpoint investigations

### 1. TAIFEX OpenAPI Swagger

- Source name: TAIFEX OpenAPI Swagger
- Source type: official machine-readable OpenAPI catalog
- URL: `https://openapi.taifex.com.tw/swagger.json`
- Request method: `GET`
- Headers: `User-Agent: tw-market probe`
- Status code: `200`
- Response format: JSON OpenAPI 3.0 document
- Sample response: document includes `servers: [{"url":"https://openapi.taifex.com.tw/v1"}]` and paths such as `/DailyMarketReportFut` and `/TimeAndSalesData`.
- Timestamp fields: catalog metadata only; no quote timestamp.
- Freshness assessment: documentation/source catalog, not a live quote source.
- Authentication requirement: none observed.
- Legal/maintenance risk: low for documented API discovery.
- AI integration suitability: useful for official source discovery; insufficient alone for live TX observation.

### 2. TAIFEX OpenAPI DailyMarketReportFut

- Source name: TAIFEX OpenAPI DailyMarketReportFut
- Source type: official public OpenAPI endpoint, daily market report
- URL: `https://openapi.taifex.com.tw/v1/DailyMarketReportFut`
- Request method: `GET`
- Headers: `Accept: application/json`, `User-Agent: tw-market probe`
- Status code: `200`
- Response format: JSON array served as `application/octet-stream`
- Sample response: first rows on probe included `Date: 20260626`, contracts such as `ZFF`, `ContractMonth(Week): 202607`, `Last`, `SettlementPrice`, `BestBid`, `BestAsk`, and `TradingSession`.
- Timestamp fields: `Date` only; no intraday source time.
- Freshness assessment: prior trading-day daily report during 2026-06-29 probe; not live.
- Authentication requirement: none observed.
- Stable: likely stable as official OpenAPI report.
- Long-term suitability: useful EOD/reference data; rejected for M5K live TX observation because it does not provide current intraday TX quote time.

### 3. TAIFEX OpenAPI TimeAndSalesData

- Source name: TAIFEX OpenAPI TimeAndSalesData
- Source type: official public OpenAPI endpoint, historical/time-and-sales report
- URL: `https://openapi.taifex.com.tw/v1/TimeAndSalesData`
- Request method: `GET`
- Headers: `Accept: application/json`, `User-Agent: tw-market probe`
- Status code: `200`
- Response format: JSON array served as `application/octet-stream`
- Sample response: rows included `Date: 20260625`, `ProductCode: BRF`, `ContractMonth(Week): 202608`, `TimeOfTrades`, `TradePrice`, and `Volume(Buy+Sell)`.
- Timestamp fields: `Date`, `TimeOfTrades`.
- Freshness assessment: historical data; first sampled rows were not TX and not current live observation.
- Authentication requirement: none observed.
- Stable: official OpenAPI, but response is broad report data rather than bounded quote lookup.
- Long-term suitability: useful for backfill/verification; rejected as the primary M5K live quote adapter.

### 4. TAIFEX MIS browser app

- Source name: TAIFEX futures market quotes website
- Source type: official TAIFEX browser-rendered quote site
- URL: `https://mis.taifex.com.tw/futures/`
- Request method: `GET`
- Headers: `User-Agent: Mozilla/5.0`
- Status code: `200`
- Response format: HTML Nuxt app
- Sample response: HTML title `臺灣期貨交易所行情資訊網`; scripts reference `/futures/_nuxt/...` and `https://mis.taifex.com.tw/futures/rtCore`.
- Timestamp fields: none in shell HTML.
- Freshness assessment: browser app shell only.
- Authentication requirement: none observed.
- Stable: official site but implementation details can change.
- Long-term suitability: useful for discovering official browser endpoints and for visual comparison.

### 5. TAIFEX MIS getMenuJson

- Source name: TAIFEX MIS menu JSON
- Source type: official browser JSON endpoint
- URL: `https://mis.taifex.com.tw/futures/api/getMenuJson`
- Request method: `POST`
- Headers: `Content-Type: application/json;charset=UTF-8`, `Origin: https://mis.taifex.com.tw`, `Referer: https://mis.taifex.com.tw/futures/`
- Status code: `200`
- Response format: JSON
- Sample response: `RegularSession.EquityIndices.FuturesDomestic.pageAttr` includes `MarketType: 0`, `SymbolType: F`, `KindID: 1`, `CID: ""`, `ExpireMonth: ""`.
- Timestamp fields: none.
- Freshness assessment: route metadata, not quotes.
- Authentication requirement: none observed.
- Stable: useful route discovery; browser endpoint risk remains.
- Long-term suitability: accepted as route-planning evidence, not quote source.

### 6. TAIFEX MIS getQuoteList, all quotes

- Source name: TAIFEX MIS getQuoteList unfiltered
- Source type: official browser JSON endpoint
- URL: `https://mis.taifex.com.tw/futures/api/getQuoteList`
- Request method: `POST`
- Request body: `{}`
- Headers: `Content-Type: application/json;charset=UTF-8`, `Origin: https://mis.taifex.com.tw`, `Referer: https://mis.taifex.com.tw/futures/RegularSession/EquityIndices/FuturesDomestic`
- Status code: `200`
- Response format: JSON
- Sample response: `RtCode: 0`, `RtData.QuoteCount: 19180`, first symbols included `TXF-P` and `TXF-S`.
- Timestamp fields: quote rows include `CDate`, `CTime`, `CTestTime`.
- Freshness assessment: live quote table candidate, but unbounded all-quote call is not acceptable for M5K bounded observation.
- Authentication requirement: none observed.
- Stable: endpoint worked, but all-market scope rejected.
- Long-term suitability: rejected for product use because M5K must stay bounded.

### 7. TAIFEX MIS getQuoteList, domestic index futures

- Source name: TAIFEX MIS getQuoteList domestic index futures
- Source type: official browser JSON endpoint
- URL: `https://mis.taifex.com.tw/futures/api/getQuoteList`
- Request method: `POST`
- Request body: `{"MarketType":"0","SymbolType":"F","KindID":"1"}`
- Status code: `200`
- Response format: JSON
- Sample response: `RtCode: 0`, `QuoteCount: 106`, rows included `TXF-S`, `TXFG6-F`, `TXFH6-F`.
- Timestamp fields: `CDate`, `CTime`, `CTestTime`.
- Freshness assessment: useful scoped category quote source, still broader than the single TX product.
- Authentication requirement: none observed.
- Stable: endpoint worked.
- Long-term suitability: acceptable as fallback investigation path, but TXF-filtered endpoint is better bounded.

### 8. TAIFEX MIS getQuoteList, TXF product filter

- Source name: TAIFEX MIS getQuoteList TXF
- Source type: official browser JSON endpoint
- URL: `https://mis.taifex.com.tw/futures/api/getQuoteList`
- Request method: `POST`
- Request body: `{"MarketType":"0","SymbolType":"F","KindID":"1","CID":"TXF"}`
- Status code: `200`
- Response format: JSON
- Sample response: `QuoteCount: 7`, rows included spot `TXF-S` and futures `TXFG6-F`, `TXFH6-F`, `TXFI6-F`, `TXFL6-F`, `TXFC7-F`, `TXFF7-F`.
- Parsed fields: `SymbolID`, `DispCName`, `DispEName`, `Status`, `CLastPrice`, `CDate`, `CTime`, `SettlementPrice`, `OpenInterest`, bid/ask fields.
- Timestamp fields: `CDate`, `CTime`, `CTestTime`.
- Freshness assessment: accepted as M5K observation candidate. The captured live run occurred after close; source status `TC` and measured delay are displayed rather than hidden.
- Authentication requirement: none observed.
- Stable: endpoint worked; browser endpoint may change and has no verified API SLA.
- Long-term suitability: suitable for bounded M5K observation with caveats; for production-grade long-term usage, apply for licensed TAIFEX market data or formal API terms.

### 9. TAIFEX MIS getQuoteList, wrong `CID: TX`

- Source type: official browser JSON endpoint negative probe
- Request body: `{"MarketType":"0","SymbolType":"F","KindID":"1","CID":"TX"}`
- Status code: `200`
- Response format: JSON
- Sample response: `{"RtCode":"2","RtMsg":"查無資料","RtData":{"QuoteCount":"","QuoteList":[]}}`
- Rejection: confirms product code is `TXF` for this endpoint; repository must not guess that `TX` is the endpoint code.

### 10. TAIFEX MIS getQuotes/getQuote/getQuoteData wrong endpoint probes

- Source type: official host negative endpoint probes
- URLs: `/futures/api/getQuotes`, `/futures/api/getQuote`, `/futures/api/getQuoteData`
- Request method: `POST`
- Status code: `404`
- Sample failure: `{"status":404,"error":"Not Found","path":"/futures/api/getQuote"}`
- Rejection: not valid endpoints.

### 11. TAIFEX MIS getQuoteDetail wrong body probe

- Source type: official browser JSON endpoint negative/body-shape probe
- URL: `https://mis.taifex.com.tw/futures/api/getQuoteDetail`
- Request method: `POST`
- Status code: `200` with empty `QuoteList` for broad bodies; `400` for `{"SymbolID":"TXF"}` because server expected a list-shaped field.
- Rejection: not needed for top-level TX live observation; retained as failure evidence.

## Contract semantics

- User-facing `TX` is a desired instrument symbol in this repository, not the TAIFEX MIS product filter.
- TAIFEX MIS product filter for TAIEX futures is `CID=TXF`.
- `TXF-S` is the TAIEX spot row and is not a futures contract.
- Futures contract rows observed end in `-F`, for example `TXFG6-F`.
- The source display `TX076` maps to July 2026 (`202607`) in the 2026-06-29 run. The adapter derives `contract_month` from `DispEName` as `TX` + two-digit month + one-digit year.
- M5K treats repository symbol `TX` as `TXF front_month` unless a future watchlist explicitly requests a different selector.
- Weekly contracts and options were not selected for TX futures observation. They must be represented as distinct instruments/selectors if added later.
- Continuous contracts are not a TAIFEX source concept in this endpoint. A continuous series would be derived data and must not be silently substituted for a specific observed contract.

## Normalization logic

The M5K adapter filters `QuoteList` to rows where `SymbolID` starts with `TXF`, ends with `-F`, and has a parseable contract month. It sorts by contract month and selects the nearest/front month. It emits:

- `symbol`: repository symbol `TX`
- `contract`: source contract symbol such as `TXFG6-F`
- `contract_month`: normalized `YYYYMM`, e.g. `202607`
- `value`: numeric `CLastPrice`, with settlement/reference fallback only if last is absent
- `timestamp`: exposed as `source_timestamp`
- `retrieved_at`: exposed as `retrieved_at_utc`
- `delay`: measured seconds between retrieval UTC and source timestamp when parseable
- `freshness`: `fresh` if within 900 seconds, otherwise `stale_or_closed_session`
- `source`: `TAIFEX`

## Recommendation

Use the accepted TAIFEX MIS `getQuoteList` TXF route for bounded M5K live observation now, with visible freshness/delay/source caveats. Do not promote it to M5F and do not claim real-time unless future evidence verifies TAIFEX terms and delivery delay. For long-term product usage, obtain TAIFEX market data licensing/API documentation and replace the browser endpoint with a contracted feed or official supported API if available.
