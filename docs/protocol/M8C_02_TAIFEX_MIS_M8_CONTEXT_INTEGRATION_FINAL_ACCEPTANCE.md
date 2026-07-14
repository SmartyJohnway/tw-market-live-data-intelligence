# M8C-02 TAIFEX MIS M8 context integration final acceptance

Status: `m8c_02_taifex_mis_m8_currentness_context_integration_and_final_acceptance_pass_with_caveats`.

## Scope and upstream acceptance

M8C-02 accepts the M8C-00 TAIFEX MIS transport preflight and the M8C-01 bounded regular-session initial-state runtime as upstream inputs. It does not redesign the REST/SockJS runtime and does not add polling, reconnect, delta merge, after-hours execution, weekly-option execution, persistence, public API, frontend, MCP surface, or model call.

The accepted pipeline is:

1. operator-confirmed M8C-01 bounded runtime execution,
2. pure TAIFEX MIS context adapter,
3. TAIFEX-MIS-specific currentness bridge,
4. M8 multi-source context builder,
5. controlled conversation projection.

## Adapter schema and allowlist

The adapter emits builder-compatible TAIFEX MIS observations with `source_id=TAIFEX_MIS`, `source_family=TAIFEX_MIS`, `authority_level=official_undocumented`, `timing_class=liveish_intraday_snapshot`, `market=taifex`, exact runtime symbol identity, source timestamp metadata, session metadata, currentness metadata, safe fields, omitted fields, caveats, and provenance.

Safe fields are limited to normalized contract identity, source time, source status code, source-specific currentness axes, price, activity, canonical top-of-book fields, and field provenance. Raw payloads, numeric QID maps, `trueValues`, raw mode=1 dictionaries, raw REST rows, cookies/session IDs, full option chains, and competing book-family dictionaries remain withheld.

## Currentness precedence and roles

TAIFEX MIS uses source-specific currentness before any generic retrieved-at fallback. `retrieved_at_utc` never upgrades a closed, unresolved, or missing-source-timestamp observation.

Role mapping remains fail-closed:

- `active_session_fresh_liveish` can become primary only with a valid timezone-aware source timestamp, aligned regular session, active regular-trading phase, fresh quote age, valid contract identity, and accepted mode=1 evidence.
- Aging or stale live-ish states are supporting only and are not described as current.
- Preopen, indicative, halted, noncontinuous, closed, historical, unresolved, source-timestamp-unresolved, transport-failure, and missing-initial-state states are supporting or metadata-only according to source evidence.
- `source_timestamp_unresolved` retains identity/currentness metadata while withholding price, volume, book, and value provenance.

## Controlled conversation projection

TAIFEX MIS conversation projection is metadata-first and source-policy gated. With `ai_context_allowed=true`, only controlled safe fields may be projected. Metadata-only contexts retain contract identity, source time/status, currentness, and caveats, while price, volume, book, and value provenance are withheld.

The projection remains factual only. It must not generate recommendations, signals, rankings, directional interpretation, targets, support/resistance language, or automatic market commentary.

## TAIFEX MIS and TAIFEX OpenAPI coexistence

TAIFEX MIS may provide bounded live-ish contract context. TAIFEX OpenAPI remains the official documented EOD/statistical reference. The M8 builder preserves separate source, timing, trade-date, runtime-symbol, and contract provenance; neither source silently overwrites the other.

## Quote-free live integration evidence

Evidence artifact: `research/probe_runs/m8c_02_taifex_mis_context/m8c_02_context_integration_summary.json`.

- Base SHA: `0553e48371d90a7cfceea444ee36c36f7fd44db7`.
- Tested remote code SHA: `b55cf800561f9997991a82b34013ff0564052710`.
- Actual execution head SHA: `b55cf800561f9997991a82b34013ff0564052710`; clean detached checkout: true; execution SHA matched tested remote SHA: true.
- Activation commit SHA: `e488e7e05a19687fb72b2ad032afda600b2aebb6`.
- Runtime status: `successful_liveish_snapshot`.
- Selector count: 3; selector OK count: 3.
- Accepted mode=1 initial-state count: 3.
- Adapter observations: 3 valid, 0 invalid.
- Currentness statuses observed on exact remote validation: `session_alignment_unresolved`, `source_timestamp_unresolved`.
- Context roles observed: `supporting_caveated`, `metadata_only`.
- Primary/supporting/metadata counts: 0 / 2 / 3.
- Monthly TXO with missing `CTime` remained structurally valid and metadata-only under `source_timestamp_unresolved`.
- No adapter-bypass caveat appeared for the valid TXO metadata context.
- Raw payload, numeric QIDs, `trueValues`, and full option chain were absent from the projected context.
- No quote values were committed.
- No recommendation, signal, or ranking was generated.

- Evidence separates `adapter_safe_field_names`, `builder_safe_field_names`, `conversation_projected_safe_field_names`, and `conversation_markdown_display_field_names`; exact remote metadata-only structured conversation safe fields are `contract_identity`, `source_time`, `source_status_code`, and `currentness`, while markdown display fields are limited to selector/currentness/context-role and value-bearing price, activity, top-of-book, and field-provenance fields are recorded as withheld.
- Quote-free per-observation traceability is retained for TX, MTX, and TXO with symbol, instrument type, adapter validity, mode=1 evidence, source timestamp validity, currentness, context role, AI-safety flag, metadata-only flag, adapter-bypass caveat flag, conversation projected fields, and conversation withheld value fields.

## Validation results

Required M8C/M8/default validations passed. Full non-network base/head comparison is recorded in the evidence artifact: base `0553e48371d90a7cfceea444ee36c36f7fd44db7` collected 1284, selected 1283, passed 1275, skipped 1, deselected 1, failed 7; tested `b55cf800561f9997991a82b34013ff0564052710` collected 1330, selected 1329, passed 1321, skipped 1, deselected 1, failed 7. The failure set is identical and consists only of the known unrelated M5D/M5E frontend-publication failures; `new_m8_failures=[]` and `new_m8c_failures=[]`.

## Final registry state

`TAIFEX_MIS` is activated for controlled caveated safe-field AI context with:

- `ai_context_allowed=true`,
- `ai_exposure_level=controlled_caveated_safe_fields`,
- `context_integration_added=true`,
- `conversation_integration_added=true`,
- `runtime_status=bounded_initial_state_snapshot_runtime_with_controlled_m8_context`,
- `currentness_integration=taifex_mis_source_specific_fail_closed`,
- `raw_payload_exposure_allowed=false`,
- `trading_signal_allowed=false`,
- `recommendation_allowed=false`.

## Remaining caveats

Regular session only; monthly `YYYYMM` contracts only; weekly options deferred; after-hours disabled; cross-midnight semantics unresolved; mode=1 initial state only; no delta merge; no reconnect; no unsubscribe invention; raw numeric `Status` semantics unresolved; TXO may lack `CTime`; retrieved-at never upgrades source currentness; no raw payload; no full option chain; no raw QID map; no `trueValues`; no recommendation, signal, ranking, or directional interpretation.
