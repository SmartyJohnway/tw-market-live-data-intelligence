# TWSE MIS Rich Field Forensics and Validation Plan

## 1. Purpose

M7A starts a richer, evidence-backed `TWSE_MIS` observation contract without changing runtime behavior. The purpose of this first forensic commit is to make every known, documented, observed, or suspected TWSE MIS raw field explicit; classify each field conservatively; preserve unknown fields as raw-only candidates; and define validation work before any broad parser, schema, FastAPI, MCP, frontend, or conversation-context exposure change.

This document is a planning and inventory artifact only. It does not claim a realtime service-level agreement, does not add a data source, and does not authorize runtime probes.

## 2. M7A boundaries

- Source family in scope: `TWSE_MIS` only.
- No `TAIFEX_MIS`, `TAIFEX_OpenAPI`, `TWSE_OpenAPI`, `TPEx_OpenAPI`, Yahoo Finance, FinMind, Fugle, or Fubon reinterpretation.
- No full-market scan, polling loop, scheduler, startup network call, automatic probe, CI network dependency, or production refresh.
- No trading recommendation, buy/sell/hold framing, target price, support/resistance framing, main-force/dealer/institutional prediction language, order book truth claim, true liquidity claim, or realtime guarantee.
- No change to current `z`/`y` fallback behavior, `reference_only` semantics, bounded watchlist behavior, or explicit confirmation requirements.

## 3. Existing TWSE_MIS runtime behavior summary

Current M5K/M5N runtime behavior is intentionally thin:

1. `plan_live_observation` maps bounded watchlist entries to TWSE MIS `ex_ch` routes without network calls.
2. `execute_live_observation` performs explicit bounded requests only after validation and operator execution.
3. The M5K TWSE MIS parser selects a price-like value by preferring numeric `z` and falling back to numeric `y` only as a reference value.
4. If `z` is used, the normalized row remains non-reference under existing logic.
5. If `y` is used because `z` is missing or invalid, the row status becomes `reference_value_only`, `reference_only` is `true`, and caveats/flags indicate that current `z` was unavailable.
6. Timestamp normalization consumes `tlong` first, then `d` + `t` as Taipei-local source time, and keeps freshness caveats rather than claiming realtime status.
7. Current product surfaces expose normalized observation rows, not raw MIS payloads.

## 4. Current parser/consumer path map

| Path | Current role | M7A-00 change |
| --- | --- | --- |
| `config/m5k_default_watchlist.json` | Bounded default watchlist that references `TWSE_MIS`. | None. |
| `config/m5l_live_source_adapter_matrix.json` | Documents bounded TWSE MIS adapters and no startup network behavior. | None. |
| `scripts/m5k_common.py` | Plans bounded routes, executes explicit observations, selects `z`/`y`, maps response rows by `key`/`ch`, and writes latest local M5K artifacts only when explicitly run. | None. |
| `scripts/observation_contract.py` | Normalizes current thin observation contract and preserves `z`/`y` fallback semantics. | None. |
| `scripts/probe_twse_mis.py` | Existing manual probe/normalization helper outside current M5K product surfaces; it already parses many rich fields for probe evidence. | None. |
| `server/main.py` | Readonly FastAPI surface plus explicit M5K endpoints; no startup probe. | None. |
| `server/mcp_server.py` | Readonly MCP plus explicit M5K tools. | None. |
| `frontend/readonly-preview/` | Displays current normalized M5K/M5N fields; no raw endpoint payload. | None. |
| `tests/unit/` | Validates current parser, safety, source registry, frontend, server, and contract behavior. | Adds inventory-boundary tests only. |

## 5. Complete raw field inventory table

The machine-readable companion inventory is `docs/data_capabilities/twse_mis_rich_field_inventory.json`. It contains the complete field-level classification for M7A-00. The table below summarizes every required raw field plus repo-observed fields.

