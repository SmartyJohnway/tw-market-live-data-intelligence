# M3H-01 TWSE MIS Field Dictionary and Normalization V2 Review

## Final status

Completed. TWSE MIS field documentation, protocol caveats, normalization v2 draft contract, fail-soft normalization helpers, static unit coverage, and governance review notes were updated.

## Scope

This milestone strengthens TWSE MIS as an unofficial low-frequency live-candidate evidence source only. It does not refresh artifacts or run probes.

## Upstream context

This work follows controlled live-probe governance, MCP readback tooling, and validation-report milestones. The MCP live-probe misuse risk is treated as handled outside this change; this milestone returns to data-quality hardening.

## Files changed

- `docs/protocol/TWSE_MIS_FIELD_DICTIONARY.md`
- `docs/protocol/TWSE_MIS_PROTOCOL.md`
- `docs/contracts/twse_mis_normalized_snapshot_v2_draft.md`
- `scripts/probe_twse_mis.py`
- `tests/unit/test_twse_mis_normalization_v2.py`
- `tests/unit/test_twse_mis_docs.py`
- `docs/reviews/M3H_01_TWSE_MIS_FIELD_DICTIONARY_AND_NORMALIZATION_V2.md`

## Normalization v2 behavior

Normalization now emits v2 contract keys including `source_id`, `source_authority`, `source_risk_flags`, `instrument_type`, `price`, `volume`, `bid_ladder`, `ask_ladder`, `source_timestamp`, `retrieved_at`, `staleness_seconds`, `delay_status`, `freshness_status`, `price_semantics`, `raw_fields_present`, `data_quality_flags`, `normalization_version`, `normalization_status`, and `errors`.

The row normalizer fails soft: malformed rows, missing critical identity, malformed numeric values, malformed ladders, missing source time, delayed timestamps, and stale timestamps return structured nulls/flags/errors instead of uncaught exceptions. Backward-compatible v1 aliases remain for existing reports/tests.

## Field dictionary summary

The field dictionary maps observed raw fields to normalized fields and documents price fields, volume fields, bid ladder fields, ask ladder fields, source time, retrieval telemetry, malformed placeholders, `data_quality_flags`, `source_risk_flags`, and `unofficial_source_risk` caveats. Unknown or unverified semantics are labeled as such.

## Protocol summary

The protocol document states frontend/session fragility, low-frequency bounded use, no official realtime claim, no full-market scan, conservative timeout/retry/rate-limit expectations, timestamp semantics, source time versus retrieval time, stale/delayed/live-candidate classification, identity validation, malformed payload handling, and no production refresh by this milestone.

## Tests added / updated

Unit tests cover normal stock rows, TPEx rows, index rows, missing price, malformed bid/ask, stale timestamps, delayed timestamps, zero/dash/empty values, unavailable source time, unofficial source risk flags, no official realtime claim, bid/ask ladder parsing, safe numeric parsing, malformed rows, partial payload behavior, required docs phrases, and required v2 fields.

## Validation commands

- `python -m compileall scripts tests`
- `pytest -m "not network" tests/unit/test_twse_mis_normalization_v2.py tests/unit/test_twse_mis_docs.py`
- `pytest -m "not network"`

## Governance boundaries

- no live probes
- no network calls
- no full-market scan
- no production refresh
- no staging write
- no generated artifact writes
- no frontend artifact writes
- no trading signal
- no `scripts/run_all_probes.py`
- no MCP live-probe behavior changes

## Non-goals

This milestone does not prove TWSE MIS is realtime, does not make TWSE MIS official, does not establish a production current-market-state feed, does not enable full-market collection, and does not produce buy/sell/hold recommendations.

## Caveats

TWSE MIS remains unofficial, fragile, frontend-derived, and not realtime-guaranteed. Normalized `live_candidate` is only a timestamp-derived evidence label, not an official realtime assertion.

## Next recommended step

Add an offline fixture-driven comparison between TWSE MIS v2 rows and at least one official delayed/reference source to further document semantic differences without running live probes.
