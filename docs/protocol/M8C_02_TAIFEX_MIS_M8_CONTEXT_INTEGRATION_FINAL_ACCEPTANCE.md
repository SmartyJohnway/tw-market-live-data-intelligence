# M8C-02 TAIFEX MIS M8 context integration staged acceptance

Status: `m8c_02_code_staged_pending_remote_validation`.

M8C-00 preflight and M8C-01 bounded runtime are accepted upstream. This staged M8C-02 change integrates their operator-confirmed output into pure M8 context infrastructure, but **does not activate TAIFEX MIS AI value context** until exact remote-code bounded TX, MTX, and monthly TXO validation succeeds and an evidence-only closure commit updates the registry.

## Adapter schema

`scripts/m8c_taifex_mis_context_adapter.py` converts M8C-01 normalized observations into M8 builder observations with `source_id=TAIFEX_MIS`, `authority_level=official_undocumented`, `timing_class=liveish_intraday_snapshot`, exact `runtime_symbol_id` as `symbol`, and futures/options live-ish context types only after strict validation.

Strict validation requires TAIFEX MIS source identity, instrument type `future` or `option`, regular session, monthly `YYYYMM` contract identity, matching `-F`/`-O` runtime suffix, complete contract identity, `raw_payload_retained=false`, known currentness status, and accepted mode=1 provenance. Unknown values fail closed into metadata-only contexts.

Safe fields are limited to contract identity, source time, source status code, currentness, normalized price/activity, canonical top of book, and non-numeric field provenance. Raw payloads, numeric QID maps, raw mode=1 dictionaries, REST records, trueValues, full option chains, cookies, session IDs, and competing top-of-book family dictionaries are omitted. Invalid observations retain only metadata safe fields.

## Currentness precedence

`scripts/m8_taifex_mis_currentness_bridge.py` is the source-specific dispatch for TAIFEX MIS. Its precedence is TAIFEX MIS source-specific currentness, then session/phase/timestamp evidence, then no generic retrieved-at upgrade. Recent `retrieved_at_utc` cannot upgrade closed sessions, unresolved market phase, unresolved session alignment, missing source timestamp, invalid adapter observations, or invalid snapshots.

`active_session_fresh_liveish` is primary only when source timestamp exists, `source_timestamp_state=resolved`, `session_alignment=aligned`, `market_phase=active_regular_trading`, `quote_age_state=fresh`, `session=regular`, and accepted mode=1 provenance is present. Inconsistent status/axes become metadata-only with values withheld.

Mappings:

- `active_session_fresh_liveish` with valid axes -> primary `fresh_intraday_snapshot` with not-realtime caveat.
- `active_session_aging_liveish` -> supporting `caveated_intraday_snapshot`, role detail `active_aging`.
- `active_session_stale_liveish` -> supporting `caveated_intraday_snapshot`, role detail `active_stale`.
- preopen/indicative/halted/noncontinuous phase -> supporting phase-caveated context only.
- `closed_session_latest_completed` -> supporting `closed_session_reference`, not EOD endpoint data.
- `special_closure_latest_completed` -> closed reference only with TAIFEX-specific official closure evidence; otherwise unresolved metadata-only.
- `closed_session_historical` -> supporting historical context only.
- `market_phase_unresolved` / `session_alignment_unresolved` -> not primary; supporting caveated only when a source timestamp and mode=1 provenance exist.
- `source_timestamp_unresolved` -> metadata only; market values withheld from conversation projection.
- no accepted mode=1 / invalid snapshot -> metadata-only or blocked.

## Controlled conversation projection

`scripts/m8_controlled_conversation_context.py` trusts TAIFEX MIS only through controlled safe fields and formats compact factual futures/options lines. Known TAIFEX metadata contexts retain contract identity, source time, source status, currentness, and caveats while withholding price, volume, book, and value provenance. A registry with `ai_context_allowed=false` never projects TAIFEX market values.

## Failed/missing selector metadata

The adapter consumes `selector_results`, `transport_summary.missing_symbols`, and overall execution status to generate metadata-only failure contexts for missing or failed symbols. These contexts expose no market values.

## TAIFEX MIS + OpenAPI coexistence

TAIFEX MIS remains bounded live-ish contract context. TAIFEX OpenAPI remains official EOD/statistical/reference context. The multi-source builder groups them distinctly as `derivatives_liveish` and official EOD/statistical groups; neither overwrites the other and each keeps its source, timing, and trade-date/source-time provenance.

## Remaining caveats

Regular session only; monthly YYYYMM contracts only; weekly options deferred; after-hours disabled; cross-midnight semantics unresolved; mode=1 initial state only; no delta merge; no reconnect; no unsubscribe invention; raw numeric status semantics unresolved; TXO may lack CTime; retrieved_at never upgrades source currentness; no raw payload; no full option chain; no raw QID map; no trueValues; no recommendation, signal, ranking, or directional interpretation.

## Validation status

Focused M8C-02 unit coverage verifies currentness precedence, projection allowlisting, raw-field withholding, TAIFEX MIS/OpenAPI coexistence, missing selector metadata, policy gating, and pure imports. Final registry activation remains pending exact remote-code bounded live validation and evidence-only closure.
