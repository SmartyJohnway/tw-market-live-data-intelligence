# Yahoo Finance Chart Protocol

## 1. Source Name
Yahoo Finance

## 2. Source Type and Risk Classification
**Source Type:** `unofficial_api`
**Classification:** `third_party_public_chart_endpoint`

**Risk and Usage Notes:**
Yahoo Finance is useful for providing low-frequency watchlist data and broad historical chart context. However, it must **not** be treated as an official exchange data source (such as TWSE or TPEx). Because this is an observed, unofficial public frontend endpoint rather than a formal API contract:
- Rate limits strictly apply and are typically undocumented.
- The schema may change without notice.
- The timestamps, latency guarantees, and coverage must not be used as execution-grade or backtest-grade sources without independent third-party validation.
- Missing fields, delayed data, or unannounced symbol delistings are common.

## 3. Endpoint Shape
**Base URL:** `https://query1.finance.yahoo.com/v8/finance/chart/{symbol}`

## 4. Request Parameters
Currently used by this repository:
- `symbol`: The asset identifier, typically using `.TW` or `.TWO` suffixes for Taiwan equities.
- No other explicit query parameters are routinely utilized in the core probe other than standard `User-Agent` headers to satisfy basic frontend proxy rules.

## 5. Supported Interval and Range Semantics
While not explicitly requested via URL params in the default probe, the endpoint natively supports parameters such as `interval` and `range` (e.g., `interval=1m`, `range=1d`). The default response typically returns 1-day range and 1-minute interval granularity.

## 6. Response Shape (High Level)
The response is structured as a JSON document:
```json
{
  "chart": {
    "result": [
      {
        "meta": { ... },
        "timestamp": [ ... ],
        "indicators": {
          "quote": [ { ... } ],
          "adjclose": [ { ... } ]
        }
      }
    ],
    "error": null
  }
}
```

## 7. Important JSON Fields
- `chart.result`: Array containing the primary payload. Typically 1 element for a single symbol.
- `meta`: Contains current market state details, including `symbol`, `regularMarketPrice`, `regularMarketTime`, `exchangeName`, `timezone`, and `currency`.
- `timestamp`: Array of epoch integers aligning chronologically with quotes.
- `indicators.quote`: Array of objects containing arrays for `open`, `high`, `low`, `close`, and `volume`.
- `indicators.adjclose`: Array containing split/dividend-adjusted close prices.
- `chart.error`: Contains error details (e.g., `code: Not Found`) when requests fail.

## 8. Timezone and Timestamp Semantics
- Timestamps are provided as UTC Unix epoch integers (e.g., `1781760608`).
- The `meta` block explicitly defines the local exchange timezone via `exchangeTimezoneName` (e.g., `Asia/Taipei`) and an explicit `gmtoffset` (e.g., `28800` for Taiwan).

## 9. Taiwan Symbol Suffix Conventions
- `.TW`: TWSE (Taiwan Stock Exchange) listed equities, ETFs.
- `.TWO`: TPEx (Taipei Exchange) OTC listed equities.
- `^TWII`: Taiwan Capitalization Weighted Stock Index (TAIEX).

## 10. Known Coverage Limitations
- Some futures (e.g., `TX.TW`), funds (e.g., `FUNDA.TW`), and heavily illiquid assets either do not exist or frequently return HTTP 404 errors.
- Symbol suffixing does not cleanly align 1:1 with domestic API definitions.

## 11. Known Failure Modes
- **HTTP 404 (Not Found):** Common for unsupported placeholders or delisted assets.
- **Empty Result Array (`chart.result = []`):** Occurs during bizarre source indexing errors or out-of-range queries.
- **chart.error Provided:** Explicit rejection message from Yahoo.
- **Missing Quote Arrays:** Missing `indicators.quote` payloads can occur if volume is completely zero for the duration.
- **Rate Limiting:** HTTP 429 Too Many Requests if querying too aggressively.
- **Stale Data:** Caching layer can delay `regularMarketTime` beyond actual market ticks.