| Raw field | Current parser status | Candidate semantic | Candidate normalized fact | Validation status | AI exposure status |
| --- | --- | --- | --- | --- | --- |
| `z` | existing_runtime_parsed | last price or current price-like value | `price_facts.last_price` | partially validated from existing code | safe after existing semantics |
| `y` | existing_runtime_parsed | previous close candidate and reference fallback | `price_facts.previous_close_candidate` | partially validated from existing code | safe after existing semantics |
| `o` | known raw field not parsed by current M5K contract | open price candidate | `price_facts.open` | requires probe validation | safe after validation |
| `h` | known raw field not parsed by current M5K contract | high price candidate | `price_facts.high` | requires probe validation | safe after validation |
| `l` | known raw field not parsed by current M5K contract | low price candidate | `price_facts.low` | requires probe validation | safe after validation |
| `v` | known raw field not parsed by current M5K contract | volume candidate | `volume_facts.v_candidate` | requires probe validation | not safe yet |
| `tv` | known raw field not parsed by current M5K contract | current/transaction volume candidate | `volume_facts.tv_candidate` | requires probe validation | not safe yet |
| `b` | known raw field not parsed by current M5K contract | displayed bid price ladder candidate | `displayed_depth_facts.bid_prices` | requires probe validation | safe after validation |
| `g` | known raw field not parsed by current M5K contract | displayed bid quantity ladder candidate | `displayed_depth_facts.bid_quantities` | requires probe validation | not safe yet |
| `a` | known raw field not parsed by current M5K contract | displayed ask price ladder candidate | `displayed_depth_facts.ask_prices` | requires probe validation | safe after validation |
| `f` | known raw field not parsed by current M5K contract | displayed ask quantity ladder candidate | `displayed_depth_facts.ask_quantities` | requires probe validation | not safe yet |
| `u` | known raw field not parsed by current M5K contract | limit-up price candidate | `limit_or_reference_facts.limit_up` | requires probe validation | safe after validation |
| `w` | known raw field not parsed by current M5K contract | limit-down price candidate | `limit_or_reference_facts.limit_down` | requires probe validation | safe after validation |
| `d` | existing runtime consumed | source date candidate | `timestamp_facts.source_date` | partially validated from existing code | safe after existing semantics |
| `t` | existing runtime consumed | source time candidate | `timestamp_facts.source_time` | partially validated from existing code | safe after existing semantics |
| `tlong` | existing runtime consumed | source epoch milliseconds candidate | `timestamp_facts.source_timestamp` | partially validated from existing code | safe after existing semantics |
| `c` | existing runtime parsed | symbol code | `identity_facts.symbol` | partially validated from existing code | safe after existing semantics |
| `ex` | existing runtime consumed | exchange/market code candidate | `identity_facts.exchange` | partially validated from existing code | safe after validation |
| `n` | known raw field not parsed by current M5K contract | display name candidate | `identity_facts.name` | requires probe validation | safe after validation |
| `ch` | existing runtime consumed | channel suffix candidate | `identity_facts.channel_suffix` | partially validated from existing code | not safe yet |
| `key` | existing runtime consumed | row/channel key candidate | `identity_facts.key_candidate` | partially validated from existing code | not safe yet |
| `%` | known raw field not parsed by current M5K contract | snapshot/session time candidate | `timestamp_facts.percent_time_candidate` | requires probe validation | not safe yet |
| `ot` | known raw field not parsed by current M5K contract | alternate session time candidate | `timestamp_facts.alternate_session_time_candidate` | requires probe validation | not safe yet |
| `it` | known raw field not parsed by current M5K contract | instrument type code candidate | `identity_facts.instrument_type_code` | requires probe validation | not safe yet |
| `@`, `ps`, `pid`, `pz`, `bp`, `m%`, `^`, `#`, `mt`, `i`, `ip`, `p`, `s`, `nf`, `ts`, `q`, `r`, `oa`, `ob` | unknown / raw-only candidate | unknown or candidate reference/session/identity field | raw-only or candidate group in JSON inventory | requires probe validation | not safe yet |

## 6. Field lifecycle classification

Lifecycle states used by the JSON inventory include:

- `existing_runtime_parsed`
- `existing_runtime_retained`
- `existing_runtime_consumed_not_retained`
- `known_raw_field_not_parsed`
- `candidate_normalized_fact`
- `candidate_raw_only`
- `candidate_requires_unit_validation`
- `candidate_requires_placeholder_validation`
- `candidate_requires_cross_source_validation`
- `unknown_semantics_preserve_raw`
- `not_safe_for_ai_exposure`
- `deprecated_or_not_observed`

Unknown fields are preserved as raw-only inventory rows. Unknown does not mean delete, normalize, expose, or infer.

## 7. Candidate normalized fact groups

Future M7A commits may add nested rich fact groups only after evidence review:

- `price_facts`: `z`, `y`, `o`, `h`, `l`.
- `volume_facts`: `v`, `tv` with units unverified.
- `displayed_depth_facts`: `b`, `g`, `a`, `f`, best bid/ask candidates, displayed-depth only.
- `limit_or_reference_facts`: `u`, `w`, `pz`, `bp`, `ps` after validation.
- `identity_facts`: `c`, `ch`, `ex`, `n`, `nf`, `it`, `key` candidates.
- `timestamp_facts`: `d`, `t`, `tlong`, `%`, `ot`.
- `quality_facts`: missing, malformed, placeholder, ladder length mismatch, non-numeric candidate, stale/reference-only flags.
- `unknown_or_raw_only`: all fields whose semantics remain unvalidated.

