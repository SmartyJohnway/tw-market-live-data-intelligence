# TWSE MIS Protocol Documentation

## 1. Source Classification
- **Source Name:** TWSE MIS (Market Information System)
- **Source Type:** `unofficial_frontend_endpoint`
- **Classification Rationale:** The endpoint (`mis.twse.com.tw/stock/api/getStockInfo.jsp`) is designed to power the official web-based market information dashboard for human viewing. It is not an officially documented or officially supported public API. Access requires specific browser-like behavior and is subject to strict, undocumented rate limits and blocking mechanisms.

## 2. Endpoint and Request Flow
The typical request flow for probing this endpoint consists of two steps:
1. **Session Initialization:** Visiting the main `index.jsp` page to acquire session cookies.
2. **Data Query:** Requesting `getStockInfo.jsp` with a pipeline-separated list of symbols.

## 3. Session Initialization
- **Role of `index.jsp` / Session Cookies:** The TWSE MIS endpoint actively rejects or throttles requests that lack valid session cookies or present as headless bots. A preliminary GET request to `https://mis.twse.com.tw/stock/index.jsp` is observed to be strictly required to establish a JSESSIONID and pass basic bot mitigation checks before querying the data endpoint.

## 4. Request Parameters
The endpoint is queried using a URL structure similar to:
`https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=[channels]&json=1&delay=0&_=[timestamp]`

- **`ex_ch`:** The target parameter, structured as a pipe-separated (`|`) list of symbol channels (e.g., `tse_2330.tw|otc_8069.tw`).
- **`json=1`:** Instructs the endpoint to return the response payload in JSON format.
- **`delay=0`:** Historically observed to request real-time data or bypass delayed caching, though the actual delay behavior is dictated by the server and market session rules regardless of this parameter.
- **`_` (Timestamp / Cache-busting):** A Unix timestamp in milliseconds (`int(time.time() * 1000)`). Used to prevent browser caching and ensure fresh data is fetched from the server.

## 5. Symbol Channel Format
TWSE MIS requires a specific composite format for querying assets, combining the exchange segment, symbol, and `.tw` suffix:
- **TWSE (Large caps/ETFs):** Prefixed with `tse_` (e.g., `tse_2330.tw` for TSMC, `tse_0050.tw` for Yuanta Taiwan 50).
- **TPEx (OTC/Small caps):** Prefixed with `otc_` (e.g., `otc_8069.tw` for E Ink).
- **Indices:** Often use specific identifiers (e.g., `tse_t00.tw` for the TAIEX index).
- **Multiple Symbols:** Joined using the pipe character `|` in a single request to reduce HTTP overhead.

## 6. Response Structure
The endpoint returns a JSON object. The most critical component is the `msgArray`, which contains a list of objects representing the current quote/snapshot for each requested channel.
- **High-level shape:** The array elements are flat JSON objects with highly abbreviated, single-letter or short-string keys (e.g., `c`, `z`, `v`, `tlong`).
- A successful response will typically have `"rtmessage": "OK"` and a populated `msgArray`.

## 7. Intraday vs. Post-Market Behavior
Observed responses heavily depend on the market session context:
- **Intraday:** Certain fields representing the "last trade" or current volume (like `z`, `tv`, `s`) may appear as `"-"` if no trade has occurred recently or during specific matching phases. Bid/ask ladders are generally populated.
- **Post-Market:** Fields that were `"-"` intraday are typically populated with final closing data. Additionally, post-market specific fields (such as `oa`, `ob`, `oz`, `ov`, `fv`) may appear, indicating after-hours trading metrics.

## 8. Asset-Type Differences
The schema of the returned objects in `msgArray` varies depending on the asset class:
- **Stocks / ETFs:** Typically include detailed bid/ask ladders (`a`, `b`, `f`, `g`) and explicit trade volumes (`tv`, `v`). ETF rows may include specific fields like `nu`.
- **Indices:** Rows like `tse_t00.tw` (TAIEX) have a fundamentally different shape. They do not have bid/ask ladders and may omit several stock-specific fields.

## 9. Timestamp Semantics
TWSE MIS provides multiple timestamp fields that must be interpreted carefully:
- **`d` (Date):** The trading date (e.g., `"20231025"`).
- **`t` (Time):** The source-reported time of the quote, usually reflecting the market session time.
- **`tlong` (Source Time MS):** An epoch timestamp (in milliseconds) representing the time the data was generated or last updated by the exchange system.
- **`queryTime.sysTime` / `userDelay` / `cachedAlive`:** Internal system telemetry fields indicating when the server processed the request and how long it was cached.
- **Derived Real-time Context:** The project derives `staleness_seconds` by comparing `tlong` to the `retrieved_at_utc` time. A classification of "realtime_candidate" or a specific `delay_status` relies on this derived calculation, not a guarantee from the source. **Data is not guaranteed to be real-time.**

## 10. Risk and Suitability
- **Known Fragility & Blocking Risk:** As an unofficial frontend endpoint, TWSE MIS enforces strict rate limiting. Requests without proper headers, cookies, or that are issued too frequently will result in IP blocks or CAPTCHA redirects.
- **Bounded Low-Frequency Usage:** It is **only suitable** for bounded, low-frequency, watchlist-style AI market discussion contexts where freshness and caveats are explicitly validated.
- **Not an Official Feed:** It **must not** be treated as an official production real-time API. It is fundamentally unsuitable for high-frequency trading, automated execution, or large-scale full-market scraping.

## 11. Non-Goals and Prohibited Uses
This repository's implementation of TWSE MIS probing explicitly prohibits:
- High-frequency polling or scheduled full-market scans.
- Use in automated trading, strategy execution, or for generating definitive buy/sell signals.
- Claiming or representing the data as officially sourced API guarantees.
- Bypassing security measures via public proxies, serverless pass-throughs, or credential sharing.
