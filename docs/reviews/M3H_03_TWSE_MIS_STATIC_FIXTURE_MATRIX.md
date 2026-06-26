# M3H-03 TWSE MIS Static Fixture Matrix

## Scope

Added disk-loaded static fixture coverage for TWSE MIS normalization v2. The test matrix uses local JSON fixtures only and never calls the live TWSE MIS endpoint.

## Fixture File

- `tests/fixtures/market_sources/twse_mis/normalization_v2_matrix.json`

## Test File

- `tests/unit/test_twse_mis_normalization_v2.py`

## Cases Covered

The fixture matrix covers:

- normal TWSE stock
- TPEx stock
- index row
- ETF row
- TDR row
- missing price
- malformed bid/ask
- stale timestamp
- delayed timestamp
- source time unavailable
- partial payload
- unknown raw fields

## Assertions

Each fixture case checks:

- `normalization_status`
- `instrument_type`
- `freshness_status`
- `delay_status`
- `data_quality_flags`
- `source_risk_flags`
- `normalization_version`
- additional case-specific fields such as `price`, `source_timestamp`, `staleness_seconds`, `bid_ladder`, `ask_ladder`, and `unmapped_raw_fields`

## Governance Boundaries

- No live probes.
- No network calls in tests.
- No `scripts/run_all_probes.py`.
- No full-market scan.
- No controlled live probe execution.
- No production refresh.
- No staging write.
- No generated artifact writes.
- No frontend artifact writes.
- No broker/auth or commercial API enablement.
- No trading signals.
- No realtime guarantee.

## Validation

- `python -m compileall scripts tests`
- `pytest -m "not network" tests/unit/test_twse_mis_normalization_v2.py`
- `pytest -m "not network"`