## 8. Fields safe for immediate future normalization

Near-safe fields are still future work, not M7A-00 runtime output:

- `z` as `price_facts.last_price`, preserving existing `z` selection behavior.
- `y` as `price_facts.previous_close_candidate`, preserving reference-only fallback behavior.
- `d`, `t`, `tlong` as timestamp inputs, preserving existing freshness behavior.

`o`, `h`, `l`, `u`, `w`, `b`, and `a` are plausible candidates but should wait for bounded evidence review and placeholder validation.

## 9. Fields requiring unit validation

- `v` and `tv` are volume candidates with unit semantics unverified.
- `g` and `f` are displayed bid/ask quantity candidates with unit semantics unverified.
- No M7A-00 artifact calls these shares, lots, executed liquidity, or true liquidity.

## 10. Fields requiring placeholder validation

All price, timestamp, volume, quantity, and displayed-depth candidates require placeholder validation. At minimum validate missing and placeholder shapes for `z`, `y`, `o`, `h`, `l`, `u`, `w`, `v`, `tv`, `b`, `g`, `a`, `f`, `d`, `t`, and `tlong`.

## 11. Fields requiring bounded live probe evidence

M7A-01 should run a manual-only, bounded-symbol probe only if authorized. Priority evidence fields: `o`, `h`, `l`, `v`, `tv`, `b`, `g`, `a`, `f`, `u`, `w`, `%`, `ot`, `it`, plus unknown fields `@`, `ps`, `pid`, `pz`, `bp`, `m%`, `^`, `#`, `mt`, `i`, `ip`, `p`, `s`, `nf`, `ts`, `q`, `r`, `oa`, and `ob` if observed.

## 12. Fields requiring cross-source sanity validation

Cross-source sanity checks are descriptive evidence only and must not promote another source family in this PR. Candidate cross-source checks:

- `y` versus official EOD/reference close where dates align.
- `o`, `h`, and `l` versus official EOD OHLC after market close where dates align.
- `u` and `w` versus validated reference/limit semantics if authoritative evidence is found.
- `v` and `tv` versus official volume only after unit semantics are proven.

## 13. Fields not safe for AI exposure yet

Not safe yet: `v`, `tv`, `g`, `f`, `%`, `ot`, `it`, `ch`, `key`, `@`, `ps`, `pid`, `pz`, `bp`, `m%`, `^`, `#`, `mt`, `i`, `ip`, `p`, `s`, `nf`, `ts`, `q`, `r`, `oa`, and `ob`.

These fields may be retained in raw evidence or inventory but must not be exposed as user-facing AI facts until semantics and guardrails are validated.

## 14. z/y fallback preservation rule

- If `z` is numeric and valid, keep using `z` as the price-like value and keep `reference_only = false` unless other existing logic says otherwise.
- If `z` is missing or invalid and `y` is numeric, use `y` only as a fallback reference value, keep `reference_only = true`, and preserve existing caveats/flags.
- If neither `z` nor `y` is numeric, report value unavailable and do not substitute yesterday's close as current market data.

## 15. reference_only preservation rule

Future rich fields must not cause a `y` fallback row to appear current. A row that is reference-only under current M5K behavior remains reference-only even if `y` is also retained later as a previous-close candidate.

## 16. Displayed depth caveats

`b`/`a` are displayed bid/ask ladder price candidates. `g`/`f` are displayed quantity candidates with unverified units. These are displayed-depth snapshots only. They are not support/resistance, order book truth, true liquidity, or trading guidance.

## 17. Volume unit caveats

`v`, `tv`, `g`, and `f` are unit-unverified candidates. Future parser work must use labels such as `volume candidate` or `quantity candidate` until bounded live evidence and documentation prove unit semantics.

## 18. Proposed next commits

- **M7A-01**: Manual bounded probe execution / evidence review. Validate field presence, placeholder patterns, and value shapes.
- **M7A-02**: Observation contract schema extension. Add nested rich fact groups while preserving existing top-level fields.
- **M7A-03**: TWSE MIS parser extension. Parse `y`/`o`/`h`/`l`, `v`/`tv`, `b`/`g`/`a`/`f`, `u`/`w` with candidate semantics and quality flags.
- **M7A-04**: Fixture expansion and normalization tests. Cover normal, reference-only, placeholder, malformed, missing, and ladder mismatch cases.
- **M7A-05**: Compatibility checks. Confirm FastAPI/MCP/frontend/conversation context existing behavior remains backward compatible.
- **M7A-06**: Generated inventory/docs sync and final M7A acceptance report.
