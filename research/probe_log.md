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

## M5K source investigation log

- TWSE MIS bounded quote endpoint was selected as the initial M5K current-observation candidate for listed equities, ETFs, and TAIEX. Probe execution is explicit only through M5K APIs/CLI, records URL, status code when available, parsed consumer fields, source timestamp, retrieval timestamp, freshness caveat, maintenance risk, and AI suitability in the observation payload; raw response samples and raw source fields are intentionally omitted from consumer payloads.
- TWSE OpenAPI `STOCK_DAY_ALL` remains an official EOD endpoint and is documented as a fallback preference, but rejected as the primary M5K live observation feed because it does not provide an intraday live guarantee.
- TPEx OpenAPI remains a documented future route for OTC-like instruments; initial M5K avoids unverified automatic routing.
- TAIFEX is required for TX futures, but rejected for initial execution until a contract-month mapping and endpoint contract are validated. TX futures therefore appears as an explicit unsupported observation failure rather than fabricated data.

## M5K live observation probe — 2026-06-29T14:43:25Z

- Command: `python scripts/run_m5k_live_observation.py --execute-live-observation --no-write-latest --watchlist config/m5k_default_watchlist.json`
- Endpoint used: TWSE MIS bounded request only, `https://mis.twse.com.tw/stock/api/getStockInfo.jsp?...&json=1&delay=0`; no endpoint/source outside current repository assumptions was used.
- Route plan summary: TWSE instruments used `tse_<symbol>.tw`; TPEx/OTC instruments used `otc_<symbol>.tw`; TAIEX used `tse_t00.tw`; TX futures remained unsupported through TAIFEX pending contract mapping.
- Observation result: 16 observations, 3 failures.
- Sample rows: 2330 observed via TWSE_MIS at source timestamp `20260629 13:30:00`; 0050 observed via TWSE_MIS at source timestamp `20260629 13:30:00`; TAIEX observed via TWSE_MIS route `tse_t00.tw` at source timestamp `20260629 13:33:00`; TPEx/OTC sample 1569 observed via TWSE_MIS route `otc_1569.tw` at source timestamp `20260629 13:30:00`.
- Failures: 3483 missing from `tse_3483.tw`; 3543 missing from `otc_3543.tw`; TX futures returned `unsupported_in_m5k_initial` because TAIFEX contract-month mapping is not yet implemented.
- Governance: no M5F write, no `frontend/public` write, no `research/generated` write, no trading recommendation/ranking/target price/order content, and no raw response sample retained in consumer payload.

## M5K routing correction live observation probe — 2026-06-29T15:01:36Z

- Command: `python scripts/run_m5k_live_observation.py --execute-live-observation --no-write-latest --watchlist config/m5k_default_watchlist.json`
- Endpoint used: TWSE MIS bounded request only, `https://mis.twse.com.tw/stock/api/getStockInfo.jsp?...&json=1&delay=0`; no endpoint/source outside current repository assumptions was used.
- Corrected route assertions: 3483 力致 used `otc_3483.tw` and no longer requested `tse_3483.tw`; 3543 州巧 used `tse_3543.tw` and no longer requested `otc_3543.tw`; TX futures remained `unsupported_in_m5k_initial`.
- Observation result after metadata fix: 18 observations, 1 failure.
- Newly recovered sample rows: 3483 observed via TWSE_MIS route `otc_3483.tw` at source timestamp `20260629 13:30:00`; 3543 observed via TWSE_MIS route `tse_3543.tw` at source timestamp `20260629 13:30:00`.
- Remaining failure: TX futures only, because TAIFEX contract-month mapping and endpoint semantics are not implemented in M5K initial execution.

## 2026-06-29 M5L TAIFEX TX live source validation

Performed low-frequency official TAIFEX probing for TX futures. Accepted bounded M5K source: `POST https://mis.taifex.com.tw/futures/api/getQuoteList` with `CID=TXF`. Live run selected `TXFG6-F`, contract month `202607`, value `45550.0`, source timestamp `2026-06-29T13:44:59+08:00`, retrieved at `2026-06-29T17:06:49Z`, freshness `stale_or_closed_session`, source status `TC`. Full evidence: `research/live_observation_runs/m5k/m5l_taifex_tx_live_observation_evidence.json`; full validation: `docs/m5l_taifex_live_source_validation.md`.

## M5L live source validation 2026-06-30

- Task: M5L-LIVE-SOURCES-VALIDATION-AND-ADAPTER-MATRIX.
- Command: `python scripts/run_m5k_live_observation.py --execute-live-observation --watchlist /tmp/m5l_probe_watchlist.json --no-write-latest`.
- Requested symbols: `2330`, `0050`, `TAIEX`, `3483`, `TX`.
- Endpoint families: TWSE MIS `getStockInfo.jsp`; TAIFEX MIS `getQuoteList`.
- Request mode: explicit, bounded, one-shot; no full-market scan; no polling; no scheduler.
- Raw payload policy: raw endpoint bodies were not committed; product output contains normalized envelopes and bounded investigation metadata only.
- Decision summary: TWSE listed stock, ETF, TPEx/OTC, TAIEX, and TAIFEX TX routes are accepted with caveats for Level 2 observation only.
- Freshness interpretation: source timestamps are displayed where available; delay is not a realtime SLA; M5F was not mutated.

### M5L bounded probe result details

- Timestamp: `2026-06-30T01:08:31Z`.
- Observations count: `5`.
- Failures count: `0`.
- Parsed observations:
  - `TX` via `taifex_mis_tx_futures_quote`: value `46390.0`, source timestamp `2026-06-30T09:08:35+08:00`, retrieved `2026-06-30T01:08:31Z`, freshness `fresh`, delay `delay_seconds_measured_from_source_timestamp_not_exchange_realtime_sla`.
  - `2330` via `twse_mis_equity_etf_quote`: value `2470.0`, source timestamp `20260630 09:08:30`, retrieved `2026-06-30T01:08:31Z`, freshness `current observation candidate; realtime status not guaranteed by M5K`, delay `not_realtime_guaranteed`.
  - `0050` via `twse_mis_equity_etf_quote`: value `None`, source timestamp `20260630 09:08:29`, retrieved `2026-06-30T01:08:31Z`, freshness `current observation candidate; realtime status not guaranteed by M5K`, delay `not_realtime_guaranteed`.
  - `TAIEX` via `twse_mis_taiex_index_quote`: value `46284.81`, source timestamp `20260630 09:08:25`, retrieved `2026-06-30T01:08:31Z`, freshness `current observation candidate; realtime status not guaranteed by M5K`, delay `not_realtime_guaranteed`.
  - `3483` via `twse_mis_equity_etf_quote`: value `None`, source timestamp `20260630 09:08:30`, retrieved `2026-06-30T01:08:31Z`, freshness `current observation candidate; realtime status not guaranteed by M5K`, delay `not_realtime_guaranteed`.
- Limitations: observed values are Level 2 bounded observations only; MIS browser endpoint and TAIFEX browser JSON endpoint are not asserted as realtime SLA feeds.
