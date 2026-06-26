# M3G-11 Controlled Refresh Staging Write Design

## Result

Added a design-only controlled refresh staging-write contract.

## Files

- `docs/contracts/controlled_refresh_staging_write_contract.md`
- `docs/reviews/M3G_11_CONTROLLED_REFRESH_STAGING_WRITE_DESIGN.md`

## Coverage

The contract defines purpose, allowed sources, required explicit confirmation flags, staging output schema, validation checks, write prohibitions, rollback/deletion expectations, stale/freshness caveats, source risk flags, operator checklist, failure modes, and non-goals.

## Explicit Non-Authorization

This milestone does not authorize:

- staging write implementation
- production refresh
- frontend/public artifact refresh
- research/generated artifact refresh
- live probes
- controlled live probe execution
- full-market scans
- broker/auth activation
- trading signals
- realtime guarantees

## Validation

- `python -m compileall scripts tests`
- `pytest -m "not network" tests/unit/test_twse_mis_normalization_v2.py`
- `pytest -m "not network"`
