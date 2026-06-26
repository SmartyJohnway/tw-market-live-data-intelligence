# M3H-02 TWSE MIS Adapter Contract Alignment

## Files Reviewed

- `scripts/probe_twse_mis.py`
- `scripts/m3g_live_probe_to_snapshot_adapter.py`
- `scripts/generate_latest_market_snapshot.py`
- `scripts/generate_ai_context_pack.py`
- `scripts/run_m3g10_bridge_dry_run.py`
- `tests/helpers/mock_fixtures.py`
- `tests/unit/test_m3g_live_probe_to_snapshot_adapter.py`
- `tests/unit/test_twse_mis_normalization_v2.py`

## Consumers Found

The reviewed consumers fall into these categories:

1. Probe envelope consumers reading `normalized_sample`, `freshness_status`, `delay_status`, and `staleness_seconds`.
2. Snapshot adapters mapping TWSE MIS evidence into latest-market-snapshot input objects.
3. Snapshot/context generators that expect snapshot-shaped fields such as `last_price`, `volume`, `source_time`, and `retrieved_time`.
4. Tests and fixture helpers that normalize TWSE MIS rows into mock input data.

## Adapter Behavior

`probe_twse_mis.py` already emits v2 canonical fields including `price`, `volume`, `bid_ladder`, `ask_ladder`, `source_timestamp`, `retrieved_at`, `freshness_status`, `delay_status`, and `staleness_seconds`, while also retaining v1 aliases such as `last_price`, `cumulative_volume`, `bid_prices`, and `ask_prices`.

The live-probe-to-snapshot adapter now accepts v2 canonical TWSE MIS normalized rows directly when v1 aliases are absent:

- `price` can populate snapshot `last_price`.
- `volume` remains preferred, with `cumulative_volume` retained as fallback.
- `bid_ladder` and `ask_ladder` are retained under the snapshot `bid_ask` structure when legacy `bid_ask` is absent.
- `source_timestamp` can populate snapshot `source_time`.
- `retrieved_at` can populate snapshot `retrieved_time`.

## v2 Canonical Field Support

Supported v2 fields verified by tests:

- `price`
- `volume`
- `bid_ladder`
- `ask_ladder`
- `source_timestamp`
- `retrieved_at`
- `freshness_status`
- `delay_status`
- `staleness_seconds`

## v1 Alias Fallback Preservation

The adapter still accepts existing v1 / pre-v2 fields:

- `last_price`
- `cumulative_volume`
- `bid_ask`
- `source_time`
- `retrieved_time`
- `retrieved_at_utc`
- Yahoo-specific `regular_market_price` and `regular_market_time_utc`

No v1 aliases were removed.

## Tests Added / Updated

Added `test_twse_mis_v2_fields_map_without_removing_v1_aliases` in `tests/unit/test_m3g_live_probe_to_snapshot_adapter.py` to prove that TWSE MIS v2 canonical fields map into snapshot input fields without removing legacy fallbacks or affecting other sources.

## Caveats

- `live_candidate` remains a caveated label and is not a realtime guarantee.
- TWSE MIS remains an unofficial frontend endpoint with fragile maintenance and legal/operational risk.
- This work does not promote any evidence into production current market state.

## Non-goals

- No live probes.
- No controlled live probe execution.
- No `scripts/run_all_probes.py` execution.
- No production refresh.
- No staging write.
- No generated or frontend artifact writes.
- No broker/auth or commercial API enablement.
- No trading signals.
- No MCP live-probe behavior changes.

## Validation

- `python -m compileall scripts tests`
- `pytest -m "not network" tests/unit/test_twse_mis_normalization_v2.py`
- `pytest -m "not network"`
