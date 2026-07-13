# M8C-02 TAIFEX MIS M8 context integration final acceptance

Status: `m8c_02_taifex_mis_m8_currentness_context_integration_and_final_acceptance_pass_with_caveats`.

M8C-00 preflight and M8C-01 bounded runtime are accepted upstream. M8C-02 integrates only their operator-confirmed output into pure M8 context infrastructure. It performs no runtime redesign, background fetch, persistence, scheduler, public API, model call, recommendation, signal, ranking, or automatic market commentary.

## Adapter schema

`scripts/m8c_taifex_mis_context_adapter.py` converts M8C-01 normalized observations into M8 builder observations with `source_id=TAIFEX_MIS`, `authority_level=official_undocumented`, `timing_class=liveish_intraday_snapshot`, exact `runtime_symbol_id` as `symbol`, and futures/options live-ish context types.

Safe fields are limited to contract identity, source time, source status code, currentness, normalized price/activity, canonical top of book, and non-numeric field provenance. Raw payloads, numeric QID maps, raw mode=1 dictionaries, REST records, trueValues, full option chains, cookies, session IDs, and competing top-of-book family dictionaries are omitted.

## Currentness precedence

`scripts/m8_taifex_mis_currentness_bridge.py` is the source-specific dispatch for TAIFEX MIS. Its precedence is TAIFEX MIS source-specific currentness, then session/phase/timestamp evidence, then no generic retrieved-at upgrade. Recent `retrieved_at_utc` cannot upgrade closed sessions, unresolved market phase, unresolved session alignment, missing source timestamp, or invalid snapshots.

Mappings:

- `active_session_fresh_liveish` -> primary `fresh_intraday_snapshot` with not-realtime caveat.
- `active_session_aging_liveish` / `active_session_stale_liveish` -> supporting `caveated_intraday_snapshot`.
- preopen/indicative/halted/noncontinuous phase -> supporting phase-caveated context only.
- `closed_session_latest_completed` / `special_closure_latest_completed` -> supporting `closed_session_reference`, not EOD endpoint data.
- `closed_session_historical` -> supporting historical context only.
- `market_phase_unresolved` / `session_alignment_unresolved` -> not primary; supporting caveated only when a source timestamp exists.
- `source_timestamp_unresolved` -> metadata only; market values withheld from conversation projection.
- no accepted mode=1 / invalid snapshot -> metadata-only or blocked.

## Controlled conversation projection

`scripts/m8_controlled_conversation_context.py` trusts TAIFEX MIS only through controlled safe fields and formats compact factual futures/options lines. It never dumps the TAIFEX MIS `safe_fields` dictionary wholesale. Missing source timestamp or metadata-only states withhold price, volume, and book values.

## TAIFEX MIS + OpenAPI coexistence

TAIFEX MIS remains bounded live-ish contract context. TAIFEX OpenAPI remains official EOD/statistical/reference context. The multi-source builder groups them distinctly as `derivatives_liveish` and official EOD/statistical groups; neither overwrites the other and each keeps its source, timing, and trade-date/source-time provenance.

## Remaining caveats

Regular session only; monthly YYYYMM contracts only; weekly options deferred; after-hours disabled; cross-midnight semantics unresolved; mode=1 initial state only; no delta merge; no reconnect; no unsubscribe invention; raw numeric status semantics unresolved; TXO may lack CTime; retrieved_at never upgrades source currentness; no raw payload; no full option chain; no raw QID map; no trueValues; no recommendation, signal, ranking, or directional interpretation.

## Validation

Focused M8C-02 unit coverage verifies currentness precedence, projection allowlisting, raw-field withholding, TAIFEX MIS/OpenAPI coexistence, partial metadata behavior, and pure imports. Live integration evidence is recorded separately in `research/probe_runs/m8c_02_taifex_mis_context/m8c_02_context_integration_summary.json` without live quote values.
