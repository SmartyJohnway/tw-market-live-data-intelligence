# M3I-01 Frontend Readonly Caveat and Staleness Display Design

## Result

Added a design-only frontend readonly caveat and staleness display contract.

## Files

- `docs/contracts/frontend_readonly_caveat_staleness_display_contract.md`
- `docs/reviews/M3I_01_FRONTEND_READONLY_CAVEAT_AND_STALENESS_DISPLAY_DESIGN.md`

## Requirements Covered

- source authority
- source id
- freshness status
- delay status
- staleness seconds
- `retrieved_at`
- `source_timestamp`
- data quality flags
- source risk flags
- normalization status
- not realtime-guaranteed caveat
- not trading signal caveat
- not production current state unless explicitly refreshed
- UI wording examples
- warning/caveat display logic
- non-goals

## Explicit Boundaries

- No frontend/public writes.
- No frontend artifact refresh.
- No production refresh.
- No trading signals.
- No realtime claim.
- No live probes.
- No MCP live-probe behavior changes.

## Validation

- `python -m compileall scripts tests`
- `pytest -m "not network" tests/unit/test_twse_mis_normalization_v2.py`
- `pytest -m "not network"`
