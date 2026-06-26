# TWSE MIS Protocol

## Source classification

TWSE MIS is classified in this project as an `unofficial_frontend_source`: a fragile browser-facing market information system endpoint, not an officially documented public realtime API. It has no official realtime guarantee, is not production current market state by itself, and must not be used as a trading signal.

## Frontend/session fragility

Observed browser flow uses a frontend page/session before data requests. Cookies, headers, session state, cache behavior, bot controls, and response shape are undocumented and can change without notice. Any session / cookie requirement is part of frontend fragility, not a stable API contract.

## Bounded-use protocol

- Use only for low-frequency, bounded evidence checks when governance explicitly permits live probing.
- Do not perform full-market scans.
- Do not use high-frequency polling.
- Apply conservative timeout, retry, and rate-limit behavior; retries must be bounded and should not amplify load.
- Do not bypass authentication, cookies, bot controls, blocks, or access restrictions.
- This milestone performs no live probe, no production refresh, and no staging write.

## Request/response shape

The observed frontend JSON payload contains `msgArray` rows with abbreviated raw fields such as `c`, `ex`, `n`, `z`, `a`, `b`, `f`, `g`, `d`, `t`, and `tlong`. Top-level telemetry may include `queryTime`, `userDelay`, `cachedAlive`, `rtcode`, and `rtmessage`. These fields are observed evidence, not an official specification.

## Timestamp semantics

- `source_time` comes from raw row `t` when present.
- `source_date` comes from raw row `d` when present.
- `source_timestamp` should prefer raw `tlong` epoch milliseconds; if unavailable, derive from `d` + `t` as Taipei time.
- `retrieved_at` is caller telemetry recording when the row was normalized/retrieved.
- `staleness_seconds` compares source time to retrieval time.
- Top-level `queryTime.sysTime` is server telemetry and must not be collapsed into exchange/source time.

## Freshness classification

Rows may be classified as `live_candidate`, `delayed`, `stale`, or `unknown` based on derived staleness. `live_candidate` means only that the observed timestamp is close to retrieval time under this project's threshold. It does not mean official realtime, official source authority, or production-grade current market state.

## Identity validation

Normalizers must validate at least `symbol` (`c`) and `exchange` (`ex`). Missing identity should fail soft with `normalization_status = invalid`, explicit `errors`, and data-quality flags. Asset type is only an observed/heuristic classification and unknown semantics must remain marked as `unknown_or_unverified_semantics`.

## Malformed payload handling

Malformed rows, missing optional fields, placeholder values (`-`, empty strings, zero ladder placeholders), and mismatched bid/ask ladder lengths must return structured nulls, flags, and errors where appropriate. Parsers must not silently misclassify or throw uncaught exceptions for row-level quality issues.

## Prohibited uses

No full-market scan, no production refresh, no staging write, no generated artifact write, no frontend artifact write, no automated trading, no buy/sell/hold output, and no claim that TWSE MIS is official or realtime-guaranteed.
