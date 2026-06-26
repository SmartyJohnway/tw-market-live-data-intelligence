# TWSE MIS Field Dictionary

This dictionary documents fields observed in repository fixtures and probe code for TWSE MIS `msgArray` rows. It is an observed contract only. TWSE MIS is unofficial / fragile, has no official realtime guarantee, is not production current market state by itself, and must not be used as a trading signal.

## Raw field to normalized mapping

| Raw field | Normalized field | Observed semantics | Caveats |
| --- | --- | --- | --- |
| `c` | `symbol` | Symbol code, e.g. `2330`, `0050`, `t00`. | Critical identity. |
| `ex` | `exchange` | Observed exchange key such as `tse` or `otc`. | Critical identity; exact authority is frontend-specific. |
| `n` | `name` | Display name. | Optional in partial rows. |
| `ch` | `channel_suffix` / `channel` | Channel suffix such as `2330.tw`. | Request channel construction is frontend-specific. |
| `z` | `price` / `last_price` | Observed price-like last/current quote field. | May be `-`; price semantics are not official realtime. |
| `y` | `previous_close` | Previous close-like field. | Semantics observed, not official. |
| `o` | `open` | Open price-like field. | May be placeholder before/without trades. |
| `h` | `high` | High price-like field. | May be placeholder. |
| `l` | `low` | Low price-like field. | May be placeholder. |
| `v` | `volume` / `cumulative_volume` | Observed cumulative volume-like field. | Unit semantics are `unknown_or_unverified_semantics`. |
| `tv` | `current_volume` | Observed current/last trade volume-like field. | May be placeholder. |
| `b` | `bid_ladder[].price` | Underscore-delimited bid prices. | Missing/`-` for index rows; zero placeholders are invalid levels. |
| `g` | `bid_ladder[].volume` | Underscore-delimited bid volumes. | Paired by level with `b`. |
| `a` | `ask_ladder[].price` | Underscore-delimited ask prices. | Missing/`-` for index rows; zero placeholders are invalid levels. |
| `f` | `ask_ladder[].volume` | Underscore-delimited ask volumes. | Paired by level with `a`. |
| `u` | `limit_up` | Limit-up-like field. | Missing for some rows; index semantics not applied. |
| `w` | `limit_down` | Limit-down-like field. | Missing for some rows; index semantics not applied. |
| `d` | `source_date` | Source/trading date string, observed as `YYYYMMDD`. | Combine cautiously with `t`. |
| `t` | `source_time` | Source row time string, observed as `HH:MM:SS`. | Can be unavailable; not retrieval time. |
| `tlong` | `source_timestamp` | Epoch milliseconds-like source timestamp. | Preferred for staleness when valid. |
| `%`, `ot` | `snapshot_time`, `alternate_session_time` | Additional timing/session fields. | `unknown_or_unverified_semantics`. |
| `queryTime` | telemetry only | Top-level server query telemetry. | Not exchange/source row time. |
| `userDelay` | telemetry only | Top-level delay-like value. | `unknown_or_unverified_semantics`. |
| `cachedAlive` | telemetry only | Top-level cache telemetry. | `unknown_or_unverified_semantics`. |

## Price and volume handling

Numeric fields parse commas, integer-like strings, and float-like strings. Missing placeholders (`null`, empty string, `-`, `--`, `N/A`) normalize to `null`. Malformed numeric values normalize to `null` and add `malformed_<field>` to `data_quality_flags`. Do not substitute yesterday's close or any fallback as current price.

## Bid/ask ladder handling

Bid ladder uses `b` prices with `g` volumes. Ask ladder uses `a` prices with `f` volumes. Values are underscore-delimited, often with a trailing underscore. Mismatched lengths add `mismatched_<side>_ladder_length`; malformed tokens add level flags; missing stock-like ladders add `missing_bid_ask`. Index rows may legitimately lack bid/ask fields.

## Timestamp, delay, freshness, and staleness

`source_date`, `source_time`, and `source_timestamp` describe source-row time. `retrieved_at` is normalization/probe telemetry supplied by the caller. `staleness_seconds` is derived from source timestamp versus retrieved time. Freshness labels (`live_candidate`, `delayed`, `stale`, `unknown`) are evidence classifications only; `live_candidate` is not an official realtime claim.

## Flags and risk

`data_quality_flags` record missing price, malformed numbers, malformed ladders, unavailable source time, delayed timestamps, stale timestamps, and partial/invalid rows. `source_risk_flags` must include `unofficial_source_risk`, `fragile_frontend_contract`, and `not_official_realtime_api`.

## Caveats

TWSE MIS remains an unofficial / fragile frontend source. It is suitable only as low-frequency bounded evidence candidate under governance. It is not official realtime, not production current market state by itself, and not a source for trading signals.
