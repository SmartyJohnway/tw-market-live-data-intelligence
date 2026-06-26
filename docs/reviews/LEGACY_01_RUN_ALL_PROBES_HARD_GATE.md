# LEGACY-01 Completion Report: run_all_probes Hard Gate

## Final Status

**Status:** COMPLETE

`scripts/run_all_probes.py` is now fail-closed as a legacy/manual network runner. Direct execution exits before loading targets, running probes, or writing generated artifacts unless this explicit acknowledgement is present:

```bash
I_UNDERSTAND_RUN_ALL_PROBES_IS_LEGACY=1 python scripts/run_all_probes.py
```

## Scope

This milestone protects against accidental use of the historical broad probe/report generator. It does not change the current M3G controlled path:

* `scripts/run_m3g04_controlled_live_probe.py`
* `scripts/m3g_live_probe_to_snapshot_adapter.py`
* `scripts/run_m3g10_bridge_dry_run.py`

## Boundary

No live probes were executed during validation. The new tests assert that the script exits before printing `Running probes...` when the acknowledgement is absent.

## Validation Commands

```bash
python -m compileall scripts tests
pytest -m "not network" tests/unit/test_run_all_probes_legacy_gate.py tests/unit/test_markdown_escaping.py
pytest -m "not network"
```

## Next Recommended Step

Proceed to `SERVER-01-FASTAPI-LIVE-PROBE-ENDPOINT-GOVERNANCE` before enabling any staging write path.
