# M8A official EOD context final acceptance

## 1. Purpose
Complete M8A official TWSE/TPEx latest EOD adapters, normalized observations, controlled execution, currentness resolution, M8 context integration, conversation projection, and closure evidence support.

## 2. Accepted upstream
M7G controlled refresh, M8-00 governance/context/conversation foundations, and M8A-00 contracts are accepted upstream.

## 3. Implemented modules
- `scripts/m8a_official_eod_observation.py`
- `scripts/m8a_twse_official_eod_adapter.py`
- `scripts/m8a_tpex_official_eod_adapter.py`
- `scripts/m8a_official_eod_execution.py`
- `scripts/m8a_ncdr_dgpa_closure_cap.py`
- `scripts/m8a_market_day_currentness_resolver.py`
- `scripts/validate_m8a_official_eod_live.py`

## 4. TWSE adapter behavior
Fetches `STOCK_DAY_ALL` explicitly, validates status/content/JSON array shape, parses ROC dates, maps required fields, derives `previous_close`, detects duplicate identity and mixed dates, and retains only requested symbols.

## 5. TPEx adapter behavior
Fetches mainboard daily close quotes explicitly, maps core OHLC/activity fields, omits source-specific fields from core context, and fail-closes unclassified instruments from AI context by default.

## 6. Shared normalized observation
`m8a_official_eod_observation.v1` preserves source, endpoint contract, authority, timing, market/symbol identity, trade date, field validation, derived fields, caveats, and compact provenance without raw payload retention.

## 7. Instrument classification
TPEx classification uses security-master style exact `(market, symbol)` lookup. Unknown rows are partial evidence only and excluded from deterministic metrics and AI context by default.

## 8. Failure handling
Deterministic statuses cover empty arrays, unavailable/error sources, schema drift, mixed dates, partial success, and currentness mismatch classes.

## 9. Controlled runtime execution
Execution requires explicit operator confirmation, allowed sources, bounded non-empty symbols, and one whole-market request per source with immediate bounded retention.

## 10. Whole-market fetch vs bounded retention
Official endpoints are whole-market network fetches; adapter results retain only requested symbols and compact rejection metadata.

## 11. Market-day currentness resolution
The resolver combines scheduled calendar status, emergency closure events, exchange special status, and reported trade date to compute expected latest completed trade date.

## 12. NCDR/DGPA exception source
`NCDR_DGPA_CLOSURE_CAP` is currentness evidence only. It is not price data and is queried only during explicit controlled execution when mismatch resolution requires it.

## 13. M8 multi-source context integration
Normalized observations project into `official_equity_eod_reference`, `official_etf_eod_reference`, or `official_market_eod_reference` without overwriting TWSE_MIS live-ish context.

## 14. Conversation projection
The controlled conversation projector labels official EOD references, preserves source/date/currentness/caveats, and continues to block raw payload exposure.

## 15. README update
README documents source roles, controlled execution, currentness model, commands, and limitations.

## 16. Live validation evidence
Manual live validation is available via `scripts/validate_m8a_official_eod_live.py`; no uncontrolled live output is committed.

## 17. Security and privacy boundaries
No scheduler, polling, startup fetch, DB write, credential provider, raw full-market retention, AI/model call, recommendation engine, TAIFEX, MOPS, TPEX_MIS, or `rotc_` route was added.

## 18. Compatibility
Deterministic M8A tests and related M8 compatibility tests pass under no-network execution.

## 19. Known caveats
- Selected OpenAPI endpoints are latest-only.
- No historical backfill is implemented in M8A.
- Instrument classification depends on the security master.
- NCDR feed retention/history window is not guaranteed.
- Emergency closure parsing is bounded to market-currentness needs.
- No scheduler or polling is added.
- Official EOD is not realtime.

## 20. Final result
`m8a_official_eod_context_final_acceptance_pass_with_caveats`

## 21. Recommended next track
Proceed to the next official reference/EOD context item in the repository roadmap: corporate action, attention/disposition, or additional official reference context after separate source-contract review.

## Review correction note
PR review blocker fixes preserve the squashed GitHub PR shape. The original implementation had been squashed into one GitHub commit before review even though the earlier report described a four-commit local execution structure. This correction does not claim four reviewable GitHub commits; it documents the implemented boundaries and validation state.

Review corrections include realistic NCDR Atom summary date parsing, entry-updated-based yearless/relative date resolution, session-aware expected EOD logic, exact repository security-master classification for TWSE/TPEx, fail-closed unknown classifications, and distinct emergency-closure unknown versus checked-empty states.
