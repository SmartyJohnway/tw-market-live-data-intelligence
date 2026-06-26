# TWSE MIS Normalized Snapshot v2 Contract (Draft)

TWSE MIS normalization v2 is an observed, fail-soft contract for a fragile frontend source. TWSE MIS remains unofficial, has no official realtime guarantee, is not production current market state by itself, and must not be used as a trading signal.

## Normalized object fields

Required keys for every normalized row:

| Field | Type | Semantics |
| --- | --- | --- |
| `source_id` | string | Always `twse_mis`. |
| `source_authority` | string | `unofficial_frontend_source`. |
| `source_risk_flags` | list[string] | Includes `unofficial_source_risk`, `fragile_frontend_contract`, `not_official_realtime_api`. |
| `symbol` | string/null | Raw `c`. Critical identity field. |
| `exchange` | string/null | Raw `ex`, observed values include `tse` and `otc`. |
| `instrument_type` | string | Candidate classification: `stock_like`, `index`, `etf`, `tdr`, or `unknown`; semantics are observed/heuristic. |
| `name` | string/null | Raw `n`. |
| `price` | number/null | Raw `z`, interpreted only as observed last trade/current quote field when available. |
| `open`, `high`, `low`, `previous_close` | number/null | Raw `o`, `h`, `l`, `y`. |
| `volume` | integer/null | Raw `v`, observed cumulative volume-like field. Unit semantics remain `unknown_or_unverified_semantics`. |
| `bid_ladder` | list[object] | Parsed from raw `b` prices and `g` volumes. |
| `ask_ladder` | list[object] | Parsed from raw `a` prices and `f` volumes. |
| `source_date` | string/null | Raw `d` in `YYYYMMDD` when present. |
| `source_time` | string/null | Raw `t` in `HH:MM:SS` when present. |
| `source_timestamp` | string/null | UTC ISO timestamp derived from `tlong` first, else `d` + `t` as Taipei time. |
| `retrieved_at` | string | Probe retrieval UTC ISO timestamp supplied by caller. |
| `staleness_seconds` | integer/null | `retrieved_at - source_timestamp`, floored at zero. |
| `delay_status` | string | `not_delayed_candidate`, `delayed_candidate`, `stale`, or `unknown`. |
| `freshness_status` | string | `live_candidate`, `delayed`, `stale`, or `unknown`. |
| `price_semantics` | string | Backward-compatible quote classification such as `live_candidate`, `delayed_quote`, `stale_quote`, or `unknown`; never an official realtime claim. |
| `price_semantics_detail` | string | Caveated interpretation of raw `z` as an observed last-trade/current-quote-like frontend field. |
| `raw_fields_present` | list[string] | Raw keys present in the row. |
| `data_quality_flags` | list[string] | Missing, malformed, delayed, stale, or partial-row flags. |
| `normalization_version` | string | `twse_mis_snapshot_v2_draft`. |
| `normalization_status` | string | `ok`, `partial`, or `invalid`. |
| `errors` | list[string] | Critical invalid-row reasons. |

## Parsing rules

- Numeric parsing removes commas, accepts integer-like and float-like strings, and returns `null` for `null`, empty strings, `-`, `--`, `N/A`, `null`, and `None` placeholders.
- Malformed numeric values return `null` and add `malformed_<field>` to `data_quality_flags`.
- Bid/ask ladder parsing splits underscore-delimited raw fields, drops trailing empty tokens, pairs price and volume by level, and emits objects shaped as `{level, price, volume}`.
- Ladder price placeholders (`-`, empty, `0`, `0.0000`) become `null` and add `invalid_<side>_price_level`; malformed tokens add `malformed_<side>_price_level` or `malformed_<side>_volume_level`.
- Missing optional fields do not raise exceptions.
- Missing critical identity (`symbol`, `exchange`) returns `normalization_status = invalid` with structured `errors`.
- Non-critical anomalies return `normalization_status = partial` and flags, not uncaught exceptions.

## Timestamp and freshness policy

- Prefer raw `tlong` as epoch milliseconds when present.
- If `tlong` is unavailable, parse raw `d` + `t` as Asia/Taipei local time and convert to UTC.
- If source time is unavailable or malformed, set `source_timestamp` and `staleness_seconds` to `null` and flag the row.
- Stale threshold policy: `<= 300s` is `live_candidate` / `not_delayed_candidate`; `301-1200s` is `delayed` / `delayed_candidate`; `> 1200s` is `stale` / `stale`.
- `live_candidate` is only a bounded evidence classification. It is not realtime-guaranteed and not production current market state by itself.

## Source caveats and non-goals

TWSE MIS is an unofficial / fragile frontend source. This contract does not authorize live probes, full-market scans, production refreshes, staging writes, generated artifact writes, frontend artifact writes, or trading signals.
