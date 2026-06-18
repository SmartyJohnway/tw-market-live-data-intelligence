# TWSE MIS Field Dictionary

This dictionary documents the observed response fields from the TWSE MIS endpoint (`getStockInfo.jsp`).
**Important:** This dictionary is an *observed contract* based on sample responses (both intraday and post-market), not an official TWSE API specification.

## Core Asset Identity
| Raw Field | Observed Meaning | Data Type | Example | Normalized Candidate | Confidence | Caveats |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `c` | Symbol Code | String | `"2330"` | `symbol` | confirmed | The core ticker symbol. |
| `n` | Symbol Name (Short) | String | `"台積電"` | `name` | confirmed | Typically the Chinese short name. |
| `ex` | Exchange Identifier | String | `"tse"`, `"otc"` | `exchange` | confirmed | Distinguishes TWSE (`tse`) from TPEx (`otc`). |
| `ch` | Quote Channel Suffix | String | `"2330.tw"` | `channel_suffix` | confirmed | The suffix used for the channel. The request `ex_ch` parameter is constructed as `ex` + "_" + `ch` (e.g., `"tse_2330.tw"`). |

## Price & Trade Data
| Raw Field | Observed Meaning | Data Type | Example | Normalized Candidate | Confidence | Caveats |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `z` | Last Trade Price | String | `"1050.00"`, `"-"` | `last_price` | observed | Intraday, this may be `"-"` if no trade has occurred or during pre-market/matching. Post-market, it is typically populated with the final closing price. |
| `y` | Previous Close Price | String | `"1040.00"` | `previous_close` | observed | Usually populated consistently across sessions. |
| `o` | Open Price | String | `"1045.00"`, `"-"` | `open` | observed | Can be `"-"` before the first trade. |
| `h` | High Price | String | `"1055.00"`, `"-"` | `high` | observed | Can be `"-"` before the first trade. |
| `l` | Low Price | String | `"1040.00"`, `"-"` | `low` | observed | Can be `"-"` before the first trade. |
| `v` | Cumulative Volume | String | `"15000"` | `cumulative_volume` | observed | Total volume traded so far in the session. |
| `tv` | Current/Last Trade Volume | String | `"5"`, `"-"` | `current_volume` | observed | Intraday, this may be `"-"`. Often populated post-market. |

## Bid/Ask Data (Stocks & ETFs primarily)
*Note: Indices like `tse_t00.tw` typically do not include bid/ask fields.*

| Raw Field | Observed Meaning | Data Type | Example | Normalized Candidate | Confidence | Caveats |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `a` | Ask Price List | String | `"1055.00_1056.00_1057.00_1058.00_1059.00_"` | `ask_prices` | observed | Underscore-separated string of the top 5 ask levels. Often ends with a trailing underscore. |
| `f` | Ask Volume List | String | `"100_200_300_400_500_"` | `ask_volumes` | observed | Underscore-separated string of volumes corresponding to the ask prices (`a`). |
| `b` | Bid Price List | String | `"1050.00_1049.00_1048.00_1047.00_1046.00_"` | `bid_prices` | observed | Underscore-separated string of the top 5 bid levels. |
| `g` | Bid Volume List | String | `"150_250_350_450_550_"` | `bid_volumes` | observed | Underscore-separated string of volumes corresponding to the bid prices (`b`). |

## Market Limits
| Raw Field | Observed Meaning | Data Type | Example | Normalized Candidate | Confidence | Caveats |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `u` | Limit Up Price | String | `"1140.00"` | `limit_up` | observed | The maximum allowed price for the session (typically +10%). |
| `w` | Limit Down Price | String | `"936.00"` | `limit_down` | observed | The minimum allowed price for the session (typically -10%). |

## Timestamps & Telemetry
| Raw Field | Observed Meaning | Data Type | Example | Normalized Candidate | Confidence | Caveats |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `d` | Trading Date | String | `"20241025"` | `source_date` | observed | Format is YYYYMMDD. |
| `t` | Source Time | String | `"13:30:00"` | `source_time` | observed | Intraday, this is close to query time. Post-market, it may reflect regular session time. |
| `tlong` | Source Time (MS) | String (Numeric) | `"1729834200000"` | `source_time_ms` | observed | Epoch timestamp in milliseconds. Used to derive staleness. |
| `queryTime` | Server Query Time | JSON Object | `{"sysTime": "13:30:05", ...}` | N/A | candidate | Internal telemetry indicating when the server processed the request. |
| `userDelay` | System User Delay | String/Int | `"0"` | N/A | unknown | Internal telemetry, meaning unclear. |
| `cachedAlive` | Cache Lifetime | String/Int | `"30000"` | N/A | candidate | Internal telemetry, likely related to server-side cache duration. |

## Optional & Internal Fields (Intraday & Post-Market)
| Raw Field | Observed Meaning | Data Type | Example | Normalized Candidate | Confidence | Caveats |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `@` / `key` | Feed/System Routing | String | Varied | N/A | unknown_or_internal | Internal routing or feed keys. |
| `^` | Unknown Metric | String | Varied | N/A | unknown | Usage unclear. |
| `%` | Session/Timing Metric | String | `"13:30:00"`, `"-"` | N/A | candidate | Intraday, aligns closely with `t`. Post-market, may reflect post-market or alternate-session timing. |
| `nf` / `it` / `i` | Company/Listing Info | String | Varied | N/A | candidate | Likely related to listing references or identifiers. |
| `nu` | ETF Reference/NAV URL | String | URL | N/A | observed | ETF-specific reference or NAV-related URL. |
| `s` / `ps` / `pz` | Trading Phase/State | String | `"-"` | N/A | candidate | Intraday, these may be `"-"`. Post-market, they often populate, likely representing matching phases or pricing state. |
| `pid` / `#` | Feed Sequence Info | String | Varied | N/A | unknown_or_internal | May change across market phases. Treat as internal feed/channel/sequence fields, not asset identity. |
| `bp` / `mt` / `m%` / `p` / `ts` | Pricing/Calculated | String | Varied | N/A | candidate | Likely relate to mid-prices, matching calculations, or tick states. |
| `oa` / `ob` / `oz` / `ov` / `ot` / `fv` | Post-market Metrics | String | Varied | N/A | candidate | Populate during post-market responses. Likely relate to odd-lot, after-hours trading, and specific closing times (`ot`). |

---

## Important Session-Dependent Caveats

### Intraday vs. Post-Market Value Behavior
1. **Missing Data (`"-"`)**: During intraday trading, especially before the first match or during specific auction phases, fields like `z`, `tv`, `s`, `ps`, `pz` may be returned as the literal string `"-"`.
2. **Post-Market Population**: After market close, these `"-"` values often become populated with final closing metrics.
3. **Post-Market Additional Fields**: Post-market responses may include new fields such as `oa`, `ob`, `oz`, `ov`, `ot`, and `fv`.
4. **Timestamp Reflection**: Intraday, `t`, `%`, and `tlong` may align closely to the ongoing session time. Post-market, `t` may reflect regular session close time, while `%` or `ot` may reflect post-market or alternate-session timing.
5. **Sequence Fields**: Fields like `pid` and `#` may change across market phases and should be treated as internal feed/channel/sequence fields, not asset identity.

### Asset Class Differences
- **Index Rows**: Rows representing market indices (like `tse_t00.tw` for the TAIEX) have a different structural shape. They generally **do not include bid/ask fields** (`a`, `b`, `f`, `g`) and may omit volume fields that don't apply to a calculated index. Do not assume all rows share identical schemas.
