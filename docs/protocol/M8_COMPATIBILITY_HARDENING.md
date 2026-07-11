# M8 Compatibility Hardening

Status: `m8_00_07_compatibility_hardening_defined`

## 1. Purpose

Document and test compatibility hardening for M8 controlled conversation context so downstream AI tools cannot misread source timing, authority, freshness, or safety policies.

## 2. Hardening matrix

| Case | Required behavior |
| --- | --- |
| EOD/reference | Visible only as EOD/reference, not realtime/current price |
| retrieved_at_utc | Retrieval time only, not exchange timestamp |
| stale | Caveated stale context, not current market |
| manual evidence | Manual context, not official and cannot override official |
| validation-only | Supporting context only, never primary |
| credential-gated | Metadata only, no runtime dependency, no secrets |
| unknown source | Safe fields withheld |
| forbidden raw fields | Absent from markdown and projected safe fields |
| trading interpretation | No advice, recommendation, signal, targets, levels, ranking, or directional labels |

## 3. Assertions

- EOD not realtime.
- `retrieved_at_utc` not exchange timestamp.
- stale not current.
- manual not official.
- validation-only not primary.
- credential-gated not runtime dependency.
- unknown source safe fields withheld.
- forbidden raw fields absent.
- no trading advice / no recommendation / no trading signal.
- no target price / support-resistance / ranking / top movers / bullish-bearish.

## 4. Compatibility with M8-00-05 builder

The builder remains the source of `m8_00_multi_source_market_context.v1`. This hardening adds a live-ish source-family observation flag, parsed UTC most-recent retrieved-at comparison, and downstream withholding of unknown-source safe fields.

## 5. Compatibility with M8-00-04 evaluator

The projection consumes freshness assessments produced through the builder and does not alter M8-00-04 evaluator semantics.

## 6. Non-goals

- no live smoke
- no network
- no adapter

## 7. Next task

`M8-00-08-FINAL-ACCEPTANCE-AND-CLOSURE`
