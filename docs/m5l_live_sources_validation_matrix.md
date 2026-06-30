# M5L live sources validation matrix

M5F remains the Level 1 canonical context. This report covers M5K/M5L Level 2 bounded live observation only. Live observations are explicit-only, do not run at startup, do not write M5F, do not write `frontend/public`, do not write `research/generated`, and do not create trading signals.

## Adapter overview

The machine-readable matrix is `config/m5l_live_source_adapter_matrix.json`.

| Adapter | Source | Instrument coverage | Decision | Product behavior |
|---|---|---|---|---|
| `twse_mis_equity_etf_quote` | TWSE MIS browser JSON | TWSE listed stocks, TWSE listed ETFs, TPEx/OTC stocks via `tse_*.tw` / `otc_*.tw` | accepted with caveats | normalized observation envelope only; no raw payload exposure |
| `twse_mis_taiex_index_quote` | TWSE MIS browser JSON | TAIEX via `tse_t00.tw` | accepted with caveats | same envelope and caveats as MIS quotes |
| `taifex_mis_tx_futures_quote` | TAIFEX MIS browser JSON | TX futures via bounded TXF query | accepted with caveats | includes contract, contract month, and selector |
| `twse_openapi_intraday_quote` | TWSE OpenAPI | TWSE reference/EOD | rejected for live observation | remains reference/EOD only |
| `licensed_vendor_future_candidate` | Fugle/Fubon/licensed vendor | potential broad coverage | future candidate | auth/terms/read-only design required |

## TWSE MIS listed stock, ETF, and TPEx/OTC route

- Source name: TWSE MIS.
- Source type: exchange-hosted browser JSON endpoint candidate, not an official SLA-backed realtime API.
- Endpoint family: `GET https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch={channels}&json=1&delay=0`.
- Required headers used by adapter: `User-Agent`, `Referer: https://mis.twse.com.tw/stock/fibest.jsp`.
- Listed stock route: `tse_2330.tw`.
- ETF route: `tse_0050.tw`.
- TPEx/OTC route: `otc_3483.tw`.
- Response format: JSON object with `msgArray` quote records when accepted. Batch requests join bounded `ex_ch` values with `|` before URL encoding; if the endpoint returns `rtcode=9999` or malformed `msgArray`, the adapter records `batch_request_failed` and falls back to individual bounded requests.
- Parsed fields: symbol/channel, numeric `z` last/current quote when available, numeric `y` reference fallback only when `z` is missing or non-numeric, `tlong`-preferred source timestamp with `d` + `t` Taipei-time fallback, retrieval UTC, source caveats. Numeric `y` fallback is `reference_value_only`, not a successful current trade observation.
- Raw payload retention: investigation-only during probe; product outputs retain normalized envelopes and bounded evidence metadata only.
- Freshness semantics: source date/time are displayed as source timestamp; retrieval time is UTC; no realtime claim is made.
- Legal/maintenance risk: medium because it is a browser endpoint and may change or be blocked.
- AI integration suitability: suitable for bounded observation with caveats; unsuitable as Level 1 canonical context.

Decision: accepted with caveats.

## TWSE MIS TAIEX route

- Endpoint: `GET https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_t00.tw&json=1&delay=0`.
- Parsed symbol: `TAIEX` from the configured instrument mapped to `tse_t00.tw`.
- Parsed value: the normalized `price_like_value` from the MIS value fields.
- Timestamp fields: same MIS `d` and `t` fields when present.
- Limitation: index channel differs from stock/ETF channels and may have different source availability behavior.

Decision: accepted with caveats.

## TAIFEX TX futures route

- Source name: TAIFEX MIS.
- Source type: TAIFEX-hosted browser JSON endpoint; not a licensed feed contract in this workbench.
- Endpoint: `POST https://mis.taifex.com.tw/futures/api/getQuoteList`.
- Body: `{"MarketType":"0","SymbolType":"F","KindID":"1","CID":"TXF"}`.
- Required headers used by adapter: `Content-Type`, `Accept`, `Origin`, `Referer`, `User-Agent`.
- Response format: JSON with `RtData.QuoteList`.
- Parsed fields: selected TXF front-month contract, last/settlement/reference fallback value, `CDate`, `CTime`, source status, display name, contract month.
- Freshness semantics: `CDate` + `CTime` is parsed as Taipei time; `delay_seconds` is computed against UTC retrieval when parseable.
- Limitation: front-month selection derives from source contract month display; closed-session status is displayed rather than hidden.

Decision: accepted with caveats.

## Probe evidence summary

The required bounded live probe command was:

```bash
python scripts/run_m5k_live_observation.py --execute-live-observation --watchlist /tmp/m5l_probe_watchlist.json --no-write-latest
```

The probe scope was exactly `2330`, `0050`, `TAIEX`, `3483`, and `TX`. Endpoint families used were TWSE MIS `getStockInfo.jsp` and TAIFEX MIS `getQuoteList`. See `research/probe_log.md#m5l-live-source-validation-2026-06-30` for timestamped command output summary and source-by-source result details.

## Endpoint acceptance/rejection rationale

Accepted-with-caveats endpoints are accepted because they can return parseable bounded observations and expose source timestamps or source status. Rows whose only numeric price-like field is MIS `y` are retained as reference-only evidence, not successful current trade observations. They remain caveated because browser endpoints can change, may be delayed, and do not provide a verified realtime SLA.

Rejected-for-live endpoints are rejected when they are EOD/reference sources rather than live observation sources. Future candidates require credentials, licensing, and read-only separation from broker/order functionality.

## Freshness and delay semantics

- `retrieved_at_utc`: UTC time at adapter retrieval.
- `source_timestamp`: source-reported timestamp when parseable or source date/time text when only text is available.
- `freshness_assessment`: adapter interpretation for observation display only.
- `delay_status`: explicit statement that realtime is not guaranteed.
- `delay_seconds`: present when computed; otherwise `null`.

## Future work

1. Add contracted/licensed read-only market data if terms permit.
2. Improve MIS source timestamp parsing for stock/ETF/index records when `tlong` is present.
3. Add fixture-backed regression cases for blocked/malformed source responses.
4. Keep raw payloads out of product surfaces while retaining bounded investigation notes in research documentation.
